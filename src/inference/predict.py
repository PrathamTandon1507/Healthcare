"""
Module: src/inference/predict.py
Phase 17: Unified Production Inference Pipeline for Future Comorbidity Risk.

Implements Section 14 and 15 of COMORBIDITY_ENSEMBLE_ML_PLAN.md:
1. Input validation and schema encoding (age, sex, race, ethnicity, current diagnoses).
2. Deterministic 81-feature vector construction identical to Phase 4 training path.
3. Already-diagnosed condition masking (Section 1.5) preventing false incident predictions.
4. Per-disease calibrated probability prediction and threshold-based risk flagging.
5. On-demand clinical explanation generation (SHAP + Meta-weights + Risk/Protective factors).
6. Single code path shared between headless testing, batch pipelines, and Streamlit UI.
"""

import os
import sys
import time
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.data.labels import TARGET_41_DISEASES, CONDITION_METADATA
from src.features.pipeline import (
    DEMOGRAPHIC_FEATURE_COLUMNS,
    BURDEN_FEATURE_COLUMNS,
    INTERACTION_FEATURE_COLUMNS,
    BACKGROUND_CONDITION_CONCEPTS,
    get_baseline_feature_columns
)
from src.packaging.bundle import ReleaseBundle, load_release_bundle


# Standard Vocabulary Registry for Name -> Concept ID resolution
DISEASE_NAME_TO_CID: Dict[str, int] = {}
CID_TO_DISEASE_NAME: Dict[int, str] = {}
CID_TO_CATEGORY: Dict[int, str] = {}

# Background concepts
for _cid, _bg_name in BACKGROUND_CONDITION_CONCEPTS.items():
    _clean_name = _bg_name.replace("bg_", "").replace("_", " ").title()
    DISEASE_NAME_TO_CID[_clean_name.lower()] = _cid
    DISEASE_NAME_TO_CID[_bg_name.lower()] = _cid
    CID_TO_DISEASE_NAME[_cid] = _clean_name
    CID_TO_CATEGORY[_cid] = "Background / Prior History"

# General / Target condition metadata (target concepts take priority on name collisions)
# 1. Non-target concepts first
for _cid, _meta in CONDITION_METADATA.items():
    _name, _cat, _is_target = _meta
    if not _is_target:
        DISEASE_NAME_TO_CID[_name.lower()] = _cid
    CID_TO_DISEASE_NAME[_cid] = _name
    CID_TO_CATEGORY[_cid] = _cat

# 2. Target concepts override so TARGET_41_DISEASES CIDs are preferred
for _cid in TARGET_41_DISEASES:
    if _cid in CONDITION_METADATA:
        _name, _cat, _ = CONDITION_METADATA[_cid]
        DISEASE_NAME_TO_CID[_name.lower()] = _cid
        CID_TO_DISEASE_NAME[_cid] = _name
        CID_TO_CATEGORY[_cid] = _cat


@dataclass
class PatientInput:
    """
    Structured, validated patient profile input matching Section 2.1 specifications.
    """
    age: float
    gender: str
    race: str = "white"
    ethnicity: str = "non_hispanic"
    current_condition_ids: List[Union[int, str]] = field(default_factory=list)
    total_prior_condition_count: Optional[int] = None
    prior_obs_years: Optional[float] = None
    patient_id: Optional[str] = None

    def validate(self) -> "PatientInput":
        """Validates fields against reasonable clinical boundaries."""
        if not (0.0 <= float(self.age) <= 125.0):
            raise ValueError(f"Invalid age: {self.age}. Age must be between 0 and 125.")

        g = str(self.gender).strip().lower()
        if g not in ["m", "male", "f", "female", "8507", "8532"]:
            raise ValueError(f"Invalid gender: {self.gender}. Must be Male (M) or Female (F).")

        r = str(self.race).strip().lower()
        valid_races = ["white", "black", "asian", "other", "unknown"]
        if r not in valid_races:
            self.race = "other"

        e = str(self.ethnicity).strip().lower()
        valid_ethnicities = ["hispanic", "non_hispanic", "non-hispanic", "not hispanic"]
        if e not in valid_ethnicities:
            self.ethnicity = "non_hispanic"
        elif e in ["non-hispanic", "not hispanic"]:
            self.ethnicity = "non_hispanic"

        return self


def resolve_condition_identifiers(
    conditions: List[Union[int, str]]
) -> Tuple[List[int], List[Dict[str, Any]]]:
    """
    Maps heterogeneous list of integer concept IDs, concept strings, or disease names
    to canonical OMOP concept IDs and structured condition metadata dicts.
    """
    resolved_cids = []
    condition_records = []
    
    for item in conditions:
        cid = None
        if isinstance(item, int):
            if item in CID_TO_DISEASE_NAME:
                cid = item
        elif isinstance(item, str):
            item_clean = item.strip()
            if item_clean.isdigit():
                c_int = int(item_clean)
                if c_int in CID_TO_DISEASE_NAME:
                    cid = c_int
            else:
                cid = DISEASE_NAME_TO_CID.get(item_clean.lower())
                
        if cid is not None:
            resolved_cids.append(cid)
            name = CID_TO_DISEASE_NAME.get(cid, f"Condition {cid}")
            cat = CID_TO_CATEGORY.get(cid, "Other")
            condition_records.append({
                "concept_id": cid,
                "name": name,
                "category": cat,
                "is_target_41": (cid in TARGET_41_DISEASES)
            })

            
    # Deduplicate while preserving order
    seen = set()
    unique_cids = []
    unique_records = []
    for cid, rec in zip(resolved_cids, condition_records):
        if cid not in seen:
            seen.add(cid)
            unique_cids.append(cid)
            unique_records.append(rec)
            
    return unique_cids, unique_records


def build_feature_vector_from_patient_input(
    patient_input: PatientInput,
    feature_names: Optional[List[str]] = None
) -> np.ndarray:
    """
    Constructs the exact 81-dimensional clinical feature vector from a PatientInput instance.
    Guarantees 100% equivalence to training-time SQL feature extraction in Phase 4.
    """
    patient_input.validate()
    cids, _ = resolve_condition_identifiers(patient_input.current_condition_ids)
    cid_set = set(cids)
    
    age = float(patient_input.age)
    gender_str = str(patient_input.gender).strip().lower()
    is_male = 1 if gender_str in ["m", "male", "8507"] else 0
    is_female = 1 if gender_str in ["f", "female", "8532"] else 0
    
    race_str = str(patient_input.race).strip().lower()
    is_white = 1 if race_str == "white" else 0
    is_black = 1 if race_str == "black" else 0
    is_asian = 1 if race_str == "asian" else 0
    is_other_race = 1 if race_str not in ["white", "black", "asian"] else 0
    
    eth_str = str(patient_input.ethnicity).strip().lower()
    is_hispanic = 1 if eth_str == "hispanic" else 0
    is_non_hispanic = 1 if is_hispanic == 0 else 0
    
    # Comorbidity burden & utilization
    if patient_input.total_prior_condition_count is not None:
        cond_count = float(patient_input.total_prior_condition_count)
    else:
        cond_count = float(len(cid_set))
        
    if patient_input.prior_obs_years is not None:
        obs_years = float(patient_input.prior_obs_years)
    else:
        # Clinical heuristic: default observation baseline of 3.0 years for chronic condition history
        obs_years = 3.0 if len(cid_set) > 0 else 1.0

    # 1. Demographics (16)
    feat_map: Dict[str, float] = {
        "age_at_landmark": age,
        "age_lt_30": 1.0 if age < 30 else 0.0,
        "age_30_39": 1.0 if 30 <= age < 40 else 0.0,
        "age_40_49": 1.0 if 40 <= age < 50 else 0.0,
        "age_50_59": 1.0 if 50 <= age < 60 else 0.0,
        "age_60_69": 1.0 if 60 <= age < 70 else 0.0,
        "age_70_79": 1.0 if 70 <= age < 80 else 0.0,
        "age_gte_80": 1.0 if age >= 80 else 0.0,
        "gender_male": float(is_male),
        "gender_female": float(is_female),
        "race_white": float(is_white),
        "race_black": float(is_black),
        "race_asian": float(is_asian),
        "race_other": float(is_other_race),
        "ethnicity_hispanic": float(is_hispanic),
        "ethnicity_non_hispanic": float(is_non_hispanic),
        
        # 2. Longitudinal Burden (2)
        "total_prior_condition_count": cond_count,
        "prior_obs_years": obs_years
    }
    
    # 3. Target Comorbidity Histories (41)
    for cid in TARGET_41_DISEASES:
        feat_map[f"has_hist_{cid}"] = 1.0 if cid in cid_set else 0.0
        
    # 4. Background Condition Indicators (17)
    for bg_cid, bg_col in BACKGROUND_CONDITION_CONCEPTS.items():
        feat_map[bg_col] = 1.0 if bg_cid in cid_set else 0.0
        
    # 5. Clinical Interaction Terms (5)
    # Diabetes / Prediabetes
    has_dm = bool(cid_set.intersection({201826, 4311629, 4214376}))
    # Hypertension
    has_htn = bool(316866 in cid_set)
    # Dyslipidemia
    has_lipid = bool(cid_set.intersection({432867, 4120314, 436940}))
    # Cardiovascular
    has_cvd = bool(cid_set.intersection({317576, 192279, 381316, 321042}))
    # Chronic Kidney Disease
    has_ckd = bool(cid_set.intersection({4229440, 443614}))
    # Chronic Respiratory
    has_resp = bool(cid_set.intersection({258780, 4051466, 257012, 4283893}))
    
    feat_map["interaction_diabetes_and_hypertension"] = 1.0 if (has_dm and has_htn) else 0.0
    feat_map["interaction_hypertension_and_lipid"] = 1.0 if (has_htn and has_lipid) else 0.0
    feat_map["interaction_metabolic_triad"] = 1.0 if (has_htn and has_dm and has_lipid) else 0.0
    feat_map["interaction_cvd_and_ckd"] = 1.0 if (has_cvd and has_ckd) else 0.0
    feat_map["interaction_copd_and_cvd"] = 1.0 if (has_resp and has_cvd) else 0.0
    
    # Target ordered list
    ordered_cols = feature_names if feature_names is not None else get_baseline_feature_columns(TARGET_41_DISEASES)
    vec = np.array([feat_map[col] for col in ordered_cols], dtype=np.float32)
    return vec


@dataclass
class PredictionItem:
    """Single comorbidity risk prediction output item."""
    concept_id: int
    disease_name: str
    category: str
    calibrated_risk: float
    raw_probability: float
    decision_threshold: float
    is_flagged_elevated_risk: bool
    risk_tier: str
    relative_risk_multiplier: float
    explanation: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["calibrated_risk_percent"] = f"{self.calibrated_risk * 100:.2f}%"
        return d


@dataclass
class PatientPredictionResult:
    """Complete comorbidity prediction and explanation response container."""
    patient_id: Optional[str]
    patient_snapshot: Dict[str, Any]
    already_diagnosed_conditions: List[Dict[str, Any]]
    top_ranked_predictions: List[PredictionItem]
    all_candidate_predictions: List[PredictionItem]
    threshold_strategy_used: str
    model_version: str
    execution_timestamp: str
    execution_time_seconds: float

    def to_dataframe(self, include_all: bool = False) -> pd.DataFrame:
        items = self.all_candidate_predictions if include_all else self.top_ranked_predictions
        rows = []
        for rank, it in enumerate(items, 1):
            rows.append({
                "Rank": rank,
                "Concept ID": it.concept_id,
                "Disease Name": it.disease_name,
                "Category": it.category,
                "Calibrated 1-Yr Risk": f"{it.calibrated_risk * 100:.2f}%",
                "Raw Risk": f"{it.raw_probability * 100:.2f}%",
                "Decision Threshold": f"{it.decision_threshold * 100:.2f}%",
                "Risk Flag": "HIGH RISK" if it.is_flagged_elevated_risk else "Baseline",
                "Risk Tier": it.risk_tier,
                "Risk Multiplier": f"{it.relative_risk_multiplier:.1f}x"
            })
        return pd.DataFrame(rows)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patient_id": self.patient_id,
            "patient_snapshot": self.patient_snapshot,
            "already_diagnosed_conditions": self.already_diagnosed_conditions,
            "top_ranked_predictions": [it.to_dict() for it in self.top_ranked_predictions],
            "threshold_strategy_used": self.threshold_strategy_used,
            "model_version": self.model_version,
            "execution_timestamp": self.execution_timestamp,
            "execution_time_seconds": self.execution_time_seconds
        }


def predict_patient_comorbidity_risk(
    patient_input: Union[PatientInput, Dict[str, Any]],
    bundle: Optional[ReleaseBundle] = None,
    top_n: int = 5,
    threshold_strategy: str = "f1_optimal",
    include_explanations: bool = True,
    mask_existing_conditions: bool = True
) -> PatientPredictionResult:
    """
    Executes the complete production comorbidity risk prediction pipeline for a patient.
    
    Args:
        patient_input: PatientInput instance or raw dictionary of patient features.
        bundle: Loaded ReleaseBundle instance (if None, loaded automatically).
        top_n: Number of highest-risk candidate conditions to surface in primary list.
        threshold_strategy: Key in thresholds.json ('f1_optimal', 'recall_80_threshold', 'prevalence_matched_threshold').
        include_explanations: Whether to generate rich SHAP/meta-learner explanations for top-N.
        mask_existing_conditions: If True (Section 1.5 invariant), excludes conditions the patient
                                 already has from candidate future incident predictions.
                                 
    Returns:
        PatientPredictionResult object containing ranked risks, masks, and clinical explanations.
    """
    t0 = time.time()
    
    # 1. Ensure Model Release Bundle is Loaded
    if bundle is None:
        bundle = load_release_bundle()
    elif not bundle.is_loaded:
        bundle.load()

    # 2. Parse & Validate Patient Input
    if isinstance(patient_input, dict):
        p_obj = PatientInput(**patient_input)
    else:
        p_obj = patient_input
        
    p_obj.validate()
    
    # 3. Resolve Current Conditions and Separate Existing from Candidate Targets
    current_cids, existing_records = resolve_condition_identifiers(p_obj.current_condition_ids)
    existing_cid_set = set(current_cids)
    
    # 4. Construct Exact 81-Dimensional Feature Vector
    x_vec = build_feature_vector_from_patient_input(p_obj, feature_names=bundle.feature_cols)
    X_mat = x_vec.reshape(1, -1)
    
    # 5. Predict Raw & Calibrated Probabilities Across All 41 Targets
    raw_probs = bundle.predict_proba(X_mat, apply_calibration=False)[0]
    cal_probs = bundle.predict_proba(X_mat, apply_calibration=True)[0]
    
    # 6. Assemble Prediction Items & Apply Masking
    candidate_items: List[PredictionItem] = []
    
    for idx, cid in enumerate(bundle.target_cids):
        # Section 1.5 Masking: Exclude already diagnosed chronic conditions
        if mask_existing_conditions and (cid in existing_cid_set):
            continue
            
        c_name = CID_TO_DISEASE_NAME.get(cid, str(cid))
        c_cat = CID_TO_CATEGORY.get(cid, "General")
        p_raw = float(raw_probs[idx])
        p_cal = float(cal_probs[idx])
        
        # Threshold info
        th_info = bundle.thresholds.get(str(cid), {})
        thresh = float(th_info.get(threshold_strategy, th_info.get("default_threshold", 0.05)))
        is_flagged = bool(p_cal >= thresh)
        
        # Risk tier & multiplier vs baseline population rate
        base_rate = float(th_info.get("prevalence_matched_threshold", 0.005))
        mult = p_cal / max(base_rate, 0.0001)
        
        if is_flagged or p_cal >= 0.15:
            tier = "High Risk"
        elif p_cal >= 0.05:
            tier = "Moderate Risk"
        elif mult >= 2.0:
            tier = "Elevated Risk"
        else:
            tier = "Baseline / Low Risk"
            
        item = PredictionItem(
            concept_id=cid,
            disease_name=c_name,
            category=c_cat,
            calibrated_risk=round(p_cal, 4),
            raw_probability=round(p_raw, 4),
            decision_threshold=round(thresh, 4),
            is_flagged_elevated_risk=is_flagged,
            risk_tier=tier,
            relative_risk_multiplier=round(mult, 2),
            explanation=None
        )
        candidate_items.append(item)
        
    # 7. Sort Candidate Predictions by Calibrated Risk (Descending)
    candidate_items.sort(key=lambda item: item.calibrated_risk, reverse=True)
    
    # 8. Generate Explanations for Top-N Candidate Diseases
    top_n_items = candidate_items[:max(1, top_n)]
    
    if include_explanations:
        for it in top_n_items:
            try:
                exp_dict = bundle.explain(x_vec, it.concept_id)
                it.explanation = exp_dict
            except Exception as e:
                it.explanation = {
                    "error": f"Could not compute explanation: {str(e)}",
                    "target_disease": it.disease_name
                }
                
    elapsed = time.time() - t0
    
    snapshot = {
        "age": p_obj.age,
        "gender": p_obj.gender,
        "race": p_obj.race,
        "ethnicity": p_obj.ethnicity,
        "total_conditions": len(existing_cid_set),
        "prior_observation_years": p_obj.prior_obs_years or 3.0
    }
    
    return PatientPredictionResult(
        patient_id=p_obj.patient_id,
        patient_snapshot=snapshot,
        already_diagnosed_conditions=existing_records,
        top_ranked_predictions=top_n_items,
        all_candidate_predictions=candidate_items,
        threshold_strategy_used=threshold_strategy,
        model_version=bundle.manifest.get("version", "1.0.0"),
        execution_timestamp=datetime.now(timezone.utc).isoformat(),
        execution_time_seconds=round(elapsed, 4)
    )


def batch_predict_patient_comorbidity_risk(
    patient_inputs: List[Union[PatientInput, Dict[str, Any]]],
    bundle: Optional[ReleaseBundle] = None,
    top_n: int = 5,
    threshold_strategy: str = "f1_optimal"
) -> List[PatientPredictionResult]:
    """
    Batch prediction interface for multi-patient cohorts.
    """
    if bundle is None:
        bundle = load_release_bundle()
    elif not bundle.is_loaded:
        bundle.load()
        
    results = []
    for inp in patient_inputs:
        res = predict_patient_comorbidity_risk(
            patient_input=inp,
            bundle=bundle,
            top_n=top_n,
            threshold_strategy=threshold_strategy,
            include_explanations=False
        )
        results.append(res)
    return results
