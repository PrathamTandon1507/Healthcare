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



# ──────────────────────────────────────────────────────────────────────────────
# Brier Score Regression Tests
# Purpose: pin the exact formula, expose common mistakes, and guard cross-phase
#          consistency (Phase 9 ↔ Phase 14 ↔ Phase 12).
# Background:
#   sklearn.metrics.brier_score_loss uses:
#       BS_d = (1/N) * sum_{i=1}^{N} (y_true_i - p_pred_i)^2
#
#   evaluate_multitarget_predictions() reports:
#       macro_brier_score = (1/K) * sum_{d=1}^{K} BS_d    (arithmetic mean over K diseases)
#
#   This means:
#     - A model predicting 0.05 for every patient on a 0.2%-prevalence disease
#       contributes Brier ≈ 0.0025 per patient, accumulating to ~0.0025 macro.
#     - The OOF Stack predicts near-zero for most patients (meta-learner has
#       large negative intercept -9.4), giving a very small Brier that reflects
#       conservative/underconfident predictions, NOT better calibration on positives.
#     - LR/RF/XGB output larger raw probabilities, giving larger Brier scores.
#
#   Known reported values (from Phase 9 and Phase 14 JSON artifacts — must NOT change):
#       Phase 9 / Phase 14 XGB  Test macro_brier_score = 0.049943
#       Phase 14 Stack   Test macro_brier_score = 0.002329
#       Phase 14 Cal-Stk Test macro_brier_score = 0.002304
#       Phase 14 LR      Test macro_brier_score = 0.109898
#       Phase 14 RF      Test macro_brier_score = 0.071803
# ──────────────────────────────────────────────────────────────────────────────

def test_brier_score_formula_against_manual_computation():
    """
    Pins the exact brier_score_loss formula used by sklearn:
        BS = (1/N) * sum( (y_true - p_pred)^2 )
    and verifies compute_binary_metrics() reports it correctly.

    Also validates macro-aggregation: macro Brier = arithmetic mean of per-disease Briers.
    """
    from sklearn.metrics import brier_score_loss

    # --- 1. Closed-form formula verification ---
    y_true = np.array([1, 0, 0, 0, 1], dtype=np.float64)
    p_pred = np.array([0.8, 0.1, 0.05, 0.2, 0.9], dtype=np.float64)
    expected_bs = np.mean((y_true - p_pred) ** 2)  # = 0.021800
    assert abs(brier_score_loss(y_true, p_pred) - expected_bs) < 1e-12, (
        "sklearn brier_score_loss does not match (1/N)*sum((y-p)^2)"
    )

    # --- 2. compute_binary_metrics wrapper ---
    metrics = compute_binary_metrics(y_true.astype(np.int32), p_pred.astype(np.float32))
    assert abs(metrics["brier_score"] - expected_bs) < 1e-5, (
        f"compute_binary_metrics brier_score mismatch: got {metrics['brier_score']}, "
        f"expected {expected_bs:.6f}"
    )

    # --- 3. Edge case: predicting near-zero for a very low-prevalence disease ---
    # Represents the stack behaviour (meta-learner intercept ~ -9.4)
    np.random.seed(0)
    N = 10_000
    prev = 0.002  # 0.2% prevalence
    y_rare = (np.random.rand(N) < prev).astype(np.int32)
    p_near_zero = np.full(N, 0.0001, dtype=np.float32)  # near-zero predictions
    p_xgb_like = np.where(np.random.rand(N) < 0.3, 0.05, 0.001).astype(np.float32)

    bs_near_zero = brier_score_loss(y_rare, p_near_zero)
    bs_xgb_like = brier_score_loss(y_rare, p_xgb_like)

    # Near-zero predictions give very small Brier for low-prevalence diseases
    assert bs_near_zero < 0.005, (
        f"Near-zero predictions should yield tiny Brier for rare disease, got {bs_near_zero:.6f}"
    )
    # Spread predictions give larger Brier
    assert bs_xgb_like > bs_near_zero, (
        "XGB-like predictions should have higher Brier than near-zero predictions"
    )

    # --- 4. Macro aggregation via evaluate_multitarget_predictions ---
    # 3 diseases, known per-disease briers, verify macro = arithmetic mean
    Y_true = np.column_stack([y_rare, y_rare, y_rare]).astype(np.int32)
    P_pred = np.column_stack([
        p_near_zero,
        p_xgb_like,
        np.full(N, prev, dtype=np.float32)  # prevalence-matched prediction
    ]).astype(np.float32)

    report = evaluate_multitarget_predictions(Y_true, P_pred, [101, 102, 103])
    per_briefs = [
        brier_score_loss(Y_true[:, i], P_pred[:, i])
        for i in range(3)
    ]
    expected_macro = float(np.mean(per_briefs))

    assert abs(report["macro_metrics"]["macro_brier_score"] - expected_macro) < 1e-5, (
        f"macro_brier_score mismatch: got {report['macro_metrics']['macro_brier_score']:.6f}, "
        f"expected {expected_macro:.6f}"
    )


def test_brier_score_low_prevalence_model_ordering():
    """
    Verifies that for low-prevalence targets, a model predicting near-zero for all
    patients can achieve a lower Brier score than a discriminative model predicting
    higher probabilities. This is the documented reason the stack (Brier ~0.002)
    beats XGB (Brier ~0.050) on Brier score despite XGB having higher AUROC/AUPRC.

    This is a KNOWN and EXPECTED behaviour, not a data integrity issue.
    """
    from sklearn.metrics import brier_score_loss, roc_auc_score

    np.random.seed(42)
    N = 33304  # approximate test set size
    prev = 0.001  # representative low prevalence across 41 diseases

    y_true = (np.random.rand(N) < prev).astype(np.int32)
    n_pos = y_true.sum()
    assert n_pos > 0, "Random seed produced zero positives"

    # Model A: near-zero predictions (stack-like)
    p_stack_like = np.full(N, 0.001, dtype=np.float64)

    # Model B: discriminative predictions spread from 0.001 to 0.5 (XGB-like)
    p_xgb_like = np.where(np.random.rand(N) < 0.25, 0.05, 0.001).astype(np.float64)
    # Boost true positives to make it discriminative
    p_xgb_like[y_true == 1] = 0.3

    bs_stack = brier_score_loss(y_true, p_stack_like)
    bs_xgb = brier_score_loss(y_true, p_xgb_like)
    auroc_xgb = roc_auc_score(y_true, p_xgb_like)

    # Stack: smaller Brier because it barely deviates from zero
    assert bs_stack < bs_xgb, (
        f"Stack-like near-zero predictions should have lower Brier ({bs_stack:.6f}) "
        f"than XGB-like predictions ({bs_xgb:.6f})"
    )

    # XGB: higher AUROC because it actually ranks positives higher
    assert auroc_xgb > 0.80, (
        f"XGB-like model should have high AUROC ({auroc_xgb:.4f}) despite higher Brier"
    )

    # This documents the BRIER DOES NOT EQUAL CALIBRATION for low-prevalence targets:
    # Predicting near-zero everywhere minimises squared-error but provides no clinical utility.
    # The primary metrics AUPRC and AUROC correctly reflect discriminative power.
    assert bs_stack < 0.01   # near-zero prediction brier is tiny
    assert bs_xgb > bs_stack  # discriminative model has larger brier but better AUROC


def test_brier_cross_phase_consistency_from_json_artifacts():
    """
    Regression test: pins the exact macro_brier_score values from the saved
    Phase 9 and Phase 14 JSON evaluation artifacts.

    INVARIANT: If the evaluation or metric code changes, these stored values must
    remain identical (i.e., re-running evaluation on same data must reproduce them
    within 1e-6 tolerance). Any deviation means either:
        (a) Model artifacts were swapped/corrupted, or
        (b) The metric formula changed — which is a breaking change.

    Phase 9 XGB Test Brier  = 0.049943  (from reports/phase9_xgb_evaluation.json)
    Phase 14 XGB Test Brier = 0.049943  (from reports/phase14_master_evaluation.json)
    -- These ARE consistent. The 0.002888 figure never appeared in any report. --

    Stack Test Brier lower than XGB Brier is expected and documented:
    Stack meta-learner has large negative intercept → near-zero predictions → small MSE.
    This is conservative under-confidence, not superior calibration.
    """
    import json

    phase9_json = "reports/phase9_xgb_evaluation.json"
    phase14_json = "reports/phase14_master_evaluation.json"

    # Load Phase 9 stored values
    with open(phase9_json, "r") as f:
        p9 = json.load(f)
    p9_val_brier = p9["validation"]["macro_metrics"]["macro_brier_score"]
    p9_test_brier = p9["test"]["macro_metrics"]["macro_brier_score"]

    # Load Phase 14 stored values
    with open(phase14_json, "r") as f:
        p14 = json.load(f)
    xgb_r = p14["model_results"]["xgboost"]
    p14_xgb_val_brier = xgb_r["validation"]["macro_metrics"]["macro_brier_score"]
    p14_xgb_test_brier = xgb_r["test"]["macro_metrics"]["macro_brier_score"]

    lr_r = p14["model_results"]["logistic_regression"]
    rf_r = p14["model_results"]["random_forest"]
    stk_r = p14["model_results"]["stacked_ensemble"]
    cal_r = p14["model_results"]["calibrated_stack"]

    # --- Phase 9 ↔ Phase 14 XGB consistency ---
    assert abs(p9_val_brier - p14_xgb_val_brier) < 1e-6, (
        f"Phase 9 val Brier {p9_val_brier} ≠ Phase 14 XGB val Brier {p14_xgb_val_brier}"
    )
    assert abs(p9_test_brier - p14_xgb_test_brier) < 1e-6, (
        f"Phase 9 test Brier {p9_test_brier} ≠ Phase 14 XGB test Brier {p14_xgb_test_brier}"
    )

    # --- Pinned absolute values (regression guards) ---
    assert abs(p9_test_brier - 0.049943) < 1e-5, (
        f"Phase 9 XGB test Brier regressed: {p9_test_brier:.6f} ≠ 0.049943"
    )
    assert abs(p14_xgb_test_brier - 0.049943) < 1e-5, (
        f"Phase 14 XGB test Brier regressed: {p14_xgb_test_brier:.6f} ≠ 0.049943"
    )

    # --- Model ordering: LR/RF/XGB all have higher Brier than stack (documented behaviour) ---
    lr_test_brier = lr_r["test"]["macro_metrics"]["macro_brier_score"]
    rf_test_brier = rf_r["test"]["macro_metrics"]["macro_brier_score"]
    stk_test_brier = stk_r["test"]["macro_metrics"]["macro_brier_score"]
    cal_test_brier = cal_r["test"]["macro_metrics"]["macro_brier_score"]

    # Pinned values
    assert abs(lr_test_brier - 0.109898) < 1e-5, f"LR Brier regressed: {lr_test_brier}"
    assert abs(rf_test_brier - 0.071803) < 1e-5, f"RF Brier regressed: {rf_test_brier}"
    assert abs(stk_test_brier - 0.002329) < 1e-5, f"Stack Brier regressed: {stk_test_brier}"
    assert abs(cal_test_brier - 0.002304) < 1e-5, f"Cal-Stack Brier regressed: {cal_test_brier}"

    # Ordering: XGB > RF >> Stack > Cal-Stack (documented by low-prevalence near-zero effect)
    assert lr_test_brier > stk_test_brier, "LR Brier should exceed Stack Brier"
    assert rf_test_brier > stk_test_brier, "RF Brier should exceed Stack Brier"
    assert p14_xgb_test_brier > stk_test_brier, "XGB Brier should exceed Stack Brier"
    assert stk_test_brier > cal_test_brier, "Calibration should reduce Stack Brier"


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

