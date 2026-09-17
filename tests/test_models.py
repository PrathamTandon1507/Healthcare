"""
Unit tests for Phase 6: Baseline Models, Metric Evaluation Harness, and Data Loaders.
"""

import pytest
import numpy as np
import os
from pathlib import Path

from src.models.baseline import (
    PrevalenceBaseline,
    build_base_classifier,
    detect_xgboost_device,
    save_model_artifact,
    load_model_artifact
)
from src.models.metrics import (
    compute_binary_metrics,
    compute_ranking_metrics_at_k,
    evaluate_multitarget_predictions
)
from src.models.data_loader import load_dataset_splits
from src.features.pipeline import NETWORK_FEATURE_COLUMNS, IDENTIFIER_COLUMNS


def test_prevalence_baseline_logic():
    """
    Verifies that PrevalenceBaseline outputs exact empirical training prevalence.
    """
    Y_train = np.array([
        [1, 0, 0],
        [1, 1, 0],
        [0, 1, 0],
        [0, 0, 0]
    ], dtype=np.int32)
    
    target_cids = [101, 102, 103]
    baseline = PrevalenceBaseline(target_concept_ids=target_cids)
    baseline.fit(Y_train)

    assert baseline.prevalences[101] == 0.50
    assert baseline.prevalences[102] == 0.50
    assert baseline.prevalences[103] == 0.00

    X_test = np.zeros((3, 10), dtype=np.float32)
    probs = baseline.predict_proba(X_test)
    assert probs.shape == (3, 3)
    assert np.all(probs[:, 0] == 0.50)
    assert np.all(probs[:, 1] == 0.50)
    assert np.all(probs[:, 2] == 0.00)


def test_metric_harness_binary_and_ranking():
    """
    Verifies single-disease binary classification and multi-disease ranking metric computations.
    """
    y_true = np.array([1, 0, 1, 0, 0, 1], dtype=np.int32)
    y_pred = np.array([0.9, 0.1, 0.8, 0.2, 0.3, 0.7], dtype=np.float32)

    metrics = compute_binary_metrics(y_true, y_pred)
    assert metrics["auprc"] > 0.90
    assert metrics["auroc"] > 0.90
    assert 0.0 <= metrics["brier_score"] <= 1.0

    # Multi-disease ranking
    Y_true = np.array([
        [1, 0, 0, 0],
        [0, 1, 1, 0],
        [0, 0, 0, 1]
    ], dtype=np.int32)

    Y_pred = np.array([
        [0.9, 0.4, 0.1, 0.2],
        [0.1, 0.8, 0.7, 0.3],
        [0.2, 0.1, 0.3, 0.85]
    ], dtype=np.float32)

    ranking = compute_ranking_metrics_at_k(Y_true, Y_pred, k_values=[1, 2, 3])
    assert ranking["precision_at_1"] == 1.0
    assert ranking["recall_at_1"] >= 0.60
    assert ranking["map_at_1"] == 1.0


def test_data_loader_active_features_and_network_exclusion():
    """
    Verifies that the split data loader extracts exactly 81 clinical features,
    completely excluding all network placeholder and identifier columns.
    """
    train_split, val_split, test_split = load_dataset_splits(
        target_concept_ids=[316866, 432867],
        max_samples_per_split=100,
        random_seed=42
    )

    assert train_split.n_features == 81
    assert val_split.n_features == 81
    assert test_split.n_features == 81

    for col in NETWORK_FEATURE_COLUMNS:
        assert col not in train_split.feature_names, f"Network placeholder {col} leaked into active features!"

    for col in IDENTIFIER_COLUMNS:
        assert col not in train_split.feature_names, f"Identifier {col} leaked into active features!"


def test_model_artifact_persistence(tmp_path):
    """
    Tests saving and loading model artifacts to ensure serialized fidelity.
    """
    X = np.random.randn(20, 5).astype(np.float32)
    y = np.array([0, 1] * 10, dtype=np.int32)

    clf = build_base_classifier(model_type="lr", target_cid=316866, pos_count=10, neg_count=10)
    clf.fit(X, y)
    orig_preds = clf.predict_proba(X)

    save_file = str(tmp_path / "test_lr.joblib")
    save_model_artifact(clf, save_file, metadata={"test": True})
    
    loaded_clf = load_model_artifact(save_file)
    loaded_preds = loaded_clf.predict_proba(X)

    np.testing.assert_allclose(orig_preds, loaded_preds, rtol=1e-5)
