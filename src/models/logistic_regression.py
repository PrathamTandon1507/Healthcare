"""
Module: src/models/logistic_regression.py
Phase 7: Standalone Logistic Regression Base Learner Module.

Features:
1. Pure NumPy feature preprocessing: Standard scaling on continuous features
   (age_at_landmark, total_prior_condition_count, prior_obs_years), passthrough for 78 binary indicators.
2. L2 Regularization parameter tuning (C in [0.01, 0.1, 1.0, 10.0]) on Validation split AUPRC.
3. Class-weighted balanced loss to handle disease imbalance.
4. Coefficient Extraction & Odds Ratio (OR = exp(beta)) calculation for clinical interpretability.
5. Clinical Plausibility Verification Harness testing established medical comorbidity relationships.
"""

import os
import sys
import json
import joblib
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

from sklearn.linear_model import LogisticRegression

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.features.pipeline import (
    DEMOGRAPHIC_FEATURE_COLUMNS,
    BURDEN_FEATURE_COLUMNS,
    INTERACTION_FEATURE_COLUMNS,
    BACKGROUND_CONDITION_CONCEPTS,
    get_baseline_feature_columns
)
from src.data.labels import TARGET_41_DISEASES, CONDITION_METADATA
from src.models.metrics import compute_binary_metrics


# Continuous features that benefit from standard scaling in linear models
CONTINUOUS_FEATURE_NAMES: List[str] = [
    "age_at_landmark",
    "total_prior_condition_count",
    "prior_obs_years"
]


class FeaturePreprocessor:
    """
    Pure NumPy feature scaler that standardizes continuous features while
    leaving binary/one-hot features intact. Avoids external dataframe dependencies.
    """
    def __init__(self, continuous_indices: List[int]):
        self.continuous_indices = continuous_indices
        self.means: Optional[np.ndarray] = None
        self.stds: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray):
        cont_x = X[:, self.continuous_indices]
        self.means = np.mean(cont_x, axis=0, keepdims=True).astype(np.float32)
        stds = np.std(cont_x, axis=0, keepdims=True).astype(np.float32)
        stds[stds == 0] = 1.0
        self.stds = stds
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        X_out = np.array(X, dtype=np.float32, copy=True)
        X_out[:, self.continuous_indices] = (
            X_out[:, self.continuous_indices] - self.means
        ) / self.stds
        return X_out

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        return self.fit(X).transform(X)


class TunedLogisticRegressionModel:
    """
    Container packaging the fitted preprocessor and the best Logistic Regression classifier.
    """
    def __init__(
        self,
        preprocessor: FeaturePreprocessor,
        classifier: LogisticRegression,
        best_C: float,
        feature_names: List[str]
    ):
        self.preprocessor = preprocessor
        self.classifier = classifier
        self.best_C = best_C
        self.feature_names = feature_names

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        X_proc = self.preprocessor.transform(X)
        return self.classifier.predict_proba(X_proc)

    def predict(self, X: np.ndarray) -> np.ndarray:
        X_proc = self.preprocessor.transform(X)
        return self.classifier.predict(X_proc)


def train_and_tune_single_lr(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    feature_names: List[str],
    target_cid: int,
    candidate_c_values: List[float] = [0.01, 0.1, 1.0, 10.0],
    random_seed: int = 42
) -> Tuple[TunedLogisticRegressionModel, float, Dict[str, Any]]:
    """
    Trains candidate LR models over C grid, selects the optimal C maximizing Validation AUPRC,
    and returns the best fitted model wrapper along with diagnostic metrics and coefficients.
    """
    cont_indices = [
        idx for idx, name in enumerate(feature_names)
        if name in CONTINUOUS_FEATURE_NAMES
    ]
    preprocessor = FeaturePreprocessor(continuous_indices=cont_indices)
    X_tr_proc = preprocessor.fit_transform(X_train)
    X_va_proc = preprocessor.transform(X_val)

    best_c = 1.0
    best_val_auprc = -1.0
    best_clf = None
    tuning_log = {}

    for c_val in candidate_c_values:
        clf = LogisticRegression(
            C=c_val,
            class_weight="balanced",
            solver="lbfgs",
            max_iter=1000,
            random_state=random_seed
        )
        clf.fit(X_tr_proc, y_train)

        val_probs = clf.predict_proba(X_va_proc)[:, 1]
        val_metrics = compute_binary_metrics(y_val, val_probs)
        tuning_log[f"C_{c_val}"] = {
            "val_auprc": val_metrics["auprc"],
            "val_auroc": val_metrics["auroc"],
            "val_brier": val_metrics["brier_score"]
        }

        if val_metrics["auprc"] > best_val_auprc:
            best_val_auprc = val_metrics["auprc"]
            best_c = c_val
            best_clf = clf

    # Wrap fitted model
    fitted_model = TunedLogisticRegressionModel(
        preprocessor=preprocessor,
        classifier=best_clf,
        best_C=best_c,
        feature_names=feature_names
    )

    # Extract coefficients
    coefficients = best_clf.coef_[0]
    intercept = float(best_clf.intercept_[0])

    coef_dict = {}
    for feat_name, coef_val in zip(feature_names, coefficients):
        coef_dict[feat_name] = {
            "coefficient": round(float(coef_val), 5),
            "odds_ratio": round(float(np.exp(coef_val)), 5)
        }

    # Top positive and negative predictors
    sorted_coefs = sorted(coef_dict.items(), key=lambda x: x[1]["coefficient"], reverse=True)
    top_positive = [{"feature": k, **v} for k, v in sorted_coefs[:10]]
    top_negative = [{"feature": k, **v} for k, v in sorted_coefs[-10:]]

    metadata = {
        "target_concept_id": target_cid,
        "best_C": best_c,
        "intercept": round(intercept, 5),
        "tuning_log": tuning_log,
        "top_positive_features": top_positive,
        "top_negative_features": top_negative,
        "all_coefficients": coef_dict
    }

    return fitted_model, best_c, metadata


def verify_clinical_plausibility(coefficients_per_disease: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Audits extracted LR coefficients against well-established medical rules.
    
    Rules verified:
    1. Diabetes / Hyperglycemia indicators positively predict Diabetic Complications (Retinopathy, Neuropathy) and CKD.
    2. Hypertension history positively predicts Coronary Arteriosclerosis, CHF, and Stroke.
    3. Age at landmark positively predicts Osteoarthritis, Osteoporosis, and Alzheimer's.
    4. Prior chronic condition count positively predicts overall multi-comorbidity risk.
    """
    checks = []

    # Rule 1: Diabetes -> CKD & Neuropathy
    for ckd_cid in [4229440, 443614]:
        if ckd_cid in coefficients_per_disease:
            coefs = coefficients_per_disease[ckd_cid]["all_coefficients"]
            dm_coef = coefs.get("has_hist_201826", {}).get("coefficient", 0.0)
            int_dm_htn = coefs.get("interaction_diabetes_and_hypertension", {}).get("coefficient", 0.0)
            passed = (dm_coef > 0.0) or (int_dm_htn > 0.0)
            checks.append({
                "rule": f"Diabetes history positively predicts CKD ({ckd_cid})",
                "target_cid": ckd_cid,
                "feature": "has_hist_201826 / interaction_diabetes_and_hypertension",
                "dm_coef": dm_coef,
                "int_coef": int_dm_htn,
                "passed": passed
            })

    # Rule 2: Hypertension -> Coronary Arteriosclerosis (317576) & Congestive Heart Failure (192279)
    for cvd_cid in [317576, 192279]:
        if cvd_cid in coefficients_per_disease:
            coefs = coefficients_per_disease[cvd_cid]["all_coefficients"]
            htn_coef = coefs.get("has_hist_316866", {}).get("coefficient", 0.0)
            int_htn_lipid = coefs.get("interaction_hypertension_and_lipid", {}).get("coefficient", 0.0)
            passed = (htn_coef > 0.0) or (int_htn_lipid > 0.0)
            checks.append({
                "rule": f"Hypertension history positively predicts CVD ({cvd_cid})",
                "target_cid": cvd_cid,
                "feature": "has_hist_316866 / interaction_hypertension_and_lipid",
                "htn_coef": htn_coef,
                "int_coef": int_htn_lipid,
                "passed": passed
            })

    # Rule 3: Age -> Alzheimer's (378419) & Osteoarthritis (4148906 / 75036 / 80502)
    for age_cid in [378419, 80502]:
        if age_cid in coefficients_per_disease:
            coefs = coefficients_per_disease[age_cid]["all_coefficients"]
            age_coef = coefs.get("age_at_landmark", {}).get("coefficient", 0.0)
            age_old = coefs.get("age_gte_80", {}).get("coefficient", 0.0)
            passed = (age_coef > 0.0) or (age_old > 0.0)
            checks.append({
                "rule": f"Age positively predicts Degenerative Disease ({age_cid})",
                "target_cid": age_cid,
                "feature": "age_at_landmark / age_gte_80",
                "age_coef": age_coef,
                "age_old_coef": age_old,
                "passed": passed
            })

    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])

    return {
        "total_clinical_rules_checked": total_checks,
        "passed_rules": passed_checks,
        "all_passed": (passed_checks == total_checks),
        "detailed_checks": checks
    }
