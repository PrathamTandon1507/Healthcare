"""
Unit tests for Phase 7: Logistic Regression Pipeline, Tuning, and Clinical Plausibility Audit.
"""

import pytest
import numpy as np
import os
from pathlib import Path

from src.models.logistic_regression import (
    FeaturePreprocessor,
    TunedLogisticRegressionModel,
    train_and_tune_single_lr,
    verify_clinical_plausibility,
    CONTINUOUS_FEATURE_NAMES
)
from src.features.pipeline import get_baseline_feature_columns
from src.data.labels import TARGET_41_DISEASES


def test_lr_feature_preprocessor_scaling():
    """
    Verifies that the FeaturePreprocessor scales continuous features and leaves binary features intact.
    """
    feature_names = get_baseline_feature_columns(TARGET_41_DISEASES)
    cont_indices = [idx for idx, name in enumerate(feature_names) if name in CONTINUOUS_FEATURE_NAMES]
    bin_indices = [idx for idx, name in enumerate(feature_names) if name not in CONTINUOUS_FEATURE_NAMES]

    preprocessor = FeaturePreprocessor(continuous_indices=cont_indices)

    # 50 sample synthetic dataset with 81 features
    X_syn = np.random.randn(50, 81).astype(np.float32)
    # Binary columns
    X_syn[:, bin_indices] = np.random.randint(0, 2, size=(50, len(bin_indices)))

    X_scaled = preprocessor.fit_transform(X_syn)

    # Continuous features should have zero mean and unit variance
    cont_scaled = X_scaled[:, cont_indices]
    np.testing.assert_allclose(np.mean(cont_scaled, axis=0), 0.0, atol=1e-5)
    np.testing.assert_allclose(np.std(cont_scaled, axis=0), 1.0, atol=1e-5)

    # Binary features should remain identical
    np.testing.assert_array_equal(X_scaled[:, bin_indices], X_syn[:, bin_indices])


def test_lr_c_tuning_and_coefficient_extraction():
    """
    Tests C hyperparameter selection and coefficient / odds ratio extraction.
    """
    feature_names = get_baseline_feature_columns(TARGET_41_DISEASES)
    
    np.random.seed(42)
    X_tr = np.random.randn(100, 81).astype(np.float32)
    y_tr = (X_tr[:, 0] > 0.5).astype(np.int32)

    X_va = np.random.randn(50, 81).astype(np.float32)
    y_va = (X_va[:, 0] > 0.5).astype(np.int32)

    model_wrap, best_c, meta = train_and_tune_single_lr(
        X_train=X_tr,
        y_train=y_tr,
        X_val=X_va,
        y_val=y_va,
        feature_names=feature_names,
        target_cid=316866,
        candidate_c_values=[0.01, 1.0],
        random_seed=42
    )

    assert best_c in [0.01, 1.0]
    assert "all_coefficients" in meta
    assert len(meta["all_coefficients"]) == 81

    # Check odds ratio relationship: OR == exp(coef)
    for feat_name, c_data in meta["all_coefficients"].items():
        expected_or = np.exp(c_data["coefficient"])
        np.testing.assert_allclose(c_data["odds_ratio"], expected_or, rtol=1e-3)


def test_clinical_plausibility_rule_verification():
    """
    Tests clinical plausibility audit logic.
    """
    mock_coefficients = {
        4229440: {  # CKD
            "all_coefficients": {
                "has_hist_201826": {"coefficient": 0.85, "odds_ratio": 2.34},
                "interaction_diabetes_and_hypertension": {"coefficient": 0.45, "odds_ratio": 1.57}
            }
        },
        317576: {  # CAD
            "all_coefficients": {
                "has_hist_316866": {"coefficient": 1.10, "odds_ratio": 3.00},
                "interaction_hypertension_and_lipid": {"coefficient": 0.60, "odds_ratio": 1.82}
            }
        },
        378419: {  # Alzheimer's
            "all_coefficients": {
                "age_at_landmark": {"coefficient": 1.45, "odds_ratio": 4.26},
                "age_gte_80": {"coefficient": 0.90, "odds_ratio": 2.46}
            }
        }
    }

    audit = verify_clinical_plausibility(mock_coefficients)
    assert audit["all_passed"] is True
    assert audit["passed_rules"] == audit["total_clinical_rules_checked"]
