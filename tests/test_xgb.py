"""
Unit tests for Phase 9: Standalone XGBoost Base Learner Module.
"""

import os
import sys
import numpy as np
import pytest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.models.xgboost_model import build_xgb_classifier, train_and_tune_single_xgb
from src.models.baseline import save_model_artifact, load_model_artifact, detect_xgboost_device
from src.models.metrics import evaluate_multitarget_predictions


def test_device_detection():
    device = detect_xgboost_device(preferred_device="auto")
    assert device in ("cuda", "cpu")
    cpu_device = detect_xgboost_device(preferred_device="cpu")
    assert cpu_device == "cpu"


def test_xgb_construction_and_fit():
    np.random.seed(42)
    X_train = np.random.randn(100, 10).astype(np.float32)
    y_train = (X_train[:, 0] + X_train[:, 1] > 0).astype(np.int32)

    X_val = np.random.randn(40, 10).astype(np.float32)
    y_val = (X_val[:, 0] + X_val[:, 1] > 0).astype(np.int32)

    clf = build_xgb_classifier(
        n_estimators=50,
        max_depth=3,
        learning_rate=0.1,
        device="cpu",
        random_seed=42
    )
    clf.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

    probs = clf.predict_proba(X_val)
    assert probs.shape == (40, 2)
    assert np.all(probs >= 0.0) and np.all(probs <= 1.0)
    assert np.allclose(np.sum(probs, axis=1), 1.0)


def test_train_and_tune_single_xgb():
    np.random.seed(42)
    X_train = np.random.randn(200, 5).astype(np.float32)
    y_train = (X_train[:, 0] > 0.5).astype(np.int32)

    X_val = np.random.randn(100, 5).astype(np.float32)
    y_val = (X_val[:, 0] > 0.5).astype(np.int32)

    feature_names = [f"feat_{i}" for i in range(5)]
    candidate_params = [
        {"max_depth": 3, "learning_rate": 0.1, "reg_lambda": 1.0},
        {"max_depth": 4, "learning_rate": 0.05, "reg_lambda": 2.0}
    ]

    best_xgb, best_config, meta = train_and_tune_single_xgb(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        feature_names=feature_names,
        target_cid=201826,
        candidate_params=candidate_params,
        early_stopping_rounds=10,
        device="cpu",
        random_seed=42,
        n_jobs=2
    )

    assert best_xgb is not None
    assert "best_hyperparameters" in meta
    assert "diagnostics" in meta
    assert "top_features_by_gain" in meta
    assert len(meta["top_features_by_gain"]) > 0
    assert meta["target_concept_id"] == 201826
    assert "learning_curves" in meta
    assert len(meta["learning_curves"]["train_loss"]) > 0

    top_feat = meta["top_features_by_gain"][0]["feature"]
    assert top_feat == "feat_0"


def test_xgb_model_serialization(tmp_path):
    np.random.seed(42)
    X = np.random.randn(50, 4).astype(np.float32)
    y = (X[:, 0] > 0).astype(np.int32)

    clf = build_xgb_classifier(n_estimators=10, max_depth=2, device="cpu", random_seed=42)
    clf.fit(X, y)

    model_file = str(tmp_path / "model_xgb_test.joblib")
    meta = {"test_metric": 0.95}
    save_model_artifact(clf, model_file, metadata=meta)

    loaded_clf = load_model_artifact(model_file)
    probs_orig = clf.predict_proba(X)
    probs_loaded = loaded_clf.predict_proba(X)
    assert np.allclose(probs_orig, probs_loaded)


def test_multitarget_evaluation_signature_regression():
    """
    Regression test ensuring evaluate_multitarget_predictions works with
    standard kwargs (Y_true, Y_pred_proba, target_concept_ids, condition_metadata)
    and does not accept invalid keyword arguments like Y_pred_probs.
    """
    np.random.seed(42)
    Y_true = np.array([
        [1, 0],
        [0, 1],
        [1, 1],
        [0, 0]
    ], dtype=np.int32)
    Y_pred = np.array([
        [0.8, 0.2],
        [0.1, 0.9],
        [0.7, 0.6],
        [0.3, 0.1]
    ], dtype=np.float32)
    targets = [316866, 201826]

    # Must succeed with correct signature
    report = evaluate_multitarget_predictions(
        Y_true=Y_true,
        Y_pred_proba=Y_pred,
        target_concept_ids=targets
    )
    assert "macro_metrics" in report
    assert "ranking_metrics" in report
    assert "per_target" in report

    # Must raise TypeError if misspelled keyword argument Y_pred_probs is passed
    with pytest.raises(TypeError) as excinfo:
        evaluate_multitarget_predictions(
            Y_true=Y_true,
            Y_pred_probs=Y_pred,
            target_concept_ids=targets
        )
    assert "unexpected keyword argument" in str(excinfo.value)
