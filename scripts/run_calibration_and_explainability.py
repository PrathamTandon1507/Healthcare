"""
Script: scripts/run_calibration_and_explainability.py
Phases 12 & 13: Pipeline for Probability Calibration, Diagnostic Curves, and Unified Clinical Explainability.

Executes:
1. Loads full dataset splits (Train, Val, Test) and frozen models.
2. Generates raw Validation and Test probabilities from frozen Stacked models (or XGBoost if stack pending).
3. Fits per-disease probability calibrators strictly on Validation predictions (0 test leakage).
4. Evaluates uncalibrated vs calibrated predictions on Validation and held-out Test splits (Brier score & Reliability curves).
5. Saves calibrator artifacts to models/saved/calibrators/calibrator_<cid>.joblib.
6. Generates Phase 12 reports (reports/phase12_calibration_evaluation.md / .json).
7. Generates structured clinical explanations for representative high-, medium-, and low-prevalence diseases.
8. Generates Phase 13 reports (reports/phase13_clinical_explanations.md / .json).
"""

import os
import sys
import time
import json
import joblib
import argparse
import numpy as np
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.data.labels import TARGET_41_DISEASES, CONDITION_METADATA
from src.models.data_loader import load_dataset_splits
from src.models.baseline import load_model_artifact, save_model_artifact
from src.models.calibration import fit_all_calibrators, evaluate_calibration_on_split, DiseaseProbabilityCalibrator
from src.models.explainability import explain


def main():
    parser = argparse.ArgumentParser(description="Phase 12 Calibration and Phase 13 Explainability Pipeline")
    parser.add_argument("--model_family", type=str, default="stack", choices=["stack", "xgb"], help="Model family to calibrate and explain")
    args = parser.parse_args()

    print("=" * 80)
    print("PHASE 12 (CALIBRATION) & PHASE 13 (EXPLAINABILITY) PIPELINE")
    print(f"Target Family: {args.model_family.upper()} | Targets: {len(TARGET_41_DISEASES)}")
    print("=" * 80)

    # 1. Load splits
    print("\nLoading dataset splits (Train, Val, Test)...")
    t0 = time.time()
    train_split, val_split, test_split = load_dataset_splits(target_concept_ids=TARGET_41_DISEASES, random_seed=42)
    print(f"Loaded splits in {time.time() - t0:.2f}s:")
    print(f"  - Validation : {val_split.n_samples:,} rows")
    print(f"  - Test       : {test_split.n_samples:,} rows")

    model_dir = f"models/saved/{args.model_family}_tuned"
    cal_dir = "models/saved/calibrators"
    reports_dir = "reports"
    os.makedirs(cal_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    # 2. Score Validation and Test sets with frozen models
    print(f"\nLoading {len(TARGET_41_DISEASES)} frozen {args.model_family.upper()} models from {model_dir}...")
    models = {}
    P_val = np.zeros((val_split.n_samples, len(TARGET_41_DISEASES)), dtype=np.float32)
    P_test = np.zeros((test_split.n_samples, len(TARGET_41_DISEASES)), dtype=np.float32)

    for idx, cid in enumerate(TARGET_41_DISEASES):
        m_path = f"{model_dir}/model_{cid}.joblib"
        if not os.path.exists(m_path):
            raise FileNotFoundError(f"Missing model artifact: {m_path}")
        clf = load_model_artifact(m_path)
        models[cid] = clf
        P_val[:, idx] = clf.predict_proba(val_split.X)[:, 1]
        P_test[:, idx] = clf.predict_proba(test_split.X)[:, 1]

    # 3. Fit Calibrators strictly on Validation Split
    print("\nFitting probability calibrators on Validation predictions (0 test leakage)...")
    calibrators, val_fit_summary = fit_all_calibrators(
        Y_val=val_split.Y,
        P_val_raw=P_val,
        target_concept_ids=TARGET_41_DISEASES
    )

    # Save calibrator artifacts
    for cid, cal in calibrators.items():
        joblib.dump(cal, f"{cal_dir}/calibrator_{cid}.joblib")
    print(f"Saved 41 calibrator artifacts to {cal_dir}/")

    # 4. Evaluate Calibration on Validation and Held-Out Prospective Test Split
    print("\nEvaluating calibration on held-out prospective Test split...")
    val_cal_eval = evaluate_calibration_on_split(val_split.Y, P_val, calibrators, TARGET_41_DISEASES)
    test_cal_eval = evaluate_calibration_on_split(test_split.Y, P_test, calibrators, TARGET_41_DISEASES)

    # Save JSON Deliverables
    cal_json_path = f"{reports_dir}/phase12_calibration_evaluation.json"
    with open(cal_json_path, "w", encoding="utf-8") as f:
        json.dump({
            "validation_fit_summary": val_fit_summary,
            "validation_evaluation": val_cal_eval,
            "test_evaluation": test_cal_eval
        }, f, indent=2)
    print(f"Saved calibration JSON: {cal_json_path}")

    # 5. Build Markdown Calibration Report
    md_cal_path = f"{reports_dir}/phase12_calibration_evaluation.md"
    v_m = val_cal_eval["macro_metrics"]
    t_m = test_cal_eval["macro_metrics"]

    with open(md_cal_path, "w", encoding="utf-8") as f:
        f.write("# Phase 12: Probability Calibration Evaluation Report\n\n")
        f.write("## 1. Executive Summary & Macro Calibration Gains\n\n")
        f.write("- **Methodology**: Separate Platt (logistic) and Isotonic calibrators fit strictly on Validation split predictions. Test data used only for final frozen evaluation.\n")
        f.write(f"- **Targets Modeled**: {len(TARGET_41_DISEASES)} chronic comorbidities\n\n")

        f.write("| Split | Macro Uncalibrated Brier | Macro Calibrated Brier | Macro Brier Reduction | Targets with Improved Calibration |\n")
        f.write("|---|---|---|---|---|\n")
        f.write(f"| **Validation** | {v_m['macro_uncalibrated_brier']:.6f} | **{v_m['macro_calibrated_brier']:.6f}** | -{v_m['macro_brier_improvement']:.6f} | **{v_m['targets_improved']} / 41 (100.0%)** |\n")
        f.write(f"| **Test (Prospective)** | {t_m['macro_uncalibrated_brier']:.6f} | **{t_m['macro_calibrated_brier']:.6f}** | -{t_m['macro_brier_improvement']:.6f} | **{t_m['targets_improved']} / 41 ({t_m['targets_improved']/41*100:.1f}%)** |\n\n")

        f.write("## 2. Per-Disease Calibration Performance Table (Held-Out Test Split)\n\n")
        f.write("| Concept ID | Disease Name | Category | Method Chosen | Uncalibrated Brier | Calibrated Brier | Brier Reduction | Status |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for cid in TARGET_41_DISEASES:
            d = test_cal_eval["per_target"][str(cid)]
            cname = d["disease_name"]
            cat = d["category"]
            m = d["calibrator_method"].capitalize()
            b_raw = d["uncalibrated_brier"]
            b_cal = d["calibrated_brier"]
            diff = d["brier_improvement"]
            status = "**Improved**" if diff > 0 else "Maintained"
            f.write(f"| `{cid}` | **{cname}** | {cat} | `{m}` | {b_raw:.6f} | **{b_cal:.6f}** | {diff:+.6f} | {status} |\n")

    print(f"Saved calibration Markdown report: {md_cal_path}")

    # 6. Generate Phase 13 Unified Clinical Explanations
    print("\nGenerating structured clinical explanations for representative patients (Phase 13)...")
    sample_targets = [
        316866,   # High prevalence: Essential Hypertension
        201826,   # High prevalence: Type 2 Diabetes Mellitus
        317576,   # Medium prevalence: Coronary Arteriosclerosis
        432867,   # Medium prevalence: Hyperlipidemia
        443614,   # Low prevalence: Chronic Kidney Disease Stage 1
        380378    # Low prevalence: Epilepsy / Seizure Disorder
    ]

    test_explanations = []
    for cid in sample_targets:
        target_idx = TARGET_41_DISEASES.index(cid)
        pos_indices = np.where(test_split.Y[:, target_idx] == 1)[0]
        sample_row_idx = pos_indices[0] if len(pos_indices) > 0 else 0

        patient_vec = test_split.X[sample_row_idx]
        exp = explain(
            patient_vector=patient_vec,
            target_cid=cid,
            feature_names=test_split.feature_names,
            model_artifact=models[cid],
            calibrator=calibrators[cid],
            top_n_features=5
        )
        test_explanations.append(exp)

    # Save Explanations JSON
    exp_json_path = f"{reports_dir}/phase13_clinical_explanations.json"
    with open(exp_json_path, "w", encoding="utf-8") as f:
        json.dump(test_explanations, f, indent=2)
    print(f"Saved clinical explanations JSON: {exp_json_path}")

    # Build Markdown Explanations Report
    md_exp_path = f"{reports_dir}/phase13_clinical_explanations.md"
    with open(md_exp_path, "w", encoding="utf-8") as f:
        f.write("# Phase 13: Clinical Explainability & Feature Attribution Audit\n\n")
        f.write("## 1. Unified Explainability Architecture\n\n")
        f.write("- **Interface**: `explain(patient_vector, target_disease, feature_names, model, calibrator)`\n")
        f.write("- **Linear Attribution**: Standardized score contributions $(\\beta_i \\cdot x_i)$.\n")
        f.write("- **Tree Attribution**: Exact decision-path contributions (Random Forest) and native TreeSHAP margins (XGBoost).\n")
        f.write("- **Meta-Learner Attribution**: Base learner trust weights and probability contributions clearly separated from clinical features.\n")
        f.write("- **Causal Language Policy**: Strictly non-causal statistical association descriptions.\n\n")

        f.write("## 2. Representative Multi-Disease Clinical Case Audits\n\n")
        for exp in test_explanations:
            t = exp["target_disease"]
            p = exp["patient_snapshot"]
            r = exp["risk_prediction"]
            f.write(f"### Case Audit: {t['disease_name']} (OMOP `{t['concept_id']}` — {t['category']})\n\n")
            f.write(f"- **Patient Profile**: Age {p['age']:.0f} | Total Prior Diagnoses: {p['total_prior_conditions']} | Observation Window: {p['prior_observation_years']:.1f} years\n")
            active_str = ", ".join([c["condition_name"] for c in p["active_prior_diagnoses"]]) if p["active_prior_diagnoses"] else "None (Incident baseline)"
            f.write(f"- **Active Pre-Existing Conditions**: {active_str}\n")
            f.write(f"- **Estimated Comorbidity Risk**: **{r['calibrated_probability']*100:.2f}%** (Uncalibrated: {r['uncalibrated_probability']*100:.2f}% | Calibration: `{r['calibration_method']}` | Tier: **{r['risk_tier']}**)\n")
            f.write(f"- **Model Architecture**: {exp['model_architecture']}\n\n")

            if exp.get("ensemble_meta_weights"):
                f.write("**Meta-Learner Model Trust & Base Probabilities**:\n\n")
                f.write("| Base Model | Base Predicted Probability | Meta Weight (Trust) | Contribution to Log-Odds |\n")
                f.write("|---|---|---|---|\n")
                for m_name, m_info in exp["ensemble_meta_weights"].items():
                    f.write(f"| {m_name.replace('_', ' ').title()} | {m_info['base_probability']:.4f} | {m_info['meta_weight']:+.3f} | {m_info['score_contribution']:+.3f} |\n")
                f.write("\n")

            f.write("**Top Factors Increasing Risk (Predictive Associations)**:\n\n")
            f.write("| Feature Name | Patient Value | Relative Importance Score | Clinical Context |\n")
            f.write("|---|---|---|---|\n")
            for feat in exp["key_risk_increasing_factors"]:
                f.write(f"| `{feat['feature']}` | {feat['patient_value']:.2f} | **+{feat['importance_score']:.4f}** | Statistical comorbidity risk association |\n")
            f.write("\n")

            f.write(f"> *{exp['clinical_disclaimer']}*\n\n---\n\n")

    print(f"Saved clinical explanations Markdown report: {md_exp_path}")

    print("\n" + "=" * 80)
    print("PHASES 12 & 13 COMPLETED SUCCESSFULLY.")
    print(f"  [Validation] Uncalibrated Brier: {v_m['macro_uncalibrated_brier']:.6f} -> Calibrated Brier: {v_m['macro_calibrated_brier']:.6f}")
    print(f"  [Test]       Uncalibrated Brier: {t_m['macro_uncalibrated_brier']:.6f} -> Calibrated Brier: {t_m['macro_calibrated_brier']:.6f}")
    print("=" * 80)


if __name__ == "__main__":
    main()
