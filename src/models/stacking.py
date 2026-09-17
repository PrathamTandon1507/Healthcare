"""
Module: src/models/stacking.py
Phase 10: Leakage-Safe Out-Of-Fold (OOF) Stacking Ensemble Module.

Features:
1. Patient-Level Group K-Fold Partitioning (M=5 folds) over training landmarks.
2. Leakage-Free OOF Probability Generation across Base Learners (LR, RF, XGB).
3. Logistic Regression Meta-Learner fitting on OOF probability matrix [P_LR, P_RF, P_XGB].
4. Full-Data Base Learner Refitting & Serialized StackedEnsembleModel bundle.
5. Strict Row-ID and Patient-ID Bookkeeping verification.
"""

import os
import sys
import json
import joblib
import numpy as np
import duckdb
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from sklearn.model_selection import KFold
from sklearn.linear_model import LogisticRegression

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.data.labels import TARGET_41_DISEASES, CONDITION_METADATA
from src.models.logistic_regression import FeaturePreprocessor, CONTINUOUS_FEATURE_NAMES
from src.models.random_forest import build_rf_classifier
from src.models.xgboost_model import build_xgb_classifier
from src.models.baseline import detect_xgboost_device, save_model_artifact, load_model_artifact
from src.models.metrics import compute_binary_metrics


def build_patient_kfold_splits(
    person_ids: np.ndarray,
    n_splits: int = 5,
    random_seed: int = 42
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    Creates deterministic K-Fold partitions strictly at the patient level.
    Guarantees that all landmark rows for any given person_id belong exclusively
    to either the train fold or the test/validation fold (0 patient overlap).

    Args:
        person_ids: Array of person_id values corresponding to each landmark row (n_samples,).
        n_splits: Number of folds (default M=5).
        random_seed: Deterministic random seed.

    Returns:
        List of (train_row_indices, oof_row_indices) for each fold.
    """
    unique_patients = np.unique(person_ids)
    rng = np.random.RandomState(random_seed)
    shuffled_patients = unique_patients.copy()
    rng.shuffle(shuffled_patients)

    kf = KFold(n_splits=n_splits, shuffle=False)
    splits = []

    # Map each patient to a fold index
    patient_to_fold = {}
    for fold_idx, (_, test_pt_idx) in enumerate(kf.split(shuffled_patients)):
        for pt in shuffled_patients[test_pt_idx]:
            patient_to_fold[pt] = fold_idx

    # Assign each landmark row index to its patient's fold
    row_folds = np.array([patient_to_fold[pid] for pid in person_ids], dtype=np.int32)

    for fold_idx in range(n_splits):
        val_idx = np.where(row_folds == fold_idx)[0]
        tr_idx = np.where(row_folds != fold_idx)[0]
        splits.append((tr_idx, val_idx))

    return splits


class StackedEnsembleModel:
    """
    Complete 4-Model Stacking Ensemble container per target disease:
    - Logistic Regression Base Model (+ Preprocessor)
    - Random Forest Base Model
    - XGBoost Base Model
    - Logistic Regression Meta-Learner
    """
    def __init__(
        self,
        target_cid: int,
        lr_model: Any,
        lr_preprocessor: FeaturePreprocessor,
        rf_model: Any,
        xgb_model: Any,
        meta_learner: LogisticRegression,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.target_cid = target_cid
        self.lr_model = lr_model
        self.lr_preprocessor = lr_preprocessor
        self.rf_model = rf_model
        self.xgb_model = xgb_model
        self.meta_learner = meta_learner
        self.metadata = metadata or {}

    def predict_base_probabilities(self, X: np.ndarray) -> np.ndarray:
        """
        Computes 3-column probability matrix [P_LR, P_RF, P_XGB] from fitted base models.
        """
        X_lr = self.lr_preprocessor.transform(X)
        p_lr = self.lr_model.predict_proba(X_lr)[:, 1]
        p_rf = self.rf_model.predict_proba(X)[:, 1]
        p_xgb = self.xgb_model.predict_proba(X)[:, 1]
        return np.column_stack([p_lr, p_rf, p_xgb]).astype(np.float32)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Outputs final 2-class probabilities [P(Y=0), P(Y=1)] from meta-learner.
        """
        P_base = self.predict_base_probabilities(X)
        return self.meta_learner.predict_proba(P_base)

    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """Outputs binary class prediction using specified decision threshold."""
        probs = self.predict_proba(X)[:, 1]
        return (probs >= threshold).astype(np.int32)


def train_single_stacked_ensemble(
    X_train: np.ndarray,
    y_train: np.ndarray,
    train_person_ids: np.ndarray,
    feature_names: List[str],
    target_cid: int,
    lr_config: Dict[str, Any],
    rf_config: Dict[str, Any],
    xgb_config: Dict[str, Any],
    n_splits: int = 5,
    device: str = "auto",
    random_seed: int = 42,
    n_jobs: int = 4
) -> Tuple[StackedEnsembleModel, np.ndarray, Dict[str, Any]]:
    """
    Executes complete Phase 10 Out-Of-Fold stacking workflow for a single target disease:
    1. Splits training data into M=5 patient-level folds.
    2. Trains base models on M-1 folds and generates OOF predictions on held-out folds.
    3. Fits Logistic Regression meta-learner on the 3-column OOF matrix.
    4. Refits all 3 base models on the full training set.
    5. Returns fitted StackedEnsembleModel, OOF probability matrix, and diagnostic metadata.
    """
    n_samples = len(y_train)
    oof_matrix = np.zeros((n_samples, 3), dtype=np.float32)  # [LR, RF, XGB]

    cont_indices = [feature_names.index(f) for f in CONTINUOUS_FEATURE_NAMES if f in feature_names]
    fold_splits = build_patient_kfold_splits(train_person_ids, n_splits=n_splits, random_seed=random_seed)

    # 1. Out-Of-Fold Base Learner Training
    for fold_idx, (tr_idx, val_idx) in enumerate(fold_splits):
        X_tr_f, y_tr_f = X_train[tr_idx], y_train[tr_idx]
        X_va_f = X_train[val_idx]

        # A. Logistic Regression
        prep_f = FeaturePreprocessor(continuous_indices=cont_indices)
        X_tr_lr = prep_f.fit_transform(X_tr_f)
        X_va_lr = prep_f.transform(X_va_f)
        lr_clf = LogisticRegression(
            C=lr_config.get("C", 1.0),
            class_weight=lr_config.get("class_weight", "balanced"),
            solver="lbfgs",
            max_iter=1000,
            random_state=random_seed
        )
        lr_clf.fit(X_tr_lr, y_tr_f)
        oof_matrix[val_idx, 0] = lr_clf.predict_proba(X_va_lr)[:, 1]

        # B. Random Forest
        rf_clf = build_rf_classifier(
            n_estimators=rf_config.get("n_estimators", 100),
            max_depth=rf_config.get("max_depth", 10),
            min_samples_leaf=rf_config.get("min_samples_leaf", 5),
            max_features=rf_config.get("max_features", "sqrt"),
            class_weight=rf_config.get("class_weight", "balanced"),
            oob_score=False,
            random_seed=random_seed,
            n_jobs=n_jobs
        )
        rf_clf.fit(X_tr_f, y_tr_f)
        oof_matrix[val_idx, 1] = rf_clf.predict_proba(X_va_f)[:, 1]

        # C. XGBoost
        pos_cnt_f = int(np.sum(y_tr_f))
        neg_cnt_f = len(y_tr_f) - pos_cnt_f
        spw_f = min(float(neg_cnt_f / max(1, pos_cnt_f)), 500.0)

        xgb_clf = build_xgb_classifier(
            n_estimators=xgb_config.get("n_estimators", 200),
            max_depth=xgb_config.get("max_depth", 6),
            learning_rate=xgb_config.get("learning_rate", 0.05),
            subsample=xgb_config.get("subsample", 0.8),
            colsample_bytree=xgb_config.get("colsample_bytree", 0.8),
            reg_lambda=xgb_config.get("reg_lambda", 1.0),
            scale_pos_weight=spw_f,
            early_stopping_rounds=None,
            eval_metric="logloss",
            device=device,
            random_seed=random_seed,
            n_jobs=n_jobs
        )
        xgb_clf.fit(X_tr_f, y_tr_f, verbose=False)
        oof_matrix[val_idx, 2] = xgb_clf.predict_proba(X_va_f)[:, 1]

    # 2. Fit Logistic Regression Meta-Learner on OOF predictions
    meta_clf = LogisticRegression(
        C=1.0,
        penalty="l2",
        solver="lbfgs",
        fit_intercept=True,
        random_state=random_seed
    )
    meta_clf.fit(oof_matrix, y_train)

    meta_weights = {
        "weight_lr": round(float(meta_clf.coef_[0][0]), 6),
        "weight_rf": round(float(meta_clf.coef_[0][1]), 6),
        "weight_xgb": round(float(meta_clf.coef_[0][2]), 6),
        "intercept": round(float(meta_clf.intercept_[0]), 6)
    }

    # Evaluate OOF performance metrics
    oof_meta_probs = meta_clf.predict_proba(oof_matrix)[:, 1]
    oof_metrics = compute_binary_metrics(y_train, oof_meta_probs)
    oof_lr_metrics = compute_binary_metrics(y_train, oof_matrix[:, 0])
    oof_rf_metrics = compute_binary_metrics(y_train, oof_matrix[:, 1])
    oof_xgb_metrics = compute_binary_metrics(y_train, oof_matrix[:, 2])

    # 3. Refit Base Learners on FULL Training Data
    full_prep = FeaturePreprocessor(continuous_indices=cont_indices)
    X_train_lr = full_prep.fit_transform(X_train)
    full_lr = LogisticRegression(
        C=lr_config.get("C", 1.0),
        class_weight=lr_config.get("class_weight", "balanced"),
        solver="lbfgs",
        max_iter=1000,
        random_state=random_seed
    )
    full_lr.fit(X_train_lr, y_train)

    full_rf = build_rf_classifier(
        n_estimators=rf_config.get("n_estimators", 100),
        max_depth=rf_config.get("max_depth", 10),
        min_samples_leaf=rf_config.get("min_samples_leaf", 5),
        max_features=rf_config.get("max_features", "sqrt"),
        class_weight=rf_config.get("class_weight", "balanced"),
        oob_score=True,
        random_seed=random_seed,
        n_jobs=n_jobs
    )
    full_rf.fit(X_train, y_train)

    pos_cnt = int(np.sum(y_train))
    neg_cnt = len(y_train) - pos_cnt
    spw = min(float(neg_cnt / max(1, pos_cnt)), 500.0)

    full_xgb = build_xgb_classifier(
        n_estimators=xgb_config.get("n_estimators", 200),
        max_depth=xgb_config.get("max_depth", 6),
        learning_rate=xgb_config.get("learning_rate", 0.05),
        subsample=xgb_config.get("subsample", 0.8),
        colsample_bytree=xgb_config.get("colsample_bytree", 0.8),
        reg_lambda=xgb_config.get("reg_lambda", 1.0),
        scale_pos_weight=spw,
        early_stopping_rounds=None,
        eval_metric="logloss",
        device=device,
        random_seed=random_seed,
        n_jobs=n_jobs
    )
    full_xgb.fit(X_train, y_train, verbose=False)

    # 4. Assemble Stacked Container
    cname, cat, _ = CONDITION_METADATA.get(target_cid, (f"Disease {target_cid}", "General", True))
    meta_info = {
        "target_concept_id": target_cid,
        "target_name": cname,
        "category": cat,
        "n_train_samples": n_samples,
        "n_folds": n_splits,
        "meta_weights": meta_weights,
        "oof_metrics": {
            "stack_auprc": round(float(oof_metrics["auprc"]), 6),
            "stack_auroc": round(float(oof_metrics["auroc"]), 6),
            "lr_auprc": round(float(oof_lr_metrics["auprc"]), 6),
            "rf_auprc": round(float(oof_rf_metrics["auprc"]), 6),
            "xgb_auprc": round(float(oof_xgb_metrics["auprc"]), 6)
        },
        "frozen_configs": {
            "logistic_regression": lr_config,
            "random_forest": rf_config,
            "xgboost": xgb_config
        }
    }

    stack_model = StackedEnsembleModel(
        target_cid=target_cid,
        lr_model=full_lr,
        lr_preprocessor=full_prep,
        rf_model=full_rf,
        xgb_model=full_xgb,
        meta_learner=meta_clf,
        metadata=meta_info
    )

    return stack_model, oof_matrix, meta_info
