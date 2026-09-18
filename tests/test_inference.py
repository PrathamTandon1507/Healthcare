"""
Unit tests for Phase 17: Inference Pipeline and Serving Module.

Tests:
1. PatientInput validation (valid boundaries, invalid inputs, fallback handling).
2. Exact 81-dimensional clinical feature vector reconstruction and interaction terms.
3. Section 1.5 already-has-disease masking invariance.
4. Per-disease probability prediction, calibration, and threshold-based risk flagging.
5. Multi-level clinical explanation generation.
6. Batch prediction interface and DataFrame export.
"""

import pytest
import numpy as np
import pandas as pd
from typing import Dict, List, Any

from src.data.labels import TARGET_41_DISEASES, CONDITION_METADATA
from src.features.pipeline import (
    DEMOGRAPHIC_FEATURE_COLUMNS,
    BURDEN_FEATURE_COLUMNS,
    INTERACTION_FEATURE_COLUMNS,
    BACKGROUND_CONDITION_CONCEPTS,
    get_baseline_feature_columns
)
from src.packaging.bundle import load_release_bundle
from src.inference.predict import (
    PatientInput,
    PredictionItem,
    PatientPredictionResult,
    resolve_condition_identifiers,
    build_feature_vector_from_patient_input,
    predict_patient_comorbidity_risk,
    batch_predict_patient_comorbidity_risk
)


@pytest.fixture(scope="module")
def shared_release_bundle():
    """Loads and caches the release bundle for test executions."""
    return load_release_bundle("models/release_v1")


def test_patient_input_validation():
    """Verifies that PatientInput validates clinical boundaries and normalizes categories."""
    # Valid input
    p_valid = PatientInput(
        age=55.0,
        gender="Male",
        race="black",
        ethnicity="non_hispanic",
        current_condition_ids=[201826]
    )
    p_valid.validate()
    assert p_valid.age == 55.0
    assert p_valid.race == "black"

    # Age boundary errors
    with pytest.raises(ValueError, match="Invalid age"):
        PatientInput(age=-5, gender="F").validate()

    with pytest.raises(ValueError, match="Invalid age"):
        PatientInput(age=130, gender="F").validate()

    # Gender validation error
    with pytest.raises(ValueError, match="Invalid gender"):
        PatientInput(age=40, gender="Unknown").validate()

    # Normalization of race/ethnicity
    p_norm = PatientInput(age=40, gender="F", race="Mars", ethnicity="Not Hispanic").validate()
    assert p_norm.race == "other"
    assert p_norm.ethnicity == "non_hispanic"


def test_resolve_condition_identifiers():
    """Verifies resolution of disease names, concept IDs, and string IDs."""
    mixed_input = [
        201826,                             # Concept ID for Type 2 Diabetes
        "316866",                           # String CID for Essential Hypertension
        "Hyperlipidemia",                  # Exact name
        "Primary Malignant Neoplasm of Colon",
        "bg_viral_sinusitis",               # Background condition
        99999999                            # Unknown concept
    ]
    cids, records = resolve_condition_identifiers(mixed_input)
    assert 201826 in cids
    assert 316866 in cids
    assert 432867 in cids  # Hyperlipidemia CID
    assert 79740 in cids   # Colon cancer CID
    assert 40481087 in cids # bg_viral_sinusitis CID
    assert 99999999 not in cids  # Unregistered concept excluded

    assert len(records) == 5
    for r in records:
        assert "concept_id" in r
        assert "name" in r
        assert "category" in r


def test_feature_vector_construction_and_interactions():
    """
    Verifies that build_feature_vector_from_patient_input constructs the exact 81 features
    and computes complex clinical interaction terms properly.
    """
    feature_cols = get_baseline_feature_columns(TARGET_41_DISEASES)
    assert len(feature_cols) == 81

    # Patient with Metabolic Triad: Diabetes (201826) + HTN (316866) + Hyperlipidemia (432867)
    patient = PatientInput(
        age=62.0,
        gender="M",
        race="white",
        ethnicity="non_hispanic",
        current_condition_ids=[201826, 316866, 432867],
        total_prior_condition_count=3,
        prior_obs_years=4.5
    )

    vec = build_feature_vector_from_patient_input(patient, feature_names=feature_cols)
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (81,)
    assert vec.dtype == np.float32

    # Check demographic one-hots
    assert vec[feature_cols.index("age_at_landmark")] == 62.0
    assert vec[feature_cols.index("age_60_69")] == 1.0
    assert vec[feature_cols.index("age_50_59")] == 0.0
    assert vec[feature_cols.index("gender_male")] == 1.0
    assert vec[feature_cols.index("gender_female")] == 0.0
    assert vec[feature_cols.index("race_white")] == 1.0

    # Check condition multi-hots
    assert vec[feature_cols.index("has_hist_201826")] == 1.0  # T2D
    assert vec[feature_cols.index("has_hist_316866")] == 1.0  # HTN
    assert vec[feature_cols.index("has_hist_432867")] == 1.0  # Hyperlipidemia
    assert vec[feature_cols.index("has_hist_75036")] == 0.0   # Osteoarthritis

    # Check interaction terms
    assert vec[feature_cols.index("interaction_diabetes_and_hypertension")] == 1.0
    assert vec[feature_cols.index("interaction_hypertension_and_lipid")] == 1.0
    assert vec[feature_cols.index("interaction_metabolic_triad")] == 1.0
    assert vec[feature_cols.index("interaction_cvd_and_ckd")] == 0.0


def test_already_has_disease_masking_invariance(shared_release_bundle):
    """
    Verifies Section 1.5 requirement:
    Conditions the patient already has MUST be excluded from candidate future incident predictions.
    """
    # Patient with Osteoarthritis of hand (75036) and Osteoporosis (80502)
    patient = PatientInput(
        age=72.0,
        gender="F",
        race="white",
        ethnicity="non_hispanic",
        current_condition_ids=[75036, 80502],
        prior_obs_years=6.0
    )

    result = predict_patient_comorbidity_risk(
        patient_input=patient,
        bundle=shared_release_bundle,
        top_n=5,
        mask_existing_conditions=True
    )

    # 1. Existing conditions list check
    existing_cids = [c["concept_id"] for c in result.already_diagnosed_conditions]
    assert 75036 in existing_cids
    assert 80502 in existing_cids
    assert len(existing_cids) == 2

    # 2. Candidate incident pool size must be 41 - 2 = 39
    assert len(result.all_candidate_predictions) == 39

    # 3. Neither 75036 nor 80502 should appear anywhere in candidate predictions
    candidate_cids = [it.concept_id for it in result.all_candidate_predictions]
    assert 75036 not in candidate_cids
    assert 80502 not in candidate_cids

    top_cids = [it.concept_id for it in result.top_ranked_predictions]
    assert 75036 not in top_cids
    assert 80502 not in top_cids


def test_risk_predictions_and_threshold_strategies(shared_release_bundle):
    """
    Verifies output properties of risk predictions across different threshold strategies.
    """
    patient = PatientInput(
        age=50.0,
        gender="M",
        race="asian",
        ethnicity="non_hispanic",
        current_condition_ids=[316866]  # HTN only
    )

    for strat in ["f1_optimal", "recall_80_threshold", "prevalence_matched_threshold"]:
        res = predict_patient_comorbidity_risk(
            patient_input=patient,
            bundle=shared_release_bundle,
            top_n=5,
            threshold_strategy=strat,
            include_explanations=False
        )

        assert len(res.top_ranked_predictions) == 5
        assert res.threshold_strategy_used == strat

        # Check ranking ordering (calibrated risk descending)
        risks = [it.calibrated_risk for it in res.top_ranked_predictions]
        for i in range(len(risks) - 1):
            assert risks[i] >= risks[i + 1], "Top-N items must be sorted in descending order of risk"

        # Check prediction item fields
        for it in res.top_ranked_predictions:
            assert 0.0 <= it.calibrated_risk <= 1.0
            assert 0.0 <= it.raw_probability <= 1.0
            assert 0.0 <= it.decision_threshold <= 1.0
            assert isinstance(it.is_flagged_elevated_risk, bool)
            assert it.risk_tier in ["High Risk", "Moderate Risk", "Elevated Risk", "Baseline / Low Risk"]


def test_clinical_explanations_structure(shared_release_bundle):
    """
    Verifies that explainability payload contains all required Section 12 elements.
    """
    patient = PatientInput(
        age=65.0,
        gender="M",
        race="black",
        ethnicity="non_hispanic",
        current_condition_ids=[201826, 316866],
        prior_obs_years=5.0
    )

    res = predict_patient_comorbidity_risk(
        patient_input=patient,
        bundle=shared_release_bundle,
        top_n=2,
        include_explanations=True
    )

    for it in res.top_ranked_predictions:
        assert it.explanation is not None
        exp = it.explanation
        assert "target_disease" in exp
        assert "patient_snapshot" in exp
        assert "ensemble_meta_weights" in exp
        assert "key_risk_increasing_factors" in exp
        assert "key_protective_factors" in exp
        assert "clinical_disclaimer" in exp

        # Check meta weights
        meta = exp["ensemble_meta_weights"]
        assert "logistic_regression" in meta
        assert "random_forest" in meta
        assert "xgboost" in meta


def test_batch_prediction_and_dataframe_export(shared_release_bundle):
    """Verifies batch inference and pandas DataFrame serialization."""
    patients = [
        PatientInput(age=30, gender="F", current_condition_ids=[]),
        PatientInput(age=75, gender="M", current_condition_ids=[201826, 316866, 432867])
    ]

    batch_res = batch_predict_patient_comorbidity_risk(
        patient_inputs=patients,
        bundle=shared_release_bundle,
        top_n=3
    )

    assert len(batch_res) == 2
    for r in batch_res:
        df = r.to_dataframe(include_all=False)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "Rank" in df.columns
        assert "Disease Name" in df.columns
        assert "Calibrated 1-Yr Risk" in df.columns
        assert "Risk Flag" in df.columns

        d = r.to_dict()
        assert isinstance(d, dict)
        assert "patient_snapshot" in d
        assert "top_ranked_predictions" in d
