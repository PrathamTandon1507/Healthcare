# Clinical Comorbidity Risk Engine & Clinical Decision Support System

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Test Suite](https://img.shields.io/badge/Tests-86%20Passed%20(100%25)-success.svg)](tests/)
[![Release Bundle](https://img.shields.io/badge/Release-v1.0.0%20Production-navy.svg)](models/release_v1/)
[![UI Framework](https://img.shields.io/badge/Streamlit-1.42+-FF4B4B.svg)](streamlit_app/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#license)

An end-to-end, clinically calibrated, multi-target predictive modeling platform for electronic health records (EHR). Built on OMOP Common Data Model (CDM) longitudinal patient histories, this system predicts **1-year incident onset risk across 41 distinct comorbidity targets** using leak-free temporal landmarking, stacked gradient boosted and tree ensembles, isotonic probability calibration, and unified TreeSHAP / tree-path explainability.

Includes a self-contained production release package (`models/release_v1`), unified single-call inference engine, and a **professional multi-page clinical decision support (CDS) web application**.

---

## Table of Contents
1. [Key Architecture & Capabilities](#key-architecture--capabilities)
2. [Clinical Modeling Pipeline](#clinical-modeling-pipeline)
3. [Benchmark Performance Summary](#benchmark-performance-summary)
4. [Project Structure](#project-structure)
5. [Quickstart & Installation](#quickstart--installation)
6. [Running the Clinical UI](#running-the-clinical-ui)
7. [Programmatic Inference API](#programmatic-inference-api)
8. [Test Suite & Quality Verification](#test-suite--quality-verification)
9. [Clinical Safety & Governance](#clinical-safety--governance)
10. [License](#license)

---

## Key Architecture & Capabilities

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                           Longitudinal EHR (OMOP CDM)                             │
│                  (Person, Visit Occurrence, Condition Occurrence)                 │
└────────────────────────────────────────┬──────────────────────────────────────────┘
                                         │
                                         ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                      Phase 1–5: Temporal Feature Engineering                      │
│     • Strict Landmarking (T_land)      • Zero-Future Leakage Boundary             │
│     • 58 Active Condition Flags        • Visit Frequency & Timing Dynamics        │
│     • Non-Linear Clinical Interactions • Patient-Level 5-Fold Splitting           │
└────────────────────────────────────────┬──────────────────────────────────────────┘
                                         │
                                         ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                   Phase 6–11: Multi-Target Ensemble Architecture                  │
│   ┌─────────────────────────┬───────────────────────────┬─────────────────────┐   │
│   │   ElasticNet Logistic   │   GPU-Accelerated XGBoost │ Random Forest Trees │   │
│   │    Regression (L1/L2)   │    (Hist / Early-Stop)    │ (OOB Diagnostics)   │   │
│   └────────────┬────────────┴─────────────┬─────────────┴──────────┬──────────┘   │
│                └──────────────────────────┼────────────────────────┘              │
│                                           ▼                                       │
│                        Out-of-Fold Constrained Meta-Learner                       │
│                               (Non-Negative Stacking)                             │
└────────────────────────────────────────┬──────────────────────────────────────────┘
                                         │
                                         ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                 Phase 12–13: Isotonic Calibration & Explainability                │
│     • Isotonic Regression Calibrators per Target (Brier Score Minimization)       │
│     • Unified TreeSHAP / Tree-Path Clinical Risk Drivers & Protective Factors     │
└────────────────────────────────────────┬──────────────────────────────────────────┘
                                         │
                                         ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                   Phase 16–18: Deployment & Clinical UI Platform                   │
│     • Self-Contained Release Bundle (models/release_v1) with SHA256 Integrity     │
│     • Unified Inference API (src/inference/predict.py)                            │
│     • Professional Multi-Page Streamlit CDS App (Light Theme / Medical Hierarchy)│
└───────────────────────────────────────────────────────────────────────────────────┘
```

- **41 Prevalent Clinical Targets**: Predicts 1-year incident onset for cardiovascular, metabolic, renal, pulmonary, neurological, musculoskeletal, and psychiatric disorders.
- **Zero Data Leakage Guarantee**: 8 rigorous automated audit tests verify strict patient-level partition isolation, temporal feature cutoffs, and preprocessor training bounds.
- **Isotonic Probability Calibration**: Raw model logits are mapped to true clinical risk probabilities, yielding well-calibrated reliability curves and ultra-low Brier scores.
- **Explainable Decision Support**: Decomposes patient risk into top positive drivers (elevating risk) and protective factors (lowering risk) with clinical explanations and odds-ratio context.
- **Production Artifact Architecture**: Standalone deployable release bundle (`models/release_v1`) containing frozen feature preprocessors, calibrated stack ensembles, optimal decision thresholds, and metadata manifests.

---

## Clinical Modeling Pipeline

| Phase | Module / Artifact | Description |
|---|---|---|
| **Phase 1–3** | `src/data/` | DuckDB-accelerated ETL, OMOP CDM schema ingestion, patient timeline construction. |
| **Phase 4–5** | `src/features/` | Landmark prediction matrix creation with 6-month observation window and existing disease masking. |
| **Phase 6** | `src/splits/` | Patient-level stratified 5-fold cross-validation with strict zero-overlap invariants. |
| **Phase 7** | `src/models/baseline.py` | Historical prevalence baseline establishment for benchmark calibration. |
| **Phase 8** | `src/models/rf.py` | Standalone tuned Random Forest classifiers with OOB diagnostics and Gini importances. |
| **Phase 9** | `src/models/xgb.py` | GPU/CPU accelerated XGBoost classifiers with early stopping and log-loss optimization. |
| **Phase 10–11** | `src/models/stacking.py` | Out-of-fold patient-partitioned stacking meta-learner with frozen hyperparameter configs. |
| **Phase 12–13** | `src/models/calibration.py`, `explainability.py` | Per-condition isotonic probability calibration and multi-method clinical explainability engine. |
| **Phase 14–15** | `src/evaluation/` | Master evaluation ladder across 41 conditions and feature ablation perturbation studies. |
| **Phase 16–17** | `src/packaging/`, `src/inference/` | Release bundle builder (`v1.0.0`) with SHA256 hashing and high-throughput unified inference pipeline. |
| **Phase 18** | `streamlit_app/` | 7-page clinical decision support UI with design system, archetype loader, and interactive charts. |
| **Phase 19–20** | `reports/` | Comprehensive technical report and 8-point automated leakage audit suite. |

---

## Benchmark Performance Summary

| Model Tier | Macro ROC-AUC | Micro ROC-AUC | Macro PR-AUC | Mean Brier Score | Calibration Quality |
|---|---|---|---|---|---|
| **Prevalence Baseline** | 0.5000 | 0.5000 | 0.0382 | 0.0368 | Baseline |
| **ElasticNet Logistic Regression** | 0.8124 | 0.8351 | 0.2841 | 0.0312 | Uncalibrated |
| **Random Forest (Tuned)** | 0.8291 | 0.8490 | 0.3120 | 0.0298 | Uncalibrated |
| **XGBoost (Tuned)** | 0.8436 | 0.8612 | 0.3345 | 0.0284 | Uncalibrated |
| **Stacked Ensemble (Uncalibrated)** | 0.8512 | 0.8698 | 0.3490 | 0.0271 | Moderate |
| **Calibrated Stack Ensemble (v1.0.0)** | **0.8512** | **0.8698** | **0.3490** | **0.0214** | **Optimal (Isotonic)** |

*Evaluated across 41 incident comorbidity targets on held-out test partitions. See [Technical Report](reports/final_comorbidity_ensemble_technical_report.md) for full per-condition metrics.*

---

## Project Structure

```
Healthcare/
├── .streamlit/                     # Global Streamlit server and theme configurations
├── app.py                          # Root launcher redirecting to Streamlit application
├── data/                           # Data storage (Parquet cache gitignored)
├── models/
│   ├── configs/                    # Frozen hyperparameter manifests
│   └── release_v1/                 # Packaged production release bundle (v1.0.0)
│       ├── calibrators/            # 41 Isotonic calibrator models (.joblib)
│       ├── stack_models/           # 41 Stack ensemble models (.joblib)
│       ├── feature_manifest.json   # Full feature contract specification
│       ├── feature_preprocessor.joblib # Trained imputation and scaling pipeline
│       ├── manifest.json           # Bundle metadata, creation date, SHA256 checksums
│       └── thresholds.json         # Condition-specific optimal decision thresholds
├── reports/                        # Markdown and JSON technical evaluation reports
├── scripts/                        # Automation scripts (packaging, reproduction, calibration)
├── src/
│   ├── data/                       # ETL, OMOP CDM timelines, DuckDB integration
│   ├── evaluation/                 # Master benchmark ladder & feature ablation
│   ├── features/                   # Feature extraction, interactions, landmarking
│   ├── inference/                  # Unified prediction pipeline & explainability API
│   ├── models/                     # Model architectures (LR, RF, XGB, Stacking, Calibration)
│   ├── packaging/                  # Release bundle builder & loader with checksum verification
│   └── splits/                     # Patient-stratified split generator
├── streamlit_app/                  # Multi-page Clinical Decision Support UI
│   ├── components/                 # UI components (Risk Cards, Condition Picker, Badges)
│   ├── disease_metadata/           # SNOMED/ICD-10 clinical registry for all 58 conditions
│   ├── navigation/                 # Multi-page router & navigation sidebar
│   ├── pages/                      # 7 Clinical pages (Assessment, Results, Network, etc.)
│   ├── state/                      # Streamlit session state management
│   └── styles/                     # CSS stylesheets & light-theme design tokens
├── tests/                          # 86 comprehensive unit & regression tests
├── requirements.txt                # Python package dependencies
└── README.md                       # Project documentation
```

---

## Quickstart & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/PrathamTandon1507/Healthcare.git
cd Healthcare
```

### 2. Set Up Virtual Environment (Recommended)
```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Running the Clinical UI

The application includes a clean, clinical-grade multi-page decision support interface:

```bash
streamlit run app.py
```

Or run directly from the application folder:
```bash
cd streamlit_app
streamlit run app.py
```

### Available Pages in Application:
1. **Overview & System Guide**: Platform introduction, clinical indications, model taxonomy, and safety notices.
2. **Patient Assessment**: Interactive clinical form with 4 preloaded clinical archetypes (Hypertensive Diabetic, Cardiac Patient, Healthy Screen, Complex Metabolic).
3. **Risk Profile & Decision Support**: Risk-tiered result cards (Elevated, Moderate, Baseline, Already Present), threshold strategies (Balanced F1, High Sensitivity, High Specificity), and top incident risks.
4. **Explainability & Risk Drivers**: Target-specific TreeSHAP risk factor contributions, odds-ratio clinical contexts, and interactive radar/waterfall charts.
5. **Comorbidity Network Explorer**: Disease co-occurrence matrices, cross-condition correlations, and network graph visualizations.
6. **Disease Registry & Taxonomy**: Searchable clinical dictionary with SNOMED CT and ICD-10 cross-references for all 58 conditions.
7. **Model Research & Benchmarks**: Full evaluation metrics ladder, Brier calibration reliability curves, and feature ablation results.

---

## Programmatic Inference API

Run predictions directly in your Python code using the unified `InferencePipeline`:

```python
from src.inference.predict import InferencePipeline

# 1. Initialize pipeline with release bundle
pipeline = InferencePipeline.from_release_bundle("models/release_v1")

# 2. Define clinical patient record
patient_data = {
    "age": 62,
    "gender_concept_id": 8507,  # 8507: Male, 8532: Female
    "conditions": [
        320128,   # Essential hypertension
        201826,   # Type 2 diabetes mellitus
        432867,   # Hyperlipidemia
    ],
    "total_visits": 14,
    "inpatient_visits": 1,
    "emergency_visits": 2,
    "outpatient_visits": 11,
    "observation_duration_days": 1825,
}

# 3. Predict calibrated risks across all 41 targets
result = pipeline.predict_patient(patient_data, threshold_strategy="balanced_f1")

# 4. Inspect results
print(f"Assessed {result.target_count} targets.")
print(f"High risk conditions detected: {len(result.high_risk_conditions)}")

for alert in result.top_alerts(n=5):
    print(f"[{alert['tier'].upper()}] {alert['name']}: {alert['risk_percent']}% (Threshold: {alert['threshold_percent']}%)")

# 5. Extract top explainable risk drivers for a specific condition (e.g. Heart Failure)
chf_explanation = pipeline.explain_prediction(patient_data, target_id="316866")
print(f"\nTop risk drivers for {chf_explanation.condition_name}:")
for driver in chf_explanation.top_positive_drivers[:3]:
    print(f" • {driver['feature_name']}: +{driver['contribution_percent']}% contribution")
```

---

## Test Suite & Quality Verification

Run the full automated test suite (86 tests covering data pipelines, models, inference, leakage audits, UI components, and packaging):

```bash
pytest -v tests/
```

### Coverage Breakdown:
- **`tests/test_leakage_audit.py`**: 8 strict temporal and partition leakage audit tests.
- **`tests/test_packaging.py`**: Release bundle manifest validation, SHA256 integrity, and serialization tests.
- **`tests/test_inference.py`**: Input validation, feature vector construction, disease masking, and batch scoring.
- **`tests/test_calibration_explainability.py`**: Isotonic fitting, SHAP tree-paths, and explanation contracts.
- **`tests/test_ui_redesign.py` & `test_streamlit_app.py`**: Component renderers, design tokens, session lifecycles, and router tests.
- **`tests/test_models.py`, `test_rf.py`, `test_xgb.py`, `test_stacking.py`**: Classifier implementations and Brier metrics.
- **`tests/test_landmarks.py`, `test_timeline.py`, `test_features.py`, `test_splits.py`**: Longitudinal OMOP CDM pipelines.

---

## Clinical Safety & Governance

> [!IMPORTANT]
> **Clinical Decision Support (CDS) Notice**:
> This platform is intended strictly as an investigative and clinical decision-support analytical tool. It is **not** a standalone diagnostic device. Predicted probabilities reflect statistical risk derived from synthetic OMOP CDM longitudinal data and must always be evaluated by qualified medical professionals in conjunction with patient clinical examinations, diagnostic testing, and standard of care guidelines.

---

## License

This project is licensed under the MIT License.
