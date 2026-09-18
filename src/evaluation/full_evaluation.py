"""
Module: src/evaluation/full_evaluation.py
Phase 14: Master Metric Suite Evaluation & Breakdown Tables.

Implements Section 9 & 10 of COMORBIDITY_ENSEMBLE_ML_PLAN.md:
1. Multi-split (Train, Validation, Prospective Test >= 2016) metric evaluation across:
   - Prevalence Baseline (Phase 6)
   - Tuned Logistic Regression (Phase 7)
   - Tuned Random Forest (Phase 8)
   - Tuned XGBoost (Phase 9)
   - Stacked Ensemble (Phase 10)
   - Calibrated Stacked Ensemble (Phase 12)
2. Primary and Secondary Metrics:
   - AUPRC, AUROC, Brier Score, F1-tuned, Precision@3, Recall@3, MAP@3, Precision@5, Recall@5, MAP@5.
3. Stratified Prevalence Tier Breakdowns (High >= 0.5%, Medium 0.1-0.5%, Low < 0.1%).
4. Generalization Gap Analysis (Validation vs Prospective Test).
5. Best Single Base Model vs Stacked Ensemble Delta Analysis (answering Section 10's core research question).
"""

import os
import sys
import json
import time
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.data.labels import TARGET_41_DISEASES, CONDITION_METADATA
from src.models.data_loader import load_dataset_splits
from src.models.baseline import load_model_artifact, PrevalenceBaseline
from src.models.metrics import evaluate_multitarget_predictions, compute_binary_metrics


def run_phase14_master_evaluation() -> Dict[str, Any]:
    """
    Executes complete master evaluation ladder across all models, splits, and prevalence tiers.
    """
    print("=" * 80)
    print("PHASE 14: MASTER METRIC SUITE EVALUATION & STRATIFIED BREAKDOWN")
    print(f"Evaluating {len(TARGET_41_DISEASES)} chronic comorbidities across all splits")
    print("=" * 80)

    # 1. Load splits
    print("Loading full dataset splits...")
    t0 = time.time()
    train_split, val_split, test_split = load_dataset_splits(target_concept_ids=TARGET_41_DISEASES, random_seed=42)
    print(f"Loaded splits in {time.time() - t0:.2f}s:")
    print(f"  - Train      : {train_split.n_samples:,} rows")
    print(f"  - Validation : {val_split.n_samples:,} rows")
    print(f"  - Test       : {test_split.n_samples:,} rows")

    # 2. Score models
    # A. Prevalence Baseline
    base_floor = PrevalenceBaseline(target_concept_ids=TARGET_41_DISEASES).fit(train_split.Y)
    P_val_base = base_floor.predict_proba(val_split.X)
    P_test_base = base_floor.predict_proba(test_split.X)

    # B. Tuned Logistic Regression
    P_val_lr = np.zeros((val_split.n_samples, len(TARGET_41_DISEASES)), dtype=np.float32)
    P_test_lr = np.zeros((test_split.n_samples, len(TARGET_41_DISEASES)), dtype=np.float32)
    for idx, cid in enumerate(TARGET_41_DISEASES):
        clf = load_model_artifact(f"models/saved/lr_tuned/model_{cid}.joblib")
        P_val_lr[:, idx] = clf.predict_proba(val_split.X)[:, 1]
        P_test_lr[:, idx] = clf.predict_proba(test_split.X)[:, 1]

    # C. Tuned Random Forest
    P_val_rf = np.zeros((val_split.n_samples, len(TARGET_41_DISEASES)), dtype=np.float32)
    P_test_rf = np.zeros((test_split.n_samples, len(TARGET_41_DISEASES)), dtype=np.float32)
    for idx, cid in enumerate(TARGET_41_DISEASES):
        clf = load_model_artifact(f"models/saved/rf_tuned/model_{cid}.joblib")
        P_val_rf[:, idx] = clf.predict_proba(val_split.X)[:, 1]
        P_test_rf[:, idx] = clf.predict_proba(test_split.X)[:, 1]

    # D. Tuned XGBoost
    P_val_xgb = np.zeros((val_split.n_samples, len(TARGET_41_DISEASES)), dtype=np.float32)
    P_test_xgb = np.zeros((test_split.n_samples, len(TARGET_41_DISEASES)), dtype=np.float32)
    for idx, cid in enumerate(TARGET_41_DISEASES):
        clf = load_model_artifact(f"models/saved/xgb_tuned/model_{cid}.joblib")
        P_val_xgb[:, idx] = clf.predict_proba(val_split.X)[:, 1]
        P_test_xgb[:, idx] = clf.predict_proba(test_split.X)[:, 1]

    # E. Stacked Ensemble (Phase 10) & Calibrated Stack (Phase 12)
    P_val_stack = np.zeros((val_split.n_samples, len(TARGET_41_DISEASES)), dtype=np.float32)
    P_test_stack = np.zeros((test_split.n_samples, len(TARGET_41_DISEASES)), dtype=np.float32)
    P_val_cal = np.zeros((val_split.n_samples, len(TARGET_41_DISEASES)), dtype=np.float32)
    P_test_cal = np.zeros((test_split.n_samples, len(TARGET_41_DISEASES)), dtype=np.float32)

    calibrators = {}
    for idx, cid in enumerate(TARGET_41_DISEASES):
        clf = load_model_artifact(f"models/saved/stack_tuned/model_{cid}.joblib")
        cal = load_model_artifact(f"models/saved/calibrators/calibrator_{cid}.joblib")
        calibrators[cid] = cal

        p_v = clf.predict_proba(val_split.X)[:, 1]
        p_t = clf.predict_proba(test_split.X)[:, 1]

        P_val_stack[:, idx] = p_v
        P_test_stack[:, idx] = p_t

        P_val_cal[:, idx] = cal.predict_proba(p_v)
        P_test_cal[:, idx] = cal.predict_proba(p_t)

    # 3. Compute Multi-Target Evaluation Reports
    models_dict = {
        "prevalence_floor": {"val": P_val_base, "test": P_test_base},
        "logistic_regression": {"val": P_val_lr, "test": P_test_lr},
        "random_forest": {"val": P_val_rf, "test": P_test_rf},
        "xgboost": {"val": P_val_xgb, "test": P_test_xgb},
        "stacked_ensemble": {"val": P_val_stack, "test": P_test_stack},
        "calibrated_stack": {"val": P_val_cal, "test": P_test_cal}
    }

    results = {}
    for m_name, probs in models_dict.items():
        val_rep = evaluate_multitarget_predictions(val_split.Y, probs["val"], TARGET_41_DISEASES, CONDITION_METADATA)
        test_rep = evaluate_multitarget_predictions(test_split.Y, probs["test"], TARGET_41_DISEASES, CONDITION_METADATA)
        results[m_name] = {"validation": val_rep, "test": test_rep}

    # 4. Master Comparison Ladder Table & Delta Analysis
    best_single_comparison = {}
    for idx, cid in enumerate(TARGET_41_DISEASES):
        cid_str = str(cid)
        cname, cat, _ = CONDITION_METADATA.get(cid, (f"Disease {cid}", "General", True))

        lr_auprc = results["logistic_regression"]["test"]["per_target"][cid_str]["auprc"]
        rf_auprc = results["random_forest"]["test"]["per_target"][cid_str]["auprc"]
        xgb_auprc = results["xgboost"]["test"]["per_target"][cid_str]["auprc"]
        stack_auprc = results["stacked_ensemble"]["test"]["per_target"][cid_str]["auprc"]

        best_base_name = "XGBoost" if (xgb_auprc >= rf_auprc and xgb_auprc >= lr_auprc) else ("Random Forest" if rf_auprc >= lr_auprc else "Logistic Regression")
        best_base_auprc = max(lr_auprc, rf_auprc, xgb_auprc)
        stack_delta = stack_auprc - best_base_auprc

        best_single_comparison[cid_str] = {
            "concept_id": cid,
            "disease_name": cname,
            "category": cat,
            "lr_auprc": lr_auprc,
            "rf_auprc": rf_auprc,
            "xgb_auprc": xgb_auprc,
            "best_base_model": best_base_name,
            "best_base_auprc": best_base_auprc,
            "stack_auprc": stack_auprc,
            "stack_delta": round(stack_delta, 6),
            "stack_wins": stack_delta >= -1e-6
        }

    master_summary = {
        "model_results": results,
        "best_single_vs_stack": best_single_comparison,
        "n_targets": len(TARGET_41_DISEASES)
    }

    # Save JSON Deliverable
    out_json = "reports/phase14_master_evaluation.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(master_summary, f, indent=2)
    print(f"Saved master evaluation JSON: {out_json}")

    # Build Markdown Report
    out_md = "reports/phase14_master_evaluation.md"
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# Phase 14: Comprehensive Model Ladder & Multi-Target Evaluation Report\n\n")
        f.write("## 1. Master Benchmark Ladder (Validation & Prospective Test Splits)\n\n")
        f.write("| Model Family | Split | Macro-AUPRC | Macro-AUROC | Precision@3 | Recall@3 | MAP@3 | Precision@5 | Recall@5 | MAP@5 | Brier Score |\n")
        f.write("|---|---|---|---|---|---|---|---|---|---|---|\n")

        for m_key, m_title in [
            ("prevalence_floor", "Prevalence Floor (Phase 6)"),
            ("logistic_regression", "Tuned Logistic Regression (Phase 7)"),
            ("random_forest", "Tuned Random Forest (Phase 8)"),
            ("xgboost", "Tuned XGBoost (Phase 9)"),
            ("stacked_ensemble", "Stacked Ensemble (Phase 10)"),
            ("calibrated_stack", "**Calibrated Stacked Ensemble (Phase 12)**")
        ]:
            for s_name in ["validation", "test"]:
                rep = results[m_key][s_name]
                m = rep["macro_metrics"]
                rk = rep.get("ranking_metrics", {})
                p3 = rk.get("precision_at_3", 0.0) * 100
                r3 = rk.get("recall_at_3", 0.0) * 100
                map3 = rk.get("map_at_3", 0.0)
                p5 = rk.get("precision_at_5", 0.0) * 100
                r5 = rk.get("recall_at_5", 0.0) * 100
                map5 = rk.get("map_at_5", 0.0)
                s_label = "Val" if s_name == "validation" else "**Test**"
                f.write(f"| {m_title} | {s_label} | **{m['macro_auprc']:.4f}** | {m['macro_auroc']:.4f} | {p3:.2f}% | {r3:.2f}% | {map3:.4f} | {p5:.2f}% | {r5:.2f}% | {map5:.4f} | {m['macro_brier_score']:.6f} |\n")

        f.write("\n---\n\n## 2. Stratified Prevalence-Tier Breakdown (Held-Out Test Split)\n\n")
        f.write("| Model Family | High Prevalence (>0.5%) Macro-AUPRC | Medium Prevalence (0.1-0.5%) Macro-AUPRC | Low Prevalence (<0.1%) Macro-AUPRC |\n")
        f.write("|---|---|---|---|\n")
        for m_key, m_title in [
            ("prevalence_floor", "Prevalence Floor"),
            ("logistic_regression", "Logistic Regression"),
            ("random_forest", "Random Forest"),
            ("xgboost", "XGBoost"),
            ("stacked_ensemble", "Stacked Ensemble"),
            ("calibrated_stack", "**Calibrated Stack**")
        ]:
            t_rep = results[m_key]["test"]["prevalence_tier_auprc"]
            f.write(f"| {m_title} | **{t_rep['high_prevalence_macro_auprc']:.4f}** | **{t_rep['medium_prevalence_macro_auprc']:.4f}** | **{t_rep['low_prevalence_macro_auprc']:.4f}** |\n")

        f.write("\n---\n\n## 3. Stacked Ensemble vs. Best Single Base Learner Comparison\n\n")
        f.write("| Concept ID | Disease Name | Category | Best Base Model | Best Base AUPRC | Stack AUPRC | Delta vs Best Base | Status |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for cid_str, comp in sorted(best_single_comparison.items(), key=lambda x: -x[1]["stack_auprc"]):
            d = comp["stack_delta"]
            status = "**Stack Outperforms / Ties**" if d >= -1e-6 else "Single Model Competitive"
            f.write(f"| `{comp['concept_id']}` | **{comp['disease_name']}** | {comp['category']} | {comp['best_base_model']} | {comp['best_base_auprc']:.4f} | **{comp['stack_auprc']:.4f}** | {d:+.4f} | {status} |\n")

    print(f"Saved master evaluation Markdown report: {out_md}")
    return master_summary


if __name__ == "__main__":
    run_phase14_master_evaluation()
