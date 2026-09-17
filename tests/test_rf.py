"""
Unit tests for Phase 8: Random Forest Pipeline, Tuning, OOB Diagnostics, and Feature Importances.
"""

import pytest
import numpy as np
import os
from pathlib import Path

from src.models.random_forest import (
    build_rf_classifier,
    train_and_tune_single_rf
)
from src.features.pipeline import get_baseline_feature_columns
from src.data.labels import TARGET_41_DISEASES


def test_rf_classifier_builder_and_oob():
    """
    Verifies that build_rf_classifier correctly creates Random Forest instances with OOB tracking.
    """
    clf = build_rf_classifier(n_estimators=30, max_depth=4, n_jobs=1)
    
    np.random.seed(42)
    X = np.random.randn(60, 10).astype(np.float32)
    y = np.random.randint(0, 2, 60).astype(np.int32)

    clf.fit(X, y)
    assert hasattr(clf, "oob_decision_function_")
    assert clf.oob_decision_function_.shape == (60, 2)
    probs = clf.predict_proba(X)
    assert probs.shape == (60, 2)
    np.testing.assert_allclose(np.sum(probs, axis=1), 1.0, rtol=1e-5)


def test_rf_tuning_diagnostics_and_feature_importances():
    """
    Tests RF hyperparameter tuning, OOB diagnostics, and feature importance extraction.
    """
    feature_names = get_baseline_feature_columns(TARGET_41_DISEASES)
    
    np.random.seed(42)
    X_tr = np.random.randn(100, 81).astype(np.float32)
    # Give feature 0 a strong correlation
    y_tr = (X_tr[:, 0] > 0.3).astype(np.int32)

    X_va = np.random.randn(50, 81).astype(np.float32)
    y_va = (X_va[:, 0] > 0.3).astype(np.int32)

    candidate_params = [
        {"max_depth": 4, "min_samples_leaf": 5, "max_features": "sqrt"},
        {"max_depth": 8, "min_samples_leaf": 2, "max_features": "sqrt"}
    ]

    best_rf, best_config, meta = train_and_tune_single_rf(
        X_train=X_tr,
        y_train=y_tr,
        X_val=X_va,
        y_val=y_va,
        feature_names=feature_names,
        target_cid=316866,
        candidate_params=candidate_params,
        random_seed=42,
        n_jobs=1
    )

    assert best_config in candidate_params
    assert "diagnostics" in meta
    diag = meta["diagnostics"]
    assert "train_auprc" in diag and "oob_auprc" in diag and "val_auprc" in diag

    # Feature importances must be non-negative and sum to 1.0
    importances = list(meta["all_feature_importances"].values())
    assert len(importances) == 81
    assert all(i >= 0.0 for i in importances)
    np.testing.assert_allclose(sum(importances), 1.0, atol=1e-3)

    # Top feature should be the correlated feature (feature 0: age_at_landmark)
    assert meta["top_features"][0]["feature"] == feature_names[0]
