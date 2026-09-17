"""
Module: src/models/xgboost_model.py
Phase 9: Standalone XGBoost Base Learner Module.

Features:
1. Configurable XGBClassifier construction with CUDA GPU support and CPU fallback.
2. Positional class weighting (scale_pos_weight = N_neg / N_pos, capped at 500 for rare disease stability).
3. Hyperparameter grid search over max_depth, learning_rate, and reg_lambda.
4. Early stopping wired strictly to the validation set (early_stopping_rounds=15) using validation logloss / eval_metric.
5. Learning curve extraction and validation of early stopping behavior (stopping neither at round 1 nor hitting max rounds indefinitely).
6. Multi-type feature importance extraction (Gain, Weight, Cover) for all 81 active clinical predictors per disease.
"""

import os
import sys
import json
import joblib
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.data.labels import TARGET_41_DISEASES, CONDITION_METADATA
from src.models.metrics import compute_binary_metrics
from src.models.baseline import detect_xgboost_device


def build_xgb_classifier(
    n_estimators: int = 200,
    max_depth: int = 6,
    learning_rate: float = 0.05,
    subsample: float = 0.8,
    colsample_bytree: float = 0.8,
    reg_lambda: float = 1.0,
    reg_alpha: float = 0.0,
    scale_pos_weight: float = 1.0,
    early_stopping_rounds: Optional[int] = None,
    eval_metric: str = "logloss",
    device: str = "auto",
    random_seed: int = 42,
    n_jobs: int = 4
) -> "xgb.XGBClassifier":
    """
    Constructs a configured XGBClassifier instance with device detection and optional early stopping.
    """
    if not XGBOOST_AVAILABLE:
        raise RuntimeError("XGBoost package is not installed.")

    resolved_device = detect_xgboost_device(preferred_device=device)

    return xgb.XGBClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        subsample=subsample,
        colsample_bytree=colsample_bytree,
        reg_lambda=reg_lambda,
        reg_alpha=reg_alpha,
        scale_pos_weight=scale_pos_weight,
        eval_metric=eval_metric,
        early_stopping_rounds=early_stopping_rounds,
        tree_method="hist",
        device=resolved_device,
        random_state=random_seed,
        n_jobs=n_jobs if resolved_device == "cpu" else 1
    )


def train_and_tune_single_xgb(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    feature_names: List[str],
    target_cid: int,
    candidate_params: Optional[List[Dict[str, Any]]] = None,
    early_stopping_rounds: int = 15,
    device: str = "auto",
    random_seed: int = 42,
    n_jobs: int = 4
) -> Tuple["xgb.XGBClassifier", Dict[str, Any], Dict[str, Any]]:
    """
    Evaluates candidate XGBoost parameter configurations, selects the best model based on
    Validation AUPRC, extracts Gain / Weight / Cover feature importances, and records learning curves & early stopping diagnostics.
    """
    if candidate_params is None:
        candidate_params = [
            {"max_depth": 4, "learning_rate": 0.05, "reg_lambda": 1.0, "subsample": 0.8, "colsample_bytree": 0.8},
            {"max_depth": 6, "learning_rate": 0.05, "reg_lambda": 1.0, "subsample": 0.8, "colsample_bytree": 0.8},
            {"max_depth": 6, "learning_rate": 0.03, "reg_lambda": 5.0, "subsample": 0.8, "colsample_bytree": 0.8},
            {"max_depth": 8, "learning_rate": 0.03, "reg_lambda": 5.0, "subsample": 0.7, "colsample_bytree": 0.7}
        ]

    pos_count = int(np.sum(y_train))
    neg_count = len(y_train) - pos_count
    scale_pos_weight = float(neg_count / max(1, pos_count))
    scale_pos_weight = min(scale_pos_weight, 500.0)

    best_val_auprc = -1.0
    best_xgb = None
    best_config = None
    best_eval_results = None
    tuning_log = {}

    resolved_device = detect_xgboost_device(preferred_device=device)

    for idx, params in enumerate(candidate_params):
        cfg_key = f"depth{params['max_depth']}_lr{params['learning_rate']}_l2{params.get('reg_lambda', 1.0)}"

        clf = build_xgb_classifier(
            n_estimators=200,
            max_depth=params["max_depth"],
            learning_rate=params["learning_rate"],
            subsample=params.get("subsample", 0.8),
            colsample_bytree=params.get("colsample_bytree", 0.8),
            reg_lambda=params.get("reg_lambda", 1.0),
            reg_alpha=params.get("reg_alpha", 0.0),
            scale_pos_weight=scale_pos_weight,
            early_stopping_rounds=early_stopping_rounds,
            eval_metric="logloss",
            device=resolved_device,
            random_seed=random_seed,
            n_jobs=n_jobs
        )

        # Fit with validation evaluation set for early stopping
        clf.fit(
            X_train,
            y_train,
            eval_set=[(X_train, y_train), (X_val, y_val)],
            verbose=False
        )

        val_probs = clf.predict_proba(X_val)[:, 1]
        val_metrics = compute_binary_metrics(y_val, val_probs)
        val_auprc = val_metrics["auprc"]

        # Extract best iteration and early stopping status
        best_iteration = int(getattr(clf, "best_iteration", clf.n_estimators - 1))
        evals_result = clf.evals_result() if hasattr(clf, "evals_result") and callable(clf.evals_result) else {}

        tuning_log[cfg_key] = {
            "params": params,
            "best_iteration": best_iteration,
            "val_auprc": round(float(val_auprc), 6),
            "val_auroc": round(float(val_metrics["auroc"]), 6),
            "val_brier": round(float(val_metrics["brier_score"]), 6),
            "val_f1_tuned": round(float(val_metrics["f1_tuned"]), 6)
        }

        if val_auprc > best_val_auprc:
            best_val_auprc = val_auprc
            best_xgb = clf
            best_config = params
            best_eval_results = evals_result

    # Compute final metrics on train & val for best model
    train_probs = best_xgb.predict_proba(X_train)[:, 1]
    val_probs = best_xgb.predict_proba(X_val)[:, 1]
    train_metrics = compute_binary_metrics(y_train, train_probs)
    val_metrics = compute_binary_metrics(y_val, val_probs)

    # Extract booster feature importances (Gain, Weight, Cover)
    booster = best_xgb.get_booster()
    score_gain = booster.get_score(importance_type="gain")
    score_weight = booster.get_score(importance_type="weight")
    score_cover = booster.get_score(importance_type="cover")

    importances_gain = {}
    importances_weight = {}
    importances_cover = {}
    for i, f_name in enumerate(feature_names):
        f_key = f"f{i}"
        g_val = score_gain.get(f_name, score_gain.get(f_key, 0.0))
        w_val = score_weight.get(f_name, score_weight.get(f_key, 0.0))
        c_val = score_cover.get(f_name, score_cover.get(f_key, 0.0))
        importances_gain[f_name] = float(g_val)
        importances_weight[f_name] = float(w_val)
        importances_cover[f_name] = float(c_val)

    sorted_importances = sorted(importances_gain.items(), key=lambda x: x[1], reverse=True)
    top_10_features = [
        {"feature": name, "gain": round(gain, 6), "weight": int(importances_weight[name]), "cover": round(importances_cover[name], 4)}
        for name, gain in sorted_importances[:10]
    ]

    best_iter = int(getattr(best_xgb, "best_iteration", best_xgb.n_estimators - 1))
    early_stopped_sensibly = (best_iter > 1) and (best_iter < (best_xgb.n_estimators - 1))

    cname, cat, _ = CONDITION_METADATA.get(target_cid, (f"Disease {target_cid}", "General", True))
    metadata = {
        "target_concept_id": target_cid,
        "target_name": cname,
        "category": cat,
        "device": resolved_device,
        "best_hyperparameters": best_config,
        "best_iteration": best_iter,
        "early_stopped_sensibly": early_stopped_sensibly,
        "scale_pos_weight": round(scale_pos_weight, 4),
        "diagnostics": {
            "train_auprc": round(float(train_metrics["auprc"]), 6),
            "train_auroc": round(float(train_metrics["auroc"]), 6),
            "val_auprc": round(float(val_metrics["auprc"]), 6),
            "val_auroc": round(float(val_metrics["auroc"]), 6),
            "generalization_gap_auprc": round(float(train_metrics["auprc"] - val_metrics["auprc"]), 6),
            "generalization_gap_auroc": round(float(train_metrics["auroc"] - val_metrics["auroc"]), 6)
        },
        "top_features_by_gain": top_10_features,
        "all_feature_importances_gain": importances_gain,
        "all_feature_importances_weight": importances_weight,
        "all_feature_importances_cover": importances_cover,
        "learning_curves": {
            "train_loss": [round(float(v), 6) for v in best_eval_results.get("validation_0", {}).get("logloss", [])] if best_eval_results else [],
            "val_loss": [round(float(v), 6) for v in best_eval_results.get("validation_1", {}).get("logloss", [])] if best_eval_results else []
        },
        "tuning_log": tuning_log
    }

    return best_xgb, best_config, metadata
