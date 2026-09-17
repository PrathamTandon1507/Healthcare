"""
Script: scripts/train_stacking.py
Phase 10 & Phase 11: Multi-Target Out-Of-Fold Stacking Ensemble Training & Hyperparameter Finalization.

Executes:
1. Frozen Hyperparameter Manifest compilation & saving (models/configs/frozen_hyperparameters.json).
2. Patient-level 5-fold Out-Of-Fold (OOF) cross-validation for Base Learners (LR, RF, XGB).
3. Meta-Learner (Logistic Regression) fitting on OOF probability matrices.
4. Refitting base learners on full training data and saving StackedEnsembleModel containers.
5. Saving OOF prediction cache to data/parquet/oof_predictions.parquet.
6. Multi-target evaluation across Validation and Prospective Test splits.
7. Generating comparative benchmarking ladder reports (Baseline vs LR vs RF vs XGB vs Stack).
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.data.labels import TARGET_41_DISEASES, CONDITION_METADATA
from src.features.pipeline import get_baseline_feature_columns
from src.models.data_loader import load_dataset_splits
from src.models.configs import save_frozen_configs
from src.models.stacking import train_single_stacked_ensemble, StackedEnsembleModel
from src.models.baseline import save_model_artifact, load_model_artifact, detect_xgboost_device
from src.models.metrics import evaluate_multitarget_predictions


def main():
    parser = argparse.ArgumentParser(description="Phase 10 & 11 Stacking Ensemble Training & Finalization")
    parser.add_argument("--target_cid", type=int, default=None, help="Optional single concept ID to train")
    parser.add_argument("--device", type=str, default="auto", choices=["auto", "cuda", "cpu"], help="Compute device for XGBoost")
    parser.add_argument("--no_resume", action="store_true", help="Force retrain of existing stacked models")
    parser.add_argument("--n_jobs", type=int, default=8, help="CPU thread count")
    args = parser.parse_args()

    resume = not args.no_resume
    targets = [args.target_cid] if args.target_cid is not None else TARGET_41_DISEASES
    resolved_device = detect_xgboost_device(preferred_device=args.device)

    print("=" * 80)
    print(f"PHASE 10 + 11: OUT-OF-FOLD STACKING ENSEMBLE & HYPERPARAMETER FINALIZATION ({len(targets)} targets)")
    print(f"Base Models: Logistic Regression + Random Forest + XGBoost ({resolved_device.upper()})")
    print(f"Meta-Learner: L2-Regularized Logistic Regression")
    print("=" * 80)

    # 1. Compile and save frozen hyperparameter manifest (Phase 11)
    print("\nCompiling frozen hyperparameter manifest...")
    manifest = save_frozen_configs(output_path="models/configs/frozen_hyperparameters.json")
    print(f"Frozen configuration registry contains {manifest['n_targets']} comorbidity targets.")

    # 2. Load dataset splits and extract train person_ids
    print("\nLoading dataset splits and patient identifiers...")
    t0_load = time.time()
    train_split, val_split, test_split = load_dataset_splits(
        target_concept_ids=targets,
        random_seed=42
    )

    # Load patient IDs for training split from splits parquet
    con = duckdb.connect()
    train_df = con.execute("SELECT person_id FROM 'data/parquet/splits_inpatient_ed.parquet' WHERE split = 'train'").fetchnumpy()
    train_person_ids = train_df["person_id"]
    assert len(train_person_ids) == train_split.n_samples, "Mismatch between person_ids and train split rows!"

    print(f"Loaded dataset in {time.time() - t0_load:.2f}s:")
    print(f"  - Train : {train_split.n_samples:,} rows ({len(np.unique(train_person_ids)):,} unique patients)")
    print(f"  - Val   : {val_split.n_samples:,} rows")
    print(f"  - Test  : {test_split.n_samples:,} rows")
    print(f"  - Active Predictors : {train_split.n_features}")

    out_dir = "models/saved/stack_tuned"
    reports_dir = "reports"
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    oof_predictions_dict = {}
    preds_val = np.zeros((val_split.n_samples, len(targets)), dtype=np.float32)
    preds_test = np.zeros((test_split.n_samples, len(targets)), dtype=np.float32)

    stack_diagnostics = {}
    meta_weights_summary = {}

    total_t0 = time.time()
    for idx, cid in enumerate(targets):
        cname, cat, _ = CONDITION_METADATA.get(cid, (f"Disease {cid}", "General", True))
        model_path = f"{out_dir}/model_{cid}.joblib"
        meta_path = f"{out_dir}/model_{cid}_metadata.json"
        t_start = time.time()

        target_cfg = manifest["models"].get(str(cid), {})
        lr_cfg = target_cfg.get("logistic_regression", {"C": 1.0, "class_weight": "balanced"})
        rf_cfg = target_cfg.get("random_forest", {"n_estimators": 100, "max_depth": 10, "min_samples_leaf": 5, "max_features": "sqrt", "class_weight": "balanced"})
        xgb_cfg = target_cfg.get("xgboost", {"n_estimators": 200, "max_depth": 6, "learning_rate": 0.05, "reg_lambda": 1.0})

        y_tr = train_split.get_target_vector(cid)
        pos_cnt = int(np.sum(y_tr))

        if resume and os.path.exists(model_path) and os.path.exists(meta_path):
            print(f"[{idx+1}/{len(targets)}] Resuming existing Stacked Model: {cid} ({cname})...")
            stack_model = load_model_artifact(model_path)
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        else:
            print(f"[{idx+1}/{len(targets)}] Training 5-Fold OOF Stack for: {cid} ({cname}) | Pos: {pos_cnt:,}...")
            stack_model, oof_mat, meta = train_single_stacked_ensemble(
                X_train=train_split.X,
                y_train=y_tr,
                train_person_ids=train_person_ids,
                feature_names=train_split.feature_names,
                target_cid=cid,
                lr_config=lr_cfg,
                rf_config=rf_cfg,
                xgb_config=xgb_cfg,
                n_splits=5,
                device=resolved_device,
                random_seed=42,
                n_jobs=args.n_jobs
            )
            save_model_artifact(stack_model, model_path, metadata=meta)
            oof_predictions_dict[f"oof_lr_{cid}"] = oof_mat[:, 0]
            oof_predictions_dict[f"oof_rf_{cid}"] = oof_mat[:, 1]
            oof_predictions_dict[f"oof_xgb_{cid}"] = oof_mat[:, 2]
            print(f"  -> Weights: LR={meta['meta_weights']['weight_lr']:.3f}, RF={meta['meta_weights']['weight_rf']:.3f}, XGB={meta['meta_weights']['weight_xgb']:.3f} | OOF AUPRC: {meta['oof_metrics']['stack_auprc']:.4f} in {time.time() - t_start:.2f}s")

        # Record validation and test predictions
        preds_val[:, idx] = stack_model.predict_proba(val_split.X)[:, 1]
        preds_test[:, idx] = stack_model.predict_proba(test_split.X)[:, 1]

        stack_diagnostics[cid] = meta
        meta_weights_summary[cid] = {
            "name": cname,
            "category": cat,
            "meta_weights": meta.get("meta_weights", {}),
            "oof_metrics": meta.get("oof_metrics", {})
        }

    total_time = time.time() - total_t0
    print(f"\nProcessed {len(targets)} Stacked Ensemble models in {total_time:.2f}s.")

    # 3. Save OOF predictions Parquet if newly generated
    if oof_predictions_dict:
        oof_parquet_path = "data/parquet/oof_predictions.parquet"
        print(f"Saving OOF predictions to {oof_parquet_path}...")
        arrow_table = pa.Table.from_arrays(
            [pa.array(arr) for arr in oof_predictions_dict.values()],
            names=list(oof_predictions_dict.keys())
        )
        pq.write_table(arrow_table, oof_parquet_path)

    # 4. Multi-Target Evaluation on Validation and Test
    print("\nEvaluating Multi-Target Predictions on Validation and Test splits...")
    val_report = evaluate_multitarget_predictions(
        Y_true=val_split.Y,
        Y_pred_proba=preds_val,
        target_concept_ids=targets,
        condition_metadata=CONDITION_METADATA
    )

    test_report = evaluate_multitarget_predictions(
        Y_true=test_split.Y,
        Y_pred_proba=preds_test,
        target_concept_ids=targets,
        condition_metadata=CONDITION_METADATA
    )

    # 5. Save JSON Deliverables
    eval_json_path = f"{reports_dir}/phase10_stacking_evaluation.json"
    weights_json_path = f"{reports_dir}/phase10_meta_learner_weights.json"

    clean_weights = {str(k): v for k, v in meta_weights_summary.items()}
    with open(eval_json_path, "w", encoding="utf-8") as f:
        json.dump({"validation": val_report, "test": test_report, "weights_summary": clean_weights}, f, indent=2)

    with open(weights_json_path, "w", encoding="utf-8") as f:
        json.dump(clean_weights, f, indent=2)

    print(f"Saved evaluation JSON: {eval_json_path}")
    print(f"Saved meta-weights JSON: {weights_json_path}")

    # 6. Load Benchmark Comparison Reports for comparative ladder table
    lr_eval_path = f"{reports_dir}/phase7_lr_evaluation.json"
    rf_eval_path = f"{reports_dir}/phase8_rf_evaluation.json"
    xgb_eval_path = f"{reports_dir}/phase9_xgb_evaluation.json"

    lr_test_auprc = 0.0502
    rf_test_auprc = 0.0739
    xgb_test_auprc = 0.0816

    if os.path.exists(lr_eval_path):
        with open(lr_eval_path, "r", encoding="utf-8") as f:
            lr_test_auprc = json.load(f).get("test_metrics", {}).get("macro_metrics", {}).get("macro_auprc", lr_test_auprc)
    if os.path.exists(rf_eval_path):
        with open(rf_eval_path, "r", encoding="utf-8") as f:
            rf_test_auprc = json.load(f).get("test_metrics", {}).get("macro_metrics", {}).get("macro_auprc", rf_test_auprc)
    if os.path.exists(xgb_eval_path):
        with open(xgb_eval_path, "r", encoding="utf-8") as f:
            xgb_test_auprc = json.load(f).get("test", {}).get("macro_metrics", {}).get("macro_auprc", xgb_test_auprc)

    # 7. Generate Markdown Evaluation Report
    md_eval_path = f"{reports_dir}/phase10_stacking_evaluation.md"
    v_m = val_report["macro_metrics"]
    t_m = test_report["macro_metrics"]
    t_rk = test_report.get("ranking_metrics", {})
    v_rk = val_report.get("ranking_metrics", {})

    with open(md_eval_path, "w", encoding="utf-8") as f:
        f.write("# Phase 10: Stacked Ensemble Multi-Model Evaluation Report\n\n")
        f.write("## 1. Executive Summary & Full Ensemble Comparison Ladder\n\n")
        f.write(f"- **Targets Modeled**: {len(targets)} chronic comorbidities\n")
        f.write(f"- **Predictor Features**: {train_split.n_features} active clinical features\n")
        f.write(f"- **Ensemble Architecture**: 5-Fold Patient-Level OOF Base Learners (LR + RF + XGB) $\\rightarrow$ Logistic Regression Meta-Learner\n")
        f.write(f"- **Total Runtime**: {total_time:.2f} seconds\n\n")

        f.write("| Model Family | Split | Macro-AUPRC | Macro-AUROC | Precision@3 | Recall@3 | MAP@3 | Brier Score |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        f.write("| Prevalence Floor (Phase 6) | Test | 0.0025 | 0.5000 | 0.81% | 1.83% | 0.0163 | 0.0028 |\n")
        f.write(f"| Tuned Logistic Regression (Phase 7) | Test | {lr_test_auprc:.4f} | 0.8676 | 20.94% | 53.15% | 0.4007 | 0.0527 |\n")
        f.write(f"| Tuned Random Forest (Phase 8) | Test | {rf_test_auprc:.4f} | 0.8772 | 25.51% | 63.66% | 0.5315 | 0.0401 |\n")
        f.write(f"| Tuned XGBoost (Phase 9) | Test | {xgb_test_auprc:.4f} | 0.8824 | 26.95% | 66.65% | 0.5555 | 0.0499 |\n")
        f.write(f"| **Stacked Ensemble (Phase 10)** | **Val** | **{v_m['macro_auprc']:.4f}** | **{v_m['macro_auroc']:.4f}** | **{v_rk.get('precision_at_3', 0.0)*100:.2f}%** | **{v_rk.get('recall_at_3', 0.0)*100:.2f}%** | **{v_rk.get('map_at_3', 0.0):.4f}** | **{v_m['macro_brier_score']:.4f}** |\n")
        f.write(f"| **Stacked Ensemble (Phase 10)** | **Test** | **{t_m['macro_auprc']:.4f}** | **{t_m['macro_auroc']:.4f}** | **{t_rk.get('precision_at_3', 0.0)*100:.2f}%** | **{t_rk.get('recall_at_3', 0.0)*100:.2f}%** | **{t_rk.get('map_at_3', 0.0):.4f}** | **{t_m['macro_brier_score']:.4f}** |\n\n")

        f.write("## 2. Per-Disease Performance Table (Held-Out Prospective Test Split)\n\n")
        f.write("| Concept ID | Disease Name | Category | Test Prevalence | Stack AUPRC | Lift vs Prev | AUROC | LR Weight | RF Weight | XGB Weight |\n")
        f.write("|---|---|---|---|---|---|---|---|---|---|\n")
        for cid in targets:
            cid_str = str(cid)
            d = test_report["per_target"].get(cid_str, {})
            diag = meta_weights_summary.get(cid, {})
            cname, cat, _ = CONDITION_METADATA.get(cid, (f"Disease {cid}", "General", True))
            p = d.get("prevalence", 0.0)
            auprc = d.get("auprc", 0.0)
            lift = (auprc / p) if p > 0 else 0.0
            w = diag.get("meta_weights", {})
            f.write(f"| `{cid}` | **{cname}** | {cat} | {p*100:.3f}% | **{auprc:.4f}** | {lift:.1f}x | {d.get('auroc', 0.0):.4f} | {w.get('weight_lr', 0.0):+.2f} | {w.get('weight_rf', 0.0):+.2f} | {w.get('weight_xgb', 0.0):+.2f} |\n")

    # 8. Generate Meta-Learner Weights Markdown Report
    md_weights_path = f"{reports_dir}/phase10_meta_learner_weights.md"
    with open(md_weights_path, "w", encoding="utf-8") as f:
        f.write("# Phase 10: Meta-Learner Weight Attribution & Base Model Trust Audit\n\n")
        f.write("## 1. Meta-Learner Trust Coefficients per Comorbidity Target\n\n")
        f.write("| Concept ID | Disease Name | Category | Intercept | LR Weight (Linear Anchor) | RF Weight (Bagged Non-Linear) | XGB Weight (Boosted Trees) | Dominant Base Model |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for cid, diag in meta_weights_summary.items():
            w = diag.get("meta_weights", {})
            w_lr = w.get("weight_lr", 0.0)
            w_rf = w.get("weight_rf", 0.0)
            w_xgb = w.get("weight_xgb", 0.0)
            
            dominant = "XGBoost" if (w_xgb >= w_rf and w_xgb >= w_lr) else ("Random Forest" if w_rf >= w_lr else "Logistic Regression")
            f.write(f"| `{cid}` | **{diag['name']}** | {diag['category']} | {w.get('intercept', 0.0):+.2f} | {w_lr:+.3f} | {w_rf:+.3f} | {w_xgb:+.3f} | **{dominant}** |\n")

    # 9. Generate Phase 11 Hyperparameter Manifest Markdown
    md_manifest_path = f"{reports_dir}/phase11_hyperparameter_manifest.md"
    with open(md_manifest_path, "w", encoding="utf-8") as f:
        f.write("# Phase 11: Frozen Hyperparameter Manifest & Registry Report\n\n")
        f.write("## 1. Overview & Discipline\n\n")
        f.write("- **Methodological Rule**: All hyperparameters selected strictly using inner-validation and training/validation splits. Zero test data was touched during tuning.\n")
        f.write(f"- **Targets Covered**: {manifest['n_targets']} comorbidity targets\n")
        f.write("- **Registry File**: `models/configs/frozen_hyperparameters.json`\n\n")
        f.write("## 2. Frozen Base Model Configurations\n\n")
        f.write("| Concept ID | Disease Name | Category | LR C | RF Depth | RF Min Leaf | RF Max Feat | XGB Depth | XGB LR | XGB L2 |\n")
        f.write("|---|---|---|---|---|---|---|---|---|---|\n")
        for cid_str, m in manifest["models"].items():
            lr_c = m["logistic_regression"]["C"]
            rf_d = m["random_forest"]["max_depth"]
            rf_l = m["random_forest"]["min_samples_leaf"]
            rf_f = m["random_forest"]["max_features"]
            xgb_d = m["xgboost"]["max_depth"]
            xgb_lr = m["xgboost"]["learning_rate"]
            xgb_l2 = m["xgboost"]["reg_lambda"]
            f.write(f"| `{cid_str}` | **{m['disease_name']}** | {m['category']} | `{lr_c}` | `{rf_d}` | `{rf_l}` | `{rf_f}` | `{xgb_d}` | `{xgb_lr}` | `{xgb_l2}` |\n")

    print(f"\nSaved Markdown reports:\n  - {md_eval_path}\n  - {md_weights_path}\n  - {md_manifest_path}")

    print("\n" + "=" * 80)
    print("PHASE 10 & 11 COMPLETED SUCCESSFULLY.")
    print(f"  [Validation] Macro-AUPRC: {v_m['macro_auprc']:.4f} | AUROC: {v_m['macro_auroc']:.4f}")
    print(f"  [Test]       Macro-AUPRC: {t_m['macro_auprc']:.4f} | AUROC: {t_m['macro_auroc']:.4f}")
    print(f"  [Test]       Precision@3: {t_rk.get('precision_at_3', 0.0)*100:.2f}% | Recall@3: {t_rk.get('recall_at_3', 0.0)*100:.2f}% | MAP@3: {t_rk.get('map_at_3', 0.0):.4f}")
    print("=" * 80)


if __name__ == "__main__":
    main()
