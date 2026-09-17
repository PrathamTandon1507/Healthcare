"""
Module: src/models/random_forest.py
Phase 8: Standalone Random Forest Base Learner Module.

Features:
1. Multi-tree ensemble training with balanced class weighting.
2. Out-Of-Bag (OOB) diagnostic scoring computed natively on training bootstrap samples.
3. Hyperparameter search over max_depth, min_samples_leaf, and max_features optimizing Validation AUPRC.
4. Gini / MDI Feature Importance extraction for all 81 clinical predictors per disease.
5. Train-vs-OOB-vs-Validation-vs-Test generalization gap analysis diagnosing overfitting / underfitting.
"""

import os
import sys
import json
import joblib
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

from sklearn.ensemble import RandomForestClassifier

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.data.labels import TARGET_41_DISEASES, CONDITION_METADATA
from src.models.metrics import compute_binary_metrics


def build_rf_classifier(
    n_estimators: int = 100,
    max_depth: int = 10,
    min_samples_leaf: int = 5,
    max_features: Union[str, float] = "sqrt",
    class_weight: str = "balanced",
    oob_score: bool = True,
    random_seed: int = 42,
    n_jobs: int = 4
) -> RandomForestClassifier:
    """
    Constructs a configured RandomForestClassifier instance with OOB score tracking.
    """
    return RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        max_features=max_features,
        class_weight=class_weight,
        oob_score=oob_score,
        random_state=random_seed,
        n_jobs=n_jobs
    )


def train_and_tune_single_rf(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    feature_names: List[str],
    target_cid: int,
    candidate_params: Optional[List[Dict[str, Any]]] = None,
    random_seed: int = 42,
    n_jobs: int = 4
) -> Tuple[RandomForestClassifier, Dict[str, Any], Dict[str, Any]]:
    """
    Evaluates candidate RF parameter configurations, selects the best model based on
    Validation AUPRC, extracts Gini feature importances, and computes OOB / generalization diagnostics.
    """
    if candidate_params is None:
        candidate_params = [
            {"max_depth": 8, "min_samples_leaf": 10, "max_features": "sqrt"},
            {"max_depth": 10, "min_samples_leaf": 5, "max_features": "sqrt"},
            {"max_depth": 14, "min_samples_leaf": 2, "max_features": "sqrt"},
            {"max_depth": 10, "min_samples_leaf": 5, "max_features": 0.3}
        ]

    best_val_auprc = -1.0
    best_rf = None
    best_config = None
    tuning_log = {}

    for idx, params in enumerate(candidate_params):
        cfg_key = f"depth{params['max_depth']}_leaf{params['min_samples_leaf']}_feat{params['max_features']}"
        
        clf = build_rf_classifier(
            n_estimators=100,
            max_depth=params["max_depth"],
            min_samples_leaf=params["min_samples_leaf"],
            max_features=params["max_features"],
            class_weight="balanced",
            oob_score=True,
            random_seed=random_seed,
            n_jobs=n_jobs
        )
        clf.fit(X_train, y_train)

        val_probs = clf.predict_proba(X_val)[:, 1]
        val_metrics = compute_binary_metrics(y_val, val_probs)

        # Compute OOB metrics on training set
        oob_probs = clf.oob_decision_function_[:, 1]
        oob_metrics = compute_binary_metrics(y_train, oob_probs)

        tuning_log[cfg_key] = {
            "params": params,
            "val_auprc": val_metrics["auprc"],
            "val_auroc": val_metrics["auroc"],
            "val_brier": val_metrics["brier_score"],
            "oob_auprc": oob_metrics["auprc"],
            "oob_auroc": oob_metrics["auroc"]
        }

        if val_metrics["auprc"] > best_val_auprc:
            best_val_auprc = val_metrics["auprc"]
            best_rf = clf
            best_config = params

    # Extract Feature Importances from best model
    importances = best_rf.feature_importances_
    feat_imp_dict = {}
    for f_name, imp_val in zip(feature_names, importances):
        feat_imp_dict[f_name] = round(float(imp_val), 6)

    # Top 10 most important features
    sorted_importances = sorted(feat_imp_dict.items(), key=lambda x: x[1], reverse=True)
    top_features = [{"feature": k, "importance": v} for k, v in sorted_importances[:10]]

    # Compute Train and OOB metrics for best model
    tr_probs = best_rf.predict_proba(X_train)[:, 1]
    tr_metrics = compute_binary_metrics(y_train, tr_probs)
    oob_metrics_best = compute_binary_metrics(y_train, best_rf.oob_decision_function_[:, 1])

    diagnostics = {
        "train_auprc": tr_metrics["auprc"],
        "train_auroc": tr_metrics["auroc"],
        "oob_auprc": oob_metrics_best["auprc"],
        "oob_auroc": oob_metrics_best["auroc"],
        "val_auprc": best_val_auprc,
        "train_val_gap_auprc": round(tr_metrics["auprc"] - best_val_auprc, 6),
        "oob_val_gap_auprc": round(oob_metrics_best["auprc"] - best_val_auprc, 6)
    }

    metadata = {
        "target_concept_id": target_cid,
        "best_hyperparameters": best_config,
        "diagnostics": diagnostics,
        "top_features": top_features,
        "all_feature_importances": feat_imp_dict,
        "tuning_log": tuning_log
    }

    return best_rf, best_config, metadata
