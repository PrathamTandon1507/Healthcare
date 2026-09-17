"""
Script: scripts/train_xgboost.py
Phase 9: Standalone XGBoost Base Model Training, Hyperparameter Tuning, Early Stopping & Diagnostic Audit.

Executes:
1. Hyperparameter grid search (max_depth, learning_rate, reg_lambda) across all K=41 targets on Validation AUPRC.
2. Early stopping evaluation on inner validation split (early_stopping_rounds=15) preventing overfit.
3. Feature importance extraction (Gain, Weight, Cover) for all 81 clinical predictors per disease.
4. Learning curve diagnostics and validation check of early stopping behavior.
5. Evaluation across Train, Validation, and Prospective Test splits.
6. Artifact & Report generation:
   - models/saved/xgb_tuned/model_<cid>.joblib
   - reports/phase9_xgb_evaluation.md / .json
   - reports/phase9_xgb_learning_curves.md / .json
   - reports/phase9_xgb_feature_importances.md / .json
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.data.labels import TARGET_41_DISEASES, CONDITION_METADATA
from src.features.pipeline import get_baseline_feature_columns
from src.models.data_loader import load_dataset_splits
from src.models.xgboost_model import train_and_tune_single_xgb
from src.models.baseline import save_model_artifact, load_model_artifact, detect_xgboost_device
from src.models.metrics import evaluate_multitarget_predictions


def main():
    parser = argparse.ArgumentParser(description="Phase 9 XGBoost Training and Diagnostics")
    parser.add_argument("--target_cid", type=int, default=None, help="Optional single concept ID to train")
    parser.add_argument("--device", type=str, default="auto", choices=["auto", "cuda", "cpu"], help="Compute device for XGBoost")
    parser.add_argument("--no_resume", action="store_true", help="Force retrain of existing models")
    parser.add_argument("--n_jobs", type=int, default=8, help="Number of CPU worker threads (if CPU fallback)")
    args = parser.parse_args()

    resume = not args.no_resume
    targets = [args.target_cid] if args.target_cid is not None else TARGET_41_DISEASES
    resolved_device = detect_xgboost_device(preferred_device=args.device)

    print("=" * 80)
    print(f"PHASE 9: XGBOOST BASE MODEL TRAINING & EARLY STOPPING ({len(targets)} targets)")
    print(f"Device: {resolved_device.upper()} (Requested: {args.device})")
    print("=" * 80)

    # 1. Load full Inpatient/ED dataset splits
    print("Loading full Inpatient/ED feature matrix and splits...")
    t0_load = time.time()
    train_split, val_split, test_split = load_dataset_splits(
        target_concept_ids=targets,
        random_seed=42
    )
    print(f"Loaded dataset in {time.time() - t0_load:.2f}s:")
    print(f"  - Train: {train_split.n_samples:,} rows")
    print(f"  - Val  : {val_split.n_samples:,} rows")
    print(f"  - Test : {test_split.n_samples:,} rows")
    print(f"  - Active Clinical Predictors: {train_split.n_features}")

    out_dir = "models/saved/xgb_tuned"
    reports_dir = "reports"
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    preds_val = np.zeros((val_split.n_samples, len(targets)), dtype=np.float32)
    preds_test = np.zeros((test_split.n_samples, len(targets)), dtype=np.float32)

    diagnostics_by_disease = {}
    importances_by_disease = {}
    tuning_summary = {}

    total_t0 = time.time()
    for idx, cid in enumerate(targets):
        cname, cat, _ = CONDITION_METADATA.get(cid, (f"Disease {cid}", "General", True))
        model_path = f"{out_dir}/model_{cid}.joblib"
        t_start = time.time()

        y_tr = train_split.get_target_vector(cid)
        y_va = val_split.get_target_vector(cid)
        pos_cnt = int(np.sum(y_tr))
        neg_cnt = len(y_tr) - pos_cnt

        if resume and os.path.exists(model_path):
            print(f"[{idx+1}/{len(targets)}] Resuming existing XGBoost model: {cid} ({cname})...")
            best_xgb = load_model_artifact(model_path)
            meta_path = f"{out_dir}/model_{cid}_metadata.json"
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            else:
                meta = {"best_hyperparameters": {}, "diagnostics": {}, "top_features_by_gain": [], "all_feature_importances_gain": {}}
        else:
            print(f"[{idx+1}/{len(targets)}] Tuning XGBoost for: {cid} ({cname}) | Pos: {pos_cnt:,} / Neg: {neg_cnt:,}...")
            best_xgb, best_config, meta = train_and_tune_single_xgb(
                X_train=train_split.X,
                y_train=y_tr,
                X_val=val_split.X,
                y_val=y_va,
                feature_names=train_split.feature_names,
                target_cid=cid,
                device=resolved_device,
                random_seed=42,
                n_jobs=args.n_jobs
            )
            save_model_artifact(best_xgb, model_path, metadata=meta)
            print(f"  -> Best Params: {meta['best_hyperparameters']} | Best Iter: {meta['best_iteration']} | Val AUPRC: {meta['diagnostics']['val_auprc']:.4f} in {time.time() - t_start:.2f}s")

        # Record predictions
        preds_val[:, idx] = best_xgb.predict_proba(val_split.X)[:, 1]
        preds_test[:, idx] = best_xgb.predict_proba(test_split.X)[:, 1]

        diagnostics_by_disease[cid] = meta
        importances_by_disease[cid] = meta.get("all_feature_importances_gain", {})
        tuning_summary[cid] = {
            "name": cname,
            "category": cat,
            "best_params": meta.get("best_hyperparameters", {}),
            "best_iteration": meta.get("best_iteration", 0),
            "early_stopped_sensibly": meta.get("early_stopped_sensibly", True),
            "val_auprc": meta.get("diagnostics", {}).get("val_auprc", 0.0),
            "train_val_gap": meta.get("diagnostics", {}).get("generalization_gap_auprc", 0.0)
        }

    total_time = time.time() - total_t0
    print(f"\nProcessed {len(targets)} XGBoost models in {total_time:.2f}s.")

    # 2. Evaluate Multi-Target Metrics using correct argument names
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

    # 3. Save JSON reports
    eval_json_path = f"{reports_dir}/phase9_xgb_evaluation.json"
    curves_json_path = f"{reports_dir}/phase9_xgb_learning_curves.json"
    feat_json_path = f"{reports_dir}/phase9_xgb_feature_importances.json"

    clean_summary = {str(k): v for k, v in tuning_summary.items()}
    with open(eval_json_path, "w", encoding="utf-8") as f:
        json.dump({"validation": val_report, "test": test_report, "tuning_summary": clean_summary}, f, indent=2)

    clean_diag = {str(k): v for k, v in diagnostics_by_disease.items()}
    with open(curves_json_path, "w", encoding="utf-8") as f:
        json.dump(clean_diag, f, indent=2)

    clean_feat = {str(k): v for k, v in importances_by_disease.items()}
    with open(feat_json_path, "w", encoding="utf-8") as f:
        json.dump(clean_feat, f, indent=2)

    print(f"Saved evaluation JSON: {eval_json_path}")
    print(f"Saved learning curves JSON: {curves_json_path}")
    print(f"Saved feature importances JSON: {feat_json_path}")

    # 4. Generate Markdown Evaluation Report
    md_eval_path = f"{reports_dir}/phase9_xgb_evaluation.md"
    v_m = val_report["macro_metrics"]
    t_m = test_report["macro_metrics"]
    t_rk = test_report.get("ranking_metrics", {})
    v_rk = val_report.get("ranking_metrics", {})

    with open(md_eval_path, "w", encoding="utf-8") as f:
        f.write("# Phase 9: Standalone XGBoost Base Model Evaluation Report\n\n")
        f.write("## 1. Executive Summary & Benchmark Comparison\n\n")
        f.write(f"- **Targets Modeled**: {len(targets)} chronic comorbidities\n")
        f.write(f"- **Predictor Features**: {train_split.n_features} active clinical features (0 network placeholders)\n")
        f.write(f"- **Compute Device**: {resolved_device.upper()}\n")
        f.write(f"- **Total Runtime**: {total_time:.2f} seconds\n\n")

        f.write("| Model Family | Split | Macro-AUPRC | Macro-AUROC | Precision@3 | Recall@3 | MAP@3 | Brier Score |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        f.write("| Prevalence Floor (Phase 6) | Test | 0.0025 | 0.5000 | 0.81% | 1.83% | 0.0163 | 0.0028 |\n")
        f.write("| Tuned Logistic Regression (Phase 7) | Test | 0.0502 | 0.8676 | 20.94% | 53.15% | 0.4007 | 0.0527 |\n")
        f.write("| Tuned Random Forest (Phase 8) | Test | 0.0739 | 0.8772 | 25.51% | 63.66% | 0.5315 | 0.0401 |\n")
        f.write(f"| **Tuned XGBoost (Phase 9)** | **Val** | **{v_m['macro_auprc']:.4f}** | **{v_m['macro_auroc']:.4f}** | **{v_rk.get('precision_at_3', 0.0)*100:.2f}%** | **{v_rk.get('recall_at_3', 0.0)*100:.2f}%** | **{v_rk.get('map_at_3', 0.0):.4f}** | **{v_m['macro_brier_score']:.4f}** |\n")
        f.write(f"| **Tuned XGBoost (Phase 9)** | **Test** | **{t_m['macro_auprc']:.4f}** | **{t_m['macro_auroc']:.4f}** | **{t_rk.get('precision_at_3', 0.0)*100:.2f}%** | **{t_rk.get('recall_at_3', 0.0)*100:.2f}%** | **{t_rk.get('map_at_3', 0.0):.4f}** | **{t_m['macro_brier_score']:.4f}** |\n\n")

        f.write("## 2. Per-Disease Performance Table (Held-Out Prospective Test Split)\n\n")
        f.write("| Concept ID | Disease Name | Category | Test Prevalence | AUPRC | Lift vs Prev | AUROC | Best Params | Best Iter |\n")
        f.write("|---|---|---|---|---|---|---|---|---|\n")
        for cid in targets:
            cid_str = str(cid)
            d = test_report["per_target"].get(cid_str, {})
            diag = tuning_summary.get(cid, {})
            cname, cat, _ = CONDITION_METADATA.get(cid, (f"Disease {cid}", "General", True))
            p = d.get("prevalence", 0.0)
            auprc = d.get("auprc", 0.0)
            lift = (auprc / p) if p > 0 else 0.0
            params = diag.get("best_params", {})
            params_str = f"d={params.get('max_depth', '-')}, lr={params.get('learning_rate', '-')}, l2={params.get('reg_lambda', '-')}"
            f.write(f"| `{cid}` | **{cname}** | {cat} | {p*100:.3f}% | **{auprc:.4f}** | {lift:.1f}x | {d.get('auroc', 0.0):.4f} | `{params_str}` | {diag.get('best_iteration', '-')} |\n")

    # 5. Generate Learning Curves & Early Stopping Markdown Report
    md_curves_path = f"{reports_dir}/phase9_xgb_learning_curves.md"
    with open(md_curves_path, "w", encoding="utf-8") as f:
        f.write("# Phase 9: XGBoost Early Stopping & Learning Curve Diagnostics\n\n")
        f.write("## 1. Early Stopping Audit Overview\n\n")
        f.write("Early stopping was configured with `early_stopping_rounds=15` tracking validation logloss across 200 trees.\n\n")
        f.write("| Concept ID | Disease Name | Best Iteration | Train AUPRC | Val AUPRC | Gen Gap (AUPRC) |\n")
        f.write("|---|---|---|---|---|---|\n")
        for cid, diag in diagnostics_by_disease.items():
            cname = diag.get("target_name", f"CID {cid}")
            b_iter = diag.get("best_iteration", 0)
            d_dict = diag.get("diagnostics", {})
            f.write(f"| `{cid}` | **{cname}** | {b_iter} | {d_dict.get('train_auprc', 0.0):.4f} | {d_dict.get('val_auprc', 0.0):.4f} | {d_dict.get('generalization_gap_auprc', 0.0):+.4f} |\n")

    # 6. Generate Feature Importances Markdown Report
    md_feat_path = f"{reports_dir}/phase9_xgb_feature_importances.md"
    with open(md_feat_path, "w", encoding="utf-8") as f:
        f.write("# Phase 9: XGBoost Feature Importance Audit (Gain, Weight, Cover)\n\n")
        f.write("## 1. Top Clinical Predictors by Gain for Representative Benchmark Diseases\n\n")
        benchmark_cids = [316866, 201826, 317576, 440383, 197320, 432867]
        for cid in benchmark_cids:
            if cid in diagnostics_by_disease:
                diag = diagnostics_by_disease[cid]
                f.write(f"### {diag.get('target_name', f'CID {cid}')} (OMOP `{cid}`)\n\n")
                f.write("| Rank | Feature Name | Gain (Relative Information) | Weight (Splits) | Cover (Hessian Support) |\n")
                f.write("|---|---|---|---|---|\n")
                for r_idx, feat in enumerate(diag.get("top_features_by_gain", [])[:5]):
                    f.write(f"| {r_idx+1} | `{feat['feature']}` | **{feat['gain']:.4f}** | {feat['weight']} | {feat['cover']:.2f} |\n")
                f.write("\n")

    print(f"Saved Markdown reports:\n  - {md_eval_path}\n  - {md_curves_path}\n  - {md_feat_path}")

    print("\n" + "=" * 80)
    print("PHASE 9 COMPLETED SUCCESSFULLY.")
    print(f"  [Validation] Macro-AUPRC: {v_m['macro_auprc']:.4f} | AUROC: {v_m['macro_auroc']:.4f}")
    print(f"  [Test]       Macro-AUPRC: {t_m['macro_auprc']:.4f} | AUROC: {t_m['macro_auroc']:.4f}")
    print(f"  [Test]       Precision@3: {t_rk.get('precision_at_3', 0.0)*100:.2f}% | Recall@3: {t_rk.get('recall_at_3', 0.0)*100:.2f}% | MAP@3: {t_rk.get('map_at_3', 0.0):.4f}")
    print("=" * 80)


if __name__ == "__main__":
    main()
