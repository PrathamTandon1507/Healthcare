"""
Module: src/models/calibration.py
Phase 12: Multi-Target Probability Calibration Module.

Features:
1. Platt Scaling (Sigmoid Logistic Calibration on logit space) & Isotonic Regression.
2. Fit calibrators strictly on Validation split predictions (zero test leakage).
3. Brier Score Loss & Reliability Curve (Calibration curve) generation across all 41 diseases.
4. Per-disease selection of optimal calibration method (Platt vs Isotonic vs Raw) based strictly on Validation Brier score.
5. Calibrated prediction forward pass and persistence of calibrator artifacts.
"""

import os
import sys
import json
import joblib
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss
from sklearn.calibration import calibration_curve

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.data.labels import TARGET_41_DISEASES, CONDITION_METADATA


class DiseaseProbabilityCalibrator:
    """
    Encapsulates calibration for a single target disease comorbidity model.
    Supports:
      - 'platt': Sigmoid logistic regression on probability logit / log-odds
      - 'isotonic': Non-parametric isotonic regression
      - 'raw': Identity passthrough (when uncalibrated yields lower validation Brier score)
    """
    def __init__(self, target_cid: int, method: str = "platt"):
        self.target_cid = target_cid
        self.method = method
        self.calibrator = None
        self.uncalibrated_val_brier = None
        self.calibrated_val_brier = None
        self.brier_improvement = None

    def fit(self, y_val: np.ndarray, p_val: np.ndarray):
        """
        Fits candidate calibrators on validation split ground truth and predicted probabilities,
        and selects the optimal method minimizing Validation Brier score.
        """
        self.uncalibrated_val_brier = float(brier_score_loss(y_val, p_val))
        eps = 1e-7
        p_clipped = np.clip(p_val, eps, 1.0 - eps)

        # 1. Platt Scaler (Logistic on log-odds)
        logits = np.log(p_clipped / (1.0 - p_clipped)).reshape(-1, 1)
        platt = LogisticRegression(solver="lbfgs", C=1.0, random_state=42)
        try:
            platt.fit(logits, y_val)
            platt_probs = platt.predict_proba(logits)[:, 1]
            platt_brier = float(brier_score_loss(y_val, platt_probs))
        except Exception:
            platt = None
            platt_brier = 999.0

        # 2. Isotonic Scaler
        iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        try:
            iso.fit(p_val, y_val)
            iso_probs = iso.predict(p_val)
            iso_brier = float(brier_score_loss(y_val, iso_probs))
        except Exception:
            iso = None
            iso_brier = 999.0

        # Select best method based on validation Brier score
        candidates = [
            ("raw", None, self.uncalibrated_val_brier),
            ("platt", platt, platt_brier),
            ("isotonic", iso, iso_brier)
        ]
        candidates.sort(key=lambda x: x[2])

        best_method, best_cal, best_brier = candidates[0]
        self.method = best_method
        self.calibrator = best_cal
        self.calibrated_val_brier = float(best_brier)
        self.brier_improvement = float(self.uncalibrated_val_brier - self.calibrated_val_brier)
        return self

    def predict_proba(self, p_raw: np.ndarray) -> np.ndarray:
        """Applies fitted calibrator to raw model probability output."""
        if self.method == "raw" or self.calibrator is None:
            return np.clip(p_raw, 0.0, 1.0).astype(np.float32)

        eps = 1e-7
        if self.method == "platt":
            p_clipped = np.clip(p_raw, eps, 1.0 - eps)
            logits = np.log(p_clipped / (1.0 - p_clipped)).reshape(-1, 1)
            return self.calibrator.predict_proba(logits)[:, 1].astype(np.float32)

        elif self.method == "isotonic":
            return self.calibrator.predict(p_raw).astype(np.float32)

        return np.clip(p_raw, 0.0, 1.0).astype(np.float32)


def fit_all_calibrators(
    Y_val: np.ndarray,
    P_val_raw: np.ndarray,
    target_concept_ids: List[int]
) -> Tuple[Dict[int, DiseaseProbabilityCalibrator], Dict[str, Any]]:
    """
    Fits separate calibrators for all K target diseases using validation set probabilities.
    """
    calibrators = {}
    summary = {}

    uncal_briers = []
    cal_briers = []

    for idx, cid in enumerate(target_concept_ids):
        y_v = Y_val[:, idx]
        p_v = P_val_raw[:, idx]

        cal = DiseaseProbabilityCalibrator(target_cid=cid)
        cal.fit(y_v, p_v)
        calibrators[cid] = cal

        uncal_briers.append(cal.uncalibrated_val_brier)
        cal_briers.append(cal.calibrated_val_brier)

        cname, cat, _ = CONDITION_METADATA.get(cid, (f"Disease {cid}", "General", True))
        summary[str(cid)] = {
            "concept_id": cid,
            "disease_name": cname,
            "category": cat,
            "best_method": cal.method,
            "uncalibrated_val_brier": round(cal.uncalibrated_val_brier, 6),
            "calibrated_val_brier": round(cal.calibrated_val_brier, 6),
            "brier_reduction": round(cal.brier_improvement, 6),
            "improved": cal.brier_improvement > 1e-6
        }

    macro_summary = {
        "macro_uncalibrated_brier": round(float(np.mean(uncal_briers)), 6),
        "macro_calibrated_brier": round(float(np.mean(cal_briers)), 6),
        "macro_brier_reduction": round(float(np.mean(uncal_briers) - np.mean(cal_briers)), 6),
        "n_targets": len(target_concept_ids),
        "n_improved": sum(1 for v in summary.values() if v["improved"])
    }

    return calibrators, {"macro_summary": macro_summary, "per_disease": summary}


def evaluate_calibration_on_split(
    Y_split: np.ndarray,
    P_raw: np.ndarray,
    calibrators: Dict[int, DiseaseProbabilityCalibrator],
    target_concept_ids: List[int],
    n_bins: int = 10
) -> Dict[str, Any]:
    """
    Evaluates uncalibrated vs calibrated probabilities on held-out split (Validation or Test).
    Computes Brier scores and reliability diagram binning.
    """
    results = {}
    raw_briers = []
    cal_briers = []

    for idx, cid in enumerate(target_concept_ids):
        y_true = Y_split[:, idx]
        p_raw = P_raw[:, idx]
        cal = calibrators[cid]
        p_cal = cal.predict_proba(p_raw)

        b_raw = float(brier_score_loss(y_true, p_raw))
        b_cal = float(brier_score_loss(y_true, p_cal))

        raw_briers.append(b_raw)
        cal_briers.append(b_cal)

        # Compute reliability curve coordinates
        try:
            prob_true_raw, prob_pred_raw = calibration_curve(y_true, p_raw, n_bins=n_bins, strategy="uniform")
            prob_true_cal, prob_pred_cal = calibration_curve(y_true, p_cal, n_bins=n_bins, strategy="uniform")
            curve_raw = [{"pred": round(float(p), 4), "true": round(float(t), 4)} for p, t in zip(prob_pred_raw, prob_true_raw)]
            curve_cal = [{"pred": round(float(p), 4), "true": round(float(t), 4)} for p, t in zip(prob_pred_cal, prob_true_cal)]
        except Exception:
            curve_raw = []
            curve_cal = []

        cname, cat, _ = CONDITION_METADATA.get(cid, (f"Disease {cid}", "General", True))
        results[str(cid)] = {
            "concept_id": cid,
            "disease_name": cname,
            "category": cat,
            "calibrator_method": cal.method,
            "uncalibrated_brier": round(b_raw, 6),
            "calibrated_brier": round(b_cal, 6),
            "brier_improvement": round(b_raw - b_cal, 6),
            "reliability_curve_raw": curve_raw,
            "reliability_curve_calibrated": curve_cal
        }

    return {
        "macro_metrics": {
            "macro_uncalibrated_brier": round(float(np.mean(raw_briers)), 6),
            "macro_calibrated_brier": round(float(np.mean(cal_briers)), 6),
            "macro_brier_improvement": round(float(np.mean(raw_briers) - np.mean(cal_briers)), 6),
            "targets_improved": sum(1 for cid in target_concept_ids if results[str(cid)]["brier_improvement"] > 1e-6)
        },
        "per_target": results
    }
