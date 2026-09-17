"""
Module: src/models/baseline.py
Model implementations for Phase 6 (Prevalence Baseline) and Phase 7-9 Base Learners
(Logistic Regression, Random Forest, XGBoost) with GPU CUDA acceleration & CPU fallback.
"""

import os
import sys
import json
import joblib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np

# Configure multi-threading env vars to avoid OpenMP contention
os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "4")
os.environ.setdefault("MKL_NUM_THREADS", "4")

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False


def detect_xgboost_device(preferred_device: str = "auto") -> str:
    """
    Detects whether XGBoost can execute with CUDA acceleration or falls back to CPU.
    """
    if preferred_device.lower() == "cpu":
        return "cpu"
    if not XGBOOST_AVAILABLE:
        return "cpu"

    if preferred_device.lower() in ("cuda", "gpu", "auto"):
        try:
            # Test small dummy fit with CUDA
            clf_test = xgb.XGBClassifier(n_estimators=1, max_depth=1, device="cuda", tree_method="hist")
            X_dummy = np.random.randn(10, 2).astype(np.float32)
            y_dummy = np.array([0, 1] * 5, dtype=np.int32)
            clf_test.fit(X_dummy, y_dummy)
            return "cuda"
        except Exception:
            return "cpu"
    return "cpu"


class PrevalenceBaseline:
    """
    Floor baseline model that outputs constant training-set prevalence P(Y=1 | Train)
    for each disease regardless of patient features.
    """
    def __init__(self, target_concept_ids: List[int]):
        self.target_concept_ids = target_concept_ids
        self.prevalences: Dict[int, float] = {}

    def fit(self, Y_train: np.ndarray):
        """Computes empirical training prevalence per target."""
        n_samples = Y_train.shape[0]
        for idx, cid in enumerate(self.target_concept_ids):
            n_pos = int(np.sum(Y_train[:, idx]))
            self.prevalences[cid] = float(n_pos / n_samples) if n_samples > 0 else 0.0
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Returns (n_samples, n_targets) array where each column is constant class prevalence."""
        n_samples = X.shape[0]
        probs = np.zeros((n_samples, len(self.target_concept_ids)), dtype=np.float32)
        for idx, cid in enumerate(self.target_concept_ids):
            probs[:, idx] = self.prevalences.get(cid, 0.0)
        return probs

    def predict_single_proba(self, X: np.ndarray, target_cid: int) -> np.ndarray:
        """Returns 1D array of constant class prevalence for single disease."""
        prev = self.prevalences.get(target_cid, 0.0)
        return np.full(X.shape[0], prev, dtype=np.float32)


def build_base_classifier(
    model_type: str,
    target_cid: int,
    pos_count: int,
    neg_count: int,
    random_seed: int = 42,
    device: str = "auto",
    n_jobs: int = 4
) -> Any:
    """
    Factory creating a configured base binary classifier for a single target comorbidity.
    
    Args:
        model_type: One of 'lr' (Logistic Regression), 'rf' (Random Forest), 'xgb' (XGBoost).
        target_cid: Target OMOP concept ID.
        pos_count: Number of positive training examples (for class weighting / scale_pos_weight).
        neg_count: Number of negative training examples.
        random_seed: Deterministic random seed.
        device: 'auto', 'cuda', or 'cpu'.
        n_jobs: Number of CPU worker threads.
        
    Returns:
        Configured scikit-learn or XGBoost classifier instance.
    """
    model_type = model_type.lower()

    if model_type in ("lr", "logistic_regression"):
        return LogisticRegression(
            C=1.0,
            class_weight="balanced",
            solver="lbfgs",
            max_iter=1000,
            random_state=random_seed
        )

    elif model_type in ("rf", "random_forest"):
        return RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=random_seed,
            n_jobs=n_jobs
        )

    elif model_type in ("xgb", "xgboost"):
        if not XGBOOST_AVAILABLE:
            raise RuntimeError("XGBoost package is not installed.")

        # Compute scale_pos_weight
        scale_pos_weight = float(neg_count / max(1, pos_count))
        # Cap scale_pos_weight for numerical stability on rare targets
        scale_pos_weight = min(scale_pos_weight, 500.0)

        resolved_device = detect_xgboost_device(preferred_device=device)

        return xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=scale_pos_weight,
            eval_metric="logloss",
            tree_method="hist",
            device=resolved_device,
            random_state=random_seed,
            n_jobs=n_jobs if resolved_device == "cpu" else 1
        )

    else:
        raise ValueError(f"Unsupported model_type: {model_type}. Expected 'lr', 'rf', or 'xgb'.")


def save_model_artifact(model: Any, filepath: str, metadata: Optional[Dict[str, Any]] = None):
    """Saves a fitted model artifact and its optional JSON metadata."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    joblib.dump(model, filepath, compress=3)
    if metadata:
        meta_path = filepath.rsplit(".", 1)[0] + "_metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)


def load_model_artifact(filepath: str) -> Any:
    """Loads a persisted model artifact."""
    return joblib.load(filepath)
