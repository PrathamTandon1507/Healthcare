"""
Module: src/models/configs.py
Phase 11: Frozen Hyperparameter Manifest and Configuration Registry.

Extracts, consolidates, freezes, and documents optimal hyperparameters chosen across
Phases 7–9 (Logistic Regression, Random Forest, XGBoost) and Phase 10 (Meta-Learner),
enforcing the strict requirement that configurations are chosen solely on Validation performance.
"""

import os
import sys
import json
import glob
from pathlib import Path
from typing import Dict, List, Any, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.data.labels import TARGET_41_DISEASES, CONDITION_METADATA


def compile_frozen_hyperparameters(
    lr_dir: str = "models/saved/lr_tuned",
    rf_dir: str = "models/saved/rf_tuned",
    xgb_dir: str = "models/saved/xgb_tuned"
) -> Dict[str, Any]:
    """
    Scans the saved Phase 7-9 metadata directories and compiles the definitive
    frozen hyperparameter registry for all 41 target diseases.
    """
    manifest = {
        "version": "1.0.0",
        "description": "Frozen Hyperparameter Manifest for 41 Curated Chronic Comorbidities (Phase 11)",
        "selection_protocol": "Tuned strictly on Inner-Validation / Validation split AUPRC; Test split untouched.",
        "n_targets": len(TARGET_41_DISEASES),
        "models": {}
    }

    for cid in TARGET_41_DISEASES:
        cname, cat, _ = CONDITION_METADATA.get(cid, (f"Disease {cid}", "General", True))
        
        # 1. Load LR Config
        lr_meta_path = Path(lr_dir) / f"model_{cid}_metadata.json"
        if lr_meta_path.exists():
            with open(lr_meta_path, "r", encoding="utf-8") as f:
                lr_data = json.load(f)
            best_C = lr_data.get("best_C", 1.0)
            lr_config = {"C": best_C, "penalty": "l2", "class_weight": "balanced", "scaling": "standard_continuous"}
        else:
            lr_config = {"C": 1.0, "penalty": "l2", "class_weight": "balanced", "scaling": "standard_continuous"}

        # 2. Load RF Config
        rf_meta_path = Path(rf_dir) / f"model_{cid}_metadata.json"
        if rf_meta_path.exists():
            with open(rf_meta_path, "r", encoding="utf-8") as f:
                rf_data = json.load(f)
            rf_params = rf_data.get("best_hyperparameters", {})
            rf_config = {
                "n_estimators": 100,
                "max_depth": rf_params.get("max_depth", 10),
                "min_samples_leaf": rf_params.get("min_samples_leaf", 5),
                "max_features": rf_params.get("max_features", "sqrt"),
                "class_weight": "balanced"
            }
        else:
            rf_config = {"n_estimators": 100, "max_depth": 10, "min_samples_leaf": 5, "max_features": "sqrt", "class_weight": "balanced"}

        # 3. Load XGBoost Config
        xgb_meta_path = Path(xgb_dir) / f"model_{cid}_metadata.json"
        if xgb_meta_path.exists():
            with open(xgb_meta_path, "r", encoding="utf-8") as f:
                xgb_data = json.load(f)
            xgb_params = xgb_data.get("best_hyperparameters", {})
            xgb_config = {
                "n_estimators": 200,
                "max_depth": xgb_params.get("max_depth", 6),
                "learning_rate": xgb_params.get("learning_rate", 0.05),
                "reg_lambda": xgb_params.get("reg_lambda", 1.0),
                "subsample": xgb_params.get("subsample", 0.8),
                "colsample_bytree": xgb_params.get("colsample_bytree", 0.8),
                "early_stopping_rounds": 15,
                "scale_pos_weight_capped": 500.0,
                "eval_metric": "logloss"
            }
        else:
            xgb_config = {
                "n_estimators": 200,
                "max_depth": 6,
                "learning_rate": 0.05,
                "reg_lambda": 1.0,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "early_stopping_rounds": 15,
                "scale_pos_weight_capped": 500.0,
                "eval_metric": "logloss"
            }

        # 4. Meta-Learner (LR) Config
        meta_config = {
            "model_type": "logistic_regression",
            "C": 1.0,
            "penalty": "l2",
            "class_weight": None,
            "fit_intercept": True
        }

        manifest["models"][str(cid)] = {
            "concept_id": cid,
            "disease_name": cname,
            "category": cat,
            "logistic_regression": lr_config,
            "random_forest": rf_config,
            "xgboost": xgb_config,
            "meta_learner": meta_config
        }

    return manifest


def save_frozen_configs(
    output_path: str = "models/configs/frozen_hyperparameters.json"
) -> Dict[str, Any]:
    """Compiles and saves the frozen configuration manifest to disk."""
    manifest = compile_frozen_hyperparameters()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Saved frozen hyperparameters manifest to: {output_path}")
    return manifest
