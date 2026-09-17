"""
Script: scripts/train_baseline.py
Multi-stage Training and Evaluation Runner for ML Baseline & Base Learner Models.

Stages:
1. smoke_test  : Runs end-to-end smoke test on small subset (5k samples, 2 diseases) across all 4 models.
2. prevalence  : Computes and evaluates empirical prevalence baseline across all 41 targets.
3. lr          : Trains L2-regularized Logistic Regression models across all 41 targets.
4. rf          : Trains Random Forest models across all 41 targets.
5. xgb         : Trains XGBoost models with GPU CUDA acceleration (or CPU fallback) across all 41 targets.
6. evaluate    : Generates unified comparison report across all trained models against prevalence baseline.

Supports:
- Independent execution per stage.
- Resume capability (--resume) skipping already saved model artifacts.
- Single target execution (--target_cid <concept_id>).
- Automatic GPU CUDA detection with seamless CPU fallback.
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.data.labels import TARGET_41_DISEASES, CONDITION_METADATA
from src.features.pipeline import get_baseline_feature_columns
from src.models.data_loader import load_dataset_splits, DatasetSplit
from src.models.baseline import (
    PrevalenceBaseline,
    build_base_classifier,
    detect_xgboost_device,
    save_model_artifact,
    load_model_artifact
)
from src.models.metrics import (
    compute_binary_metrics,
    evaluate_multitarget_predictions,
    compute_ranking_metrics_at_k
)


def run_smoke_test(device: str = "auto"):
    """
    Executes a fast smoke test on 5,000 samples and 2 representative targets
    (Hypertension 316866 and Hyperlipidemia 432867) across all 4 model architectures.
    """
    print("=" * 80)
    print("RUNNING PHASE 6 PIPELINE SMOKE TEST (5,000 samples, 2 test targets)")
    print("=" * 80)

    test_targets = [316866, 432867]  # Hypertension, Hyperlipidemia
    resolved_device = detect_xgboost_device(preferred_device=device)
    print(f"XGBoost compute device resolved to: {resolved_device.upper()}")

    print("Loading 5,000 sample split subsets...")
    train_split, val_split, test_split = load_dataset_splits(
        target_concept_ids=test_targets,
        max_samples_per_split=5000,
        random_seed=42
    )

    print(f"Loaded splits successfully: Train={train_split.n_samples} rows, Val={val_split.n_samples} rows, Test={test_split.n_samples} rows, Features={train_split.n_features}")
    assert train_split.n_features == 81, f"Expected 81 active ML features, got {train_split.n_features}"

    models_to_test = ["prevalence", "lr", "rf", "xgb"]
    smoke_results = {}

    for m_type in models_to_test:
        t0 = time.time()
        print(f"\n--- Testing Model Architecture: {m_type.upper()} ---")
        
        preds_val = np.zeros((val_split.n_samples, len(test_targets)), dtype=np.float32)
        preds_test = np.zeros((test_split.n_samples, len(test_targets)), dtype=np.float32)

        if m_type == "prevalence":
            baseline = PrevalenceBaseline(target_concept_ids=test_targets)
            baseline.fit(train_split.Y)
            preds_val = baseline.predict_proba(val_split.X)
            preds_test = baseline.predict_proba(test_split.X)
        else:
            for idx, cid in enumerate(test_targets):
                y_tr = train_split.get_target_vector(cid)
                pos_cnt = int(np.sum(y_tr))
                neg_cnt = len(y_tr) - pos_cnt

                clf = build_base_classifier(
                    model_type=m_type,
                    target_cid=cid,
                    pos_count=pos_cnt,
                    neg_count=neg_cnt,
                    random_seed=42,
                    device=device,
                    n_jobs=4
                )
                clf.fit(train_split.X, y_tr)
                
                # Test single model saving and loading
                smoke_save_path = f"models/saved/smoke_test/{m_type}_{cid}.joblib"
                save_model_artifact(clf, smoke_save_path, metadata={"model": m_type, "cid": cid})
                loaded_clf = load_model_artifact(smoke_save_path)

                preds_val[:, idx] = loaded_clf.predict_proba(val_split.X)[:, 1]
                preds_test[:, idx] = loaded_clf.predict_proba(test_split.X)[:, 1]

        # Evaluate on validation
        val_eval = evaluate_multitarget_predictions(val_split.Y, preds_val, test_targets, CONDITION_METADATA)
        test_eval = evaluate_multitarget_predictions(test_split.Y, preds_test, test_targets, CONDITION_METADATA)
        elapsed = time.time() - t0

        print(f"  [Val]  Macro-AUPRC: {val_eval['macro_metrics']['macro_auprc']:.4f} | AUROC: {val_eval['macro_metrics']['macro_auroc']:.4f} | Brier: {val_eval['macro_metrics']['macro_brier_score']:.4f}")
        print(f"  [Test] Macro-AUPRC: {test_eval['macro_metrics']['macro_auprc']:.4f} | AUROC: {test_eval['macro_metrics']['macro_auroc']:.4f} | Brier: {test_eval['macro_metrics']['macro_brier_score']:.4f}")
        print(f"  Time: {elapsed:.2f}s")

        smoke_results[m_type] = {
            "val_macro_auprc": val_eval["macro_metrics"]["macro_auprc"],
            "test_macro_auprc": test_eval["macro_metrics"]["macro_auprc"],
            "elapsed_seconds": round(elapsed, 2)
        }

    print("\n" + "=" * 80)
    print("SMOKE TEST SUMMARY RESULTS:")
    for m_type, res in smoke_results.items():
        print(f"  - {m_type.upper():<12}: Val AUPRC = {res['val_macro_auprc']:.4f} | Test AUPRC = {res['test_macro_auprc']:.4f} | ({res['elapsed_seconds']}s)")
    print("=" * 80)
    print("SMOKE TEST PASSED SUCCESSFULLY. ALL PIPELINES ARE READY FOR FULL TRAINING.")


def train_model_stage(
    stage: str,
    target_cids: Optional[List[int]] = None,
    device: str = "auto",
    resume: bool = True,
    n_jobs: int = 4
):
    """
    Executes full training for a specified model stage ('prevalence', 'lr', 'rf', 'xgb').
    """
    if target_cids is None:
        target_cids = TARGET_41_DISEASES

    print("=" * 80)
    print(f"STARTING TRAINING STAGE: {stage.upper()} ({len(target_cids)} target diseases)")
    print("=" * 80)

    # 1. Load full dataset splits
    print("Loading full Inpatient/ED feature matrix and splits...")
    t0_load = time.time()
    train_split, val_split, test_split = load_dataset_splits(
        target_concept_ids=target_cids,
        random_seed=42
    )
    print(f"Loaded full dataset in {time.time() - t0_load:.2f}s:")
    print(f"  - Train: {train_split.n_samples:,} rows")
    print(f"  - Val  : {val_split.n_samples:,} rows")
    print(f"  - Test : {test_split.n_samples:,} rows")
    print(f"  - Features: {train_split.n_features} clinical predictors (network placeholders excluded)")

    out_dir = f"models/saved/{stage}"
    metrics_dir = "reports/metrics"
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(metrics_dir, exist_ok=True)

    preds_val = np.zeros((val_split.n_samples, len(target_cids)), dtype=np.float32)
    preds_test = np.zeros((test_split.n_samples, len(target_cids)), dtype=np.float32)

    # Stage: Prevalence Baseline
    if stage == "prevalence":
        baseline = PrevalenceBaseline(target_concept_ids=target_cids)
        baseline.fit(train_split.Y)
        save_model_artifact(baseline, f"{out_dir}/prevalence_baseline.joblib")
        preds_val = baseline.predict_proba(val_split.X)
        preds_test = baseline.predict_proba(test_split.X)

    # Stage: LR / RF / XGB Base Learners
    else:
        resolved_device = detect_xgboost_device(preferred_device=device) if stage == "xgb" else "cpu"
        print(f"Device configuration for {stage.upper()}: {resolved_device.upper()} (n_jobs={n_jobs})")

        total_t0 = time.time()
        for idx, cid in enumerate(target_cids):
            cname, cat, _ = CONDITION_METADATA.get(cid, (f"Disease {cid}", "General", True))
            model_path = f"{out_dir}/model_{cid}.joblib"
            
            # Check if model already exists and resume flag is active
            if resume and os.path.exists(model_path):
                print(f"[{idx+1}/{len(target_cids)}] Resuming existing model: {cid} ({cname})...")
                clf = load_model_artifact(model_path)
            else:
                t_start = time.time()
                y_tr = train_split.get_target_vector(cid)
                pos_cnt = int(np.sum(y_tr))
                neg_cnt = len(y_tr) - pos_cnt

                print(f"[{idx+1}/{len(target_cids)}] Training {stage.upper()} for: {cid} ({cname}) | Pos: {pos_cnt:,} / Neg: {neg_cnt:,}...")
                
                clf = build_base_classifier(
                    model_type=stage,
                    target_cid=cid,
                    pos_count=pos_cnt,
                    neg_count=neg_cnt,
                    random_seed=42,
                    device=resolved_device,
                    n_jobs=n_jobs
                )
                clf.fit(train_split.X, y_tr)
                
                save_model_artifact(
                    model=clf,
                    filepath=model_path,
                    metadata={
                        "model_type": stage,
                        "concept_id": cid,
                        "clinical_name": cname,
                        "pos_count": pos_cnt,
                        "neg_count": neg_cnt,
                        "trained_samples": len(y_tr),
                        "device": resolved_device
                    }
                )
                print(f"     Saved artifact to {model_path} ({time.time() - t_start:.2f}s)")

            # Generate validation and test predictions
            preds_val[:, idx] = clf.predict_proba(val_split.X)[:, 1]
            preds_test[:, idx] = clf.predict_proba(test_split.X)[:, 1]

        print(f"\nCompleted training for all {len(target_cids)} targets in {time.time() - total_t0:.2f}s")

    # Evaluate multi-target performance
    val_eval = evaluate_multitarget_predictions(val_split.Y, preds_val, target_cids, CONDITION_METADATA)
    test_eval = evaluate_multitarget_predictions(test_split.Y, preds_test, target_cids, CONDITION_METADATA)

    # Save metrics
    metrics_payload = {
        "model_stage": stage,
        "n_targets": len(target_cids),
        "validation_metrics": val_eval,
        "test_metrics": test_eval
    }
    json_path = f"{metrics_dir}/{stage}_metrics.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)
    print(f"\nSaved evaluation metrics to {json_path}")

    # Display headline results
    print("\n" + "=" * 80)
    print(f"{stage.upper()} HEADLINE METRICS:")
    print(f"  [Validation] Macro-AUPRC: {val_eval['macro_metrics']['macro_auprc']:.4f} | AUROC: {val_eval['macro_metrics']['macro_auroc']:.4f} | Brier: {val_eval['macro_metrics']['macro_brier_score']:.4f}")
    print(f"  [Test]       Macro-AUPRC: {test_eval['macro_metrics']['macro_auprc']:.4f} | AUROC: {test_eval['macro_metrics']['macro_auroc']:.4f} | Brier: {test_eval['macro_metrics']['macro_brier_score']:.4f}")
    print(f"  [Test Top-K] Precision@3: {test_eval['ranking_metrics'].get('precision_at_3', 0.0):.4f} | Recall@3: {test_eval['ranking_metrics'].get('recall_at_3', 0.0):.4f} | MAP@3: {test_eval['ranking_metrics'].get('map_at_3', 0.0):.4f}")
    print("=" * 80)


def generate_comparative_evaluation_report():
    """
    Aggregates metrics across all available model stages and generates a comprehensive Markdown report.
    """
    metrics_dir = "reports/metrics"
    stages = ["prevalence", "lr", "rf", "xgb"]
    loaded_results = {}

    for s in stages:
        path = f"{metrics_dir}/{s}_metrics.json"
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                loaded_results[s] = json.load(f)

    if not loaded_results:
        print("No evaluation metric files found to compare. Run training stages first.")
        return

    report_path = "reports/baseline_models_evaluation.md"
    md = []
    md.append("# Baseline Models Evaluation & Benchmark Report\n")
    md.append("**Models Evaluated**: " + ", ".join([s.upper() for s in loaded_results.keys()]) + "  \n")
    md.append("**Target Diseases**: K = 41 Curated Chronic Comorbidity Targets  \n")
    md.append("**Features**: 81 Active Clinical Predictors (Excluding Network Placeholders)  \n\n")

    md.append("## 1. Macro Model Benchmark Comparison\n\n")
    md.append("| Model Architecture | Val Macro-AUPRC | Val Macro-AUROC | Val Brier | Test Macro-AUPRC | Test Macro-AUROC | Test Brier | Test P@3 | Test R@3 | Test MAP@3 |\n")
    md.append("|---|---|---|---|---|---|---|---|---|---|\n")

    for s, data in loaded_results.items():
        v = data["validation_metrics"]["macro_metrics"]
        t = data["test_metrics"]["macro_metrics"]
        rk = data["test_metrics"].get("ranking_metrics", {})
        md.append(f"| **{s.upper()}** | {v['macro_auprc']:.4f} | {v['macro_auroc']:.4f} | {v['macro_brier_score']:.4f} | **{t['macro_auprc']:.4f}** | {t['macro_auroc']:.4f} | {t['macro_brier_score']:.4f} | {rk.get('precision_at_3', 0.0):.4f} | {rk.get('recall_at_3', 0.0):.4f} | {rk.get('map_at_3', 0.0):.4f} |\n")

    md.append("\n---\n\n## 2. Prevalence Tier Breakdown (Test Macro-AUPRC)\n\n")
    md.append("| Model Architecture | High Prevalence (>0.5%) | Medium Prevalence (0.1%-0.5%) | Low Prevalence (<0.1%) |\n")
    md.append("|---|---|---|---|\n")

    for s, data in loaded_results.items():
        tiers = data["test_metrics"].get("prevalence_tier_auprc", {})
        h = tiers.get("high_prevalence_macro_auprc", 0.0)
        m = tiers.get("medium_prevalence_macro_auprc", 0.0)
        l = tiers.get("low_prevalence_macro_auprc", 0.0)
        md.append(f"| **{s.upper()}** | {h:.4f} | {m:.4f} | {l:.4f} |\n")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("".join(md))
    print(f"Generated benchmark comparison report: {report_path}")


def main():
    parser = argparse.ArgumentParser(description="Phase 6 Multi-stage ML Baseline Runner")
    parser.add_argument("--stage", type=str, default="smoke_test", choices=["smoke_test", "prevalence", "lr", "rf", "xgb", "evaluate", "all"])
    parser.add_argument("--device", type=str, default="auto", choices=["auto", "cuda", "cpu"])
    parser.add_argument("--target_cid", type=int, default=None, help="Optional single concept ID to train")
    parser.add_argument("--no_resume", action="store_true", help="Force retrain of existing model files")
    parser.add_argument("--n_jobs", type=int, default=4, help="Number of CPU threads")

    args = parser.parse_args()
    resume = not args.no_resume
    targets = [args.target_cid] if args.target_cid is not None else TARGET_41_DISEASES

    if args.stage == "smoke_test":
        run_smoke_test(device=args.device)
    elif args.stage == "evaluate":
        generate_comparative_evaluation_report()
    elif args.stage == "all":
        for stg in ["prevalence", "lr", "rf", "xgb"]:
            train_model_stage(stage=stg, target_cids=targets, device=args.device, resume=resume, n_jobs=args.n_jobs)
        generate_comparative_evaluation_report()
    else:
        train_model_stage(stage=args.stage, target_cids=targets, device=args.device, resume=resume, n_jobs=args.n_jobs)


if __name__ == "__main__":
    main()
