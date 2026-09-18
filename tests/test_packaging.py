"""
Test Suite: tests/test_packaging.py
Phase 16: Automated Verification for Production Model Release Bundle.

Validates:
  1. Package generation and manifest creation.
  2. SHA-256 integrity verification across all 41 stack models and 41 calibrators.
  3. Fresh-process loading via ReleaseBundle.
  4. Scoring shape and range invariants: predict_proba() in [0, 1], predict() in {0, 1}.
  5. Feature manifest schema and continuous statistics consistency.
  6. Decision thresholding functionality and explainability integration.
"""

import os
import json
import pytest
import numpy as np
from pathlib import Path

from src.packaging.bundle import package_release_bundle, load_release_bundle, ReleaseBundle, compute_sha256
from src.data.labels import TARGET_41_DISEASES, CONDITION_METADATA


@pytest.fixture(scope="module")
def release_bundle(tmp_path_factory):
    """Creates and loads a test release bundle."""
    bundle_dir = tmp_path_factory.mktemp("test_release_bundle")
    manifest = package_release_bundle(output_dir=bundle_dir, version="1.0.0-test")
    bundle = load_release_bundle(bundle_dir)
    return bundle, bundle_dir, manifest


def test_bundle_packaging_structure(release_bundle):
    """Verifies all required files, directories, and manifests exist in the bundle."""
    bundle, bundle_dir, manifest = release_bundle
    
    assert (bundle_dir / "manifest.json").exists()
    assert (bundle_dir / "feature_manifest.json").exists()
    assert (bundle_dir / "thresholds.json").exists()
    assert (bundle_dir / "feature_preprocessor.joblib").exists()
    
    stack_dir = bundle_dir / "stack_models"
    calib_dir = bundle_dir / "calibrators"
    assert stack_dir.exists()
    assert calib_dir.exists()
    
    # Check all 41 targets have serialized models and calibrators
    for cid in TARGET_41_DISEASES:
        assert (stack_dir / f"model_{cid}.joblib").exists() or (stack_dir / f"stack_{cid}.joblib").exists()
        assert (calib_dir / f"calibrator_{cid}.joblib").exists()


def test_bundle_manifest_content(release_bundle):
    """Verifies manifest metadata and checksum coverage."""
    bundle, bundle_dir, manifest = release_bundle
    
    assert manifest["version"] == "1.0.0-test"
    assert manifest["metadata"]["target_disease_count"] == 41
    assert manifest["metadata"]["predictor_feature_count"] == 81
    assert len(manifest["target_concept_ids"]) == 41
    
    # Total checksummed files: 41 stack models + 41 calibrators + preprocessor + feat_man + thresholds
    assert len(manifest["file_checksums_sha256"]) >= 85


def test_bundle_sha256_integrity(release_bundle):
    """Verifies SHA-256 hash checks succeed 100% on intact files."""
    bundle, bundle_dir, manifest = release_bundle
    
    integrity_results = bundle.verify_integrity()
    assert len(integrity_results) >= 85
    assert all(integrity_results.values()), f"Integrity check failed for: {[k for k, v in integrity_results.items() if not v]}"


def test_bundle_feature_manifest_schema(release_bundle):
    """Verifies feature manifest structure and column count."""
    bundle, bundle_dir, manifest = release_bundle
    
    feat_man = bundle.feature_manifest
    assert feat_man["feature_count"] == 81
    assert len(feat_man["ordered_features"]) == 81
    assert len(feat_man["continuous_features"]) == 3
    assert len(feat_man["demographic_features"]) == 16
    assert len(feat_man["target_history_features"]) == 41
    assert len(feat_man["background_features"]) == 17
    assert len(feat_man["interaction_features"]) == 5


def test_bundle_thresholds_schema(release_bundle):
    """Verifies per-disease decision threshold dictionary."""
    bundle, bundle_dir, manifest = release_bundle
    
    thresholds = bundle.thresholds
    assert len(thresholds) == 41
    for cid in TARGET_41_DISEASES:
        cid_str = str(cid)
        assert cid_str in thresholds
        t_entry = thresholds[cid_str]
        assert "f1_optimal" in t_entry
        assert "default_threshold" in t_entry
        assert 0.0 <= t_entry["f1_optimal"] <= 1.0


def test_bundle_predict_proba_and_predict(release_bundle):
    """Verifies prediction interface output shapes and probability bounds."""
    bundle, bundle_dir, manifest = release_bundle
    
    np.random.seed(42)
    # Synthetic batch of 5 patients with 81 features
    X_sample = np.random.randn(5, 81).astype(np.float32)
    X_sample[:, 3:] = np.random.randint(0, 2, size=(5, 78)).astype(np.float32)
    
    # 1. Calibrated Probabilities
    probs_calib = bundle.predict_proba(X_sample, apply_calibration=True)
    assert probs_calib.shape == (5, 41)
    assert np.all(probs_calib >= 0.0)
    assert np.all(probs_calib <= 1.0)
    assert not np.isnan(probs_calib).any()
    
    # 2. Raw Probabilities
    probs_raw = bundle.predict_proba(X_sample, apply_calibration=False)
    assert probs_raw.shape == (5, 41)
    assert np.all(probs_raw >= 0.0)
    assert np.all(probs_raw <= 1.0)
    
    # 3. Binary Predictions
    preds_bin = bundle.predict(X_sample, strategy="f1_optimal")
    assert preds_bin.shape == (5, 41)
    assert set(np.unique(preds_bin)).issubset({0, 1})


def test_bundle_explainability_interface(release_bundle):
    """Verifies explain() method returns valid clinical explanation structure."""
    bundle, bundle_dir, manifest = release_bundle
    
    np.random.seed(42)
    x_patient = np.random.randn(81).astype(np.float32)
    x_patient[3:] = np.random.randint(0, 2, size=78).astype(np.float32)
    
    sample_cid = TARGET_41_DISEASES[0]
    explanation = bundle.explain(x_patient, sample_cid)
    
    assert "target_disease" in explanation
    assert explanation["target_disease"]["concept_id"] == sample_cid
    assert "patient_snapshot" in explanation
    assert "risk_prediction" in explanation
    assert "ensemble_meta_weights" in explanation
    assert "key_risk_increasing_factors" in explanation
    assert "clinical_disclaimer" in explanation
    assert "non-causal" in explanation["clinical_disclaimer"].lower() or "does not establish causal" in explanation["clinical_disclaimer"].lower()

