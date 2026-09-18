"""
Unit tests for Phase 12 (Calibration) and Phase 13 (Explainability).
"""

import os
import sys
import pytest
import numpy as np
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.models.calibration import DiseaseProbabilityCalibrator, fit_all_calibrators, evaluate_calibration_on_split
from src.models.explainability import (
    compute_rf_feature_contributions,
    compute_xgb_feature_contributions,
    compute_lr_feature_contributions,
    explain
)
from src.models.stacking import StackedEnsembleModel
from src.models.logistic_regression import FeaturePreprocessor
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb


def test_calibration_fit_and_predict():
    np.random.seed(42)
    y_val = np.array([0, 0, 1, 0, 1, 1, 0, 0, 1, 0] * 10, dtype=np.int32)
    p_val = np.array([0.1, 0.2, 0.8, 0.3, 0.7, 0.9, 0.05, 0.15, 0.65, 0.4] * 10, dtype=np.float32)

    cal = DiseaseProbabilityCalibrator(target_cid=201826)
    cal.fit(y_val, p_val)

    assert cal.method in ("platt", "isotonic", "raw")
    assert cal.calibrated_val_brier <= cal.uncalibrated_val_brier + 1e-6

    test_probs = np.array([0.05, 0.5, 0.95], dtype=np.float32)
    cal_probs = cal.predict_proba(test_probs)

    assert len(cal_probs) == 3
    assert np.all(cal_probs >= 0.0) and np.all(cal_probs <= 1.0)


def test_rf_tree_path_contributions():
    np.random.seed(42)
    X = np.random.randn(50, 6).astype(np.float32)
    y = (X[:, 0] > 0).astype(np.int32)
    rf = RandomForestClassifier(n_estimators=10, max_depth=3, random_state=42).fit(X, y)

    x_sample = X[0]
    contribs = compute_rf_feature_contributions(rf, x_sample)

    assert contribs.shape == (6,)
    # Top contributor should be feature 0
    assert np.argmax(np.abs(contribs)) == 0


def test_xgb_shap_contributions():
    np.random.seed(42)
    X = np.random.randn(50, 6).astype(np.float32)
    y = (X[:, 1] > 0).astype(np.int32)
    clf = xgb.XGBClassifier(n_estimators=10, max_depth=3, random_state=42).fit(X, y)

    x_sample = X[0]
    contribs = compute_xgb_feature_contributions(clf, x_sample)

    assert contribs.shape == (6,)
    assert np.argmax(np.abs(contribs)) == 1


def test_unified_explain_interface():
    np.random.seed(42)
    feature_names = ["age_at_landmark", "total_prior_condition_count", "prior_obs_years", "has_hist_316866", "has_hist_201826"]
    x = np.array([65.0, 3.0, 10.0, 1.0, 0.0], dtype=np.float32)

    X_train = np.random.randn(100, 5).astype(np.float32)
    y_train = (X_train[:, 0] > 0).astype(np.int32)

    # Base models
    prep = FeaturePreprocessor(continuous_indices=[0, 1, 2])
    X_tr_lr = prep.fit_transform(X_train)
    lr = LogisticRegression(C=1.0, random_state=42).fit(X_tr_lr, y_train)
    rf = RandomForestClassifier(n_estimators=5, max_depth=2, random_state=42).fit(X_train, y_train)
    xgb_m = xgb.XGBClassifier(n_estimators=5, max_depth=2, random_state=42).fit(X_train, y_train)

    meta = LogisticRegression(C=1.0, random_state=42).fit(np.column_stack([
        lr.predict_proba(X_tr_lr)[:, 1],
        rf.predict_proba(X_train)[:, 1],
        xgb_m.predict_proba(X_train)[:, 1]
    ]), y_train)

    stack = StackedEnsembleModel(
        target_cid=316866,
        lr_model=lr,
        lr_preprocessor=prep,
        rf_model=rf,
        xgb_model=xgb_m,
        meta_learner=meta
    )

    cal = DiseaseProbabilityCalibrator(target_cid=316866, method="platt")
    cal.fit(y_train, stack.predict_proba(X_train)[:, 1])

    exp = explain(
        patient_vector=x,
        target_cid=316866,
        feature_names=feature_names,
        model_artifact=stack,
        calibrator=cal
    )

    assert "target_disease" in exp
    assert exp["target_disease"]["concept_id"] == 316866
    assert "patient_snapshot" in exp
    assert exp["patient_snapshot"]["age"] == 65.0
    assert "risk_prediction" in exp
    assert "ensemble_meta_weights" in exp
    assert "key_risk_increasing_factors" in exp
    assert "clinical_disclaimer" in exp

    # Check that disclaimer avoids causal language
    disclaimer = exp["clinical_disclaimer"]
    assert "causal" in disclaimer.lower() or "association" in disclaimer.lower()
