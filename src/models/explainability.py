"""
Module: src/models/explainability.py
Phase 13: Unified Multi-Model Feature & Model Attribution Explainability Module.

Features:
1. Unified `explain(patient_vector, disease_id, model_container, calibrator)` interface.
2. LR: Standardized feature coefficients and linear risk score contributions (beta_i * x_i).
3. XGBoost: Native TreeSHAP attribution (pred_contribs).
4. Random Forest: Exact decision-tree path contributions (Saabas / TreeInterpreter method).
5. Stacked Ensemble: Meta-learner weight attribution ([alpha_LR * P_LR, alpha_RF * P_RF, alpha_XGB * P_XGB])
   clearly separated and paired with base-model feature-level contributions.
6. Structured output formatting matching Section 13 target deck format:
   - Patient snapshot profile (age, gender, existing conditions)
   - Calibrated predicted comorbidity risk
   - Model evidence & meta-learner trust
   - Top positive and negative contributing clinical features
   - Explicit clinical association language (STRICTLY NO CAUSAL LANGUAGE).
"""

import os
import sys
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.data.labels import TARGET_41_DISEASES, CONDITION_METADATA
from src.features.pipeline import DEMOGRAPHIC_FEATURE_COLUMNS, BURDEN_FEATURE_COLUMNS, INTERACTION_FEATURE_COLUMNS
from src.models.logistic_regression import FeaturePreprocessor, CONTINUOUS_FEATURE_NAMES
from src.models.stacking import StackedEnsembleModel
from src.models.calibration import DiseaseProbabilityCalibrator


def compute_rf_feature_contributions(rf_model: Any, x_vector: np.ndarray) -> np.ndarray:
    """
    Computes exact decision-tree path probability contributions for Random Forest.
    Returns 1D array (n_features,) of feature contributions summing with base_value to P(Y=1).
    """
    if x_vector.ndim == 1:
        X = x_vector.reshape(1, -1)
    else:
        X = x_vector

    n_features = X.shape[1]
    contributions = np.zeros(n_features, dtype=np.float32)

    for tree in rf_model.estimators_:
        tree_obj = tree.tree_
        values = tree_obj.value[:, 0, :]
        probs = values / np.maximum(values.sum(axis=1, keepdims=True), 1e-9)
        class1_probs = probs[:, 1]

        paths = tree.decision_path(X).toarray()[0]
        features = tree_obj.feature
        node_indices = np.where(paths == 1)[0]

        for j in range(len(node_indices) - 1):
            from_node = node_indices[j]
            to_node = node_indices[j + 1]
            feat = features[from_node]
            if feat >= 0:
                diff = class1_probs[to_node] - class1_probs[from_node]
                contributions[feat] += diff

    contributions /= max(1, len(rf_model.estimators_))
    return contributions


def compute_xgb_feature_contributions(xgb_model: Any, x_vector: np.ndarray) -> np.ndarray:
    """
    Computes native TreeSHAP margin contributions for XGBoost using DMatrix pred_contribs.
    Returns 1D array (n_features,) of feature contributions.
    """
    import xgboost as xgb

    if x_vector.ndim == 1:
        X = x_vector.reshape(1, -1)
    else:
        X = x_vector

    booster = xgb_model.get_booster()
    dmat = xgb.DMatrix(X)
    contribs = booster.predict(dmat, pred_contribs=True)
    # Output shape is (1, n_features + 1), where last element is bias / base value
    return contribs[0, :-1].astype(np.float32)


def compute_lr_feature_contributions(
    lr_model: Any,
    lr_preprocessor: FeaturePreprocessor,
    x_vector: np.ndarray
) -> np.ndarray:
    """
    Computes standardized feature score contributions (beta_i * scaled_x_i) for Logistic Regression.
    """
    if x_vector.ndim == 1:
        X = x_vector.reshape(1, -1)
    else:
        X = x_vector

    X_scaled = lr_preprocessor.transform(X)
    coefs = lr_model.coef_[0]
    return (coefs * X_scaled[0]).astype(np.float32)


def explain(
    patient_vector: np.ndarray,
    target_cid: int,
    feature_names: List[str],
    model_artifact: Any,
    calibrator: Optional[DiseaseProbabilityCalibrator] = None,
    top_n_features: int = 5
) -> Dict[str, Any]:
    """
    Generates a comprehensive, structured clinical explanation for a single patient's
    comorbidity prediction.

    STRICT CLINICAL LANGUAGE POLICY:
    - Language reflects predictive statistical associations and contributions to estimated risk.
    - Explicitly NEVER asserts causal statements (e.g. 'this caused X').
    """
    cname, cat, _ = CONDITION_METADATA.get(target_cid, (f"Disease {target_cid}", "General", True))

    if patient_vector.ndim == 1:
        x = patient_vector
        X = x.reshape(1, -1)
    else:
        x = patient_vector[0]
        X = patient_vector

    # 1. Determine Model Type and Extract Probabilities + Attributions
    is_stack = isinstance(model_artifact, StackedEnsembleModel)
    
    if is_stack:
        # A. Stacked Ensemble
        base_probs = model_artifact.predict_base_probabilities(X)[0]
        p_lr_base, p_rf_base, p_xgb_base = float(base_probs[0]), float(base_probs[1]), float(base_probs[2])
        raw_prob = float(model_artifact.predict_proba(X)[0, 1])

        # Meta-learner weights
        meta_coefs = model_artifact.meta_learner.coef_[0]
        meta_intercept = float(model_artifact.meta_learner.intercept_[0])
        meta_contributions = {
            "logistic_regression": {
                "base_probability": round(p_lr_base, 4),
                "meta_weight": round(float(meta_coefs[0]), 4),
                "score_contribution": round(float(meta_coefs[0] * p_lr_base), 4)
            },
            "random_forest": {
                "base_probability": round(p_rf_base, 4),
                "meta_weight": round(float(meta_coefs[1]), 4),
                "score_contribution": round(float(meta_coefs[1] * p_rf_base), 4)
            },
            "xgboost": {
                "base_probability": round(p_xgb_base, 4),
                "meta_weight": round(float(meta_coefs[2]), 4),
                "score_contribution": round(float(meta_coefs[2] * p_xgb_base), 4)
            }
        }

        # Feature-level contributions from base models
        xgb_contribs = compute_xgb_feature_contributions(model_artifact.xgb_model, x)
        rf_contribs = compute_rf_feature_contributions(model_artifact.rf_model, x)
        lr_contribs = compute_lr_feature_contributions(model_artifact.lr_model, model_artifact.lr_preprocessor, x)

        # Composite normalized feature ranking
        # Weighted blend of tree SHAP and linear score contributions
        combined_importance = (
            meta_coefs[2] * (xgb_contribs / (np.std(xgb_contribs) + 1e-6)) +
            meta_coefs[1] * (rf_contribs / (np.std(rf_contribs) + 1e-6)) +
            meta_coefs[0] * (lr_contribs / (np.std(lr_contribs) + 1e-6))
        )
        primary_feature_weights = combined_importance
        model_type_str = "4-Model Stacked Ensemble (LR + RF + XGB + Meta-LR)"

    else:
        # Standalone Base Learner
        raw_prob = float(model_artifact.predict_proba(X)[0, 1])
        meta_contributions = None

        if hasattr(model_artifact, "get_booster"):
            primary_feature_weights = compute_xgb_feature_contributions(model_artifact, x)
            model_type_str = "XGBoost Classifier (TreeSHAP Attributions)"
        elif hasattr(model_artifact, "estimators_"):
            primary_feature_weights = compute_rf_feature_contributions(model_artifact, x)
            model_type_str = "Random Forest Classifier (Decision Path Attributions)"
        elif hasattr(model_artifact, "coef_"):
            primary_feature_weights = model_artifact.coef_[0] * x
            model_type_str = "Logistic Regression (Standardized Score Contributions)"
        else:
            primary_feature_weights = np.zeros(len(feature_names), dtype=np.float32)
            model_type_str = "Generic Classifier"

    # 2. Apply Calibration if provided
    if calibrator is not None:
        calibrated_prob = float(calibrator.predict_proba(np.array([raw_prob]))[0])
        calibration_method = calibrator.method
    else:
        calibrated_prob = raw_prob
        calibration_method = "uncalibrated"

    # 3. Extract Top Contributing Clinical Features
    feature_items = []
    for i, f_name in enumerate(feature_names):
        val = float(x[i])
        weight = float(primary_feature_weights[i])
        feature_items.append({
            "feature": f_name,
            "patient_value": val,
            "importance_score": round(weight, 4),
            "direction": "increases_risk" if weight > 0 else "decreases_risk"
        })

    # Sort positive and negative contributors
    pos_features = sorted([f for f in feature_items if f["importance_score"] > 0], key=lambda x: x["importance_score"], reverse=True)[:top_n_features]
    neg_features = sorted([f for f in feature_items if f["importance_score"] < 0], key=lambda x: x["importance_score"])[:top_n_features]

    # 4. Extract Patient Clinical Snapshot
    age_val = float(x[feature_names.index("age_at_landmark")]) if "age_at_landmark" in feature_names else None
    prior_cond_val = int(x[feature_names.index("total_prior_condition_count")]) if "total_prior_condition_count" in feature_names else None
    prior_obs_val = float(x[feature_names.index("prior_obs_years")]) if "prior_obs_years" in feature_names else None

    # Identify active prior conditions
    active_conditions = []
    for i, f_name in enumerate(feature_names):
        if f_name.startswith("has_hist_") and x[i] == 1.0:
            hist_cid = int(f_name.replace("has_hist_", ""))
            c_name, _, _ = CONDITION_METADATA.get(hist_cid, (f"Condition {hist_cid}", "", True))
            active_conditions.append({"concept_id": hist_cid, "condition_name": c_name})

    structured_explanation = {
        "target_disease": {
            "concept_id": target_cid,
            "disease_name": cname,
            "category": cat
        },
        "patient_snapshot": {
            "age": age_val,
            "total_prior_conditions": prior_cond_val,
            "prior_observation_years": prior_obs_val,
            "active_prior_diagnoses": active_conditions
        },
        "risk_prediction": {
            "uncalibrated_probability": round(raw_prob, 4),
            "calibrated_probability": round(calibrated_prob, 4),
            "calibration_method": calibration_method,
            "risk_tier": "High" if calibrated_prob >= 0.15 else ("Moderate" if calibrated_prob >= 0.05 else "Low")
        },
        "model_architecture": model_type_str,
        "ensemble_meta_weights": meta_contributions,
        "key_risk_increasing_factors": pos_features,
        "key_protective_factors": neg_features,
        "clinical_disclaimer": "This statistical attribution describes predictive associations observed in population training data. It does not establish causal etiology."
    }

    return structured_explanation
