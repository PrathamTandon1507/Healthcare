# Phase 13: Clinical Explainability & Feature Attribution Audit

## 1. Unified Explainability Architecture

- **Interface**: `explain(patient_vector, target_disease, feature_names, model, calibrator)`
- **Linear Attribution**: Standardized score contributions $(\beta_i \cdot x_i)$.
- **Tree Attribution**: Exact decision-path contributions (Random Forest) and native TreeSHAP margins (XGBoost).
- **Meta-Learner Attribution**: Base learner trust weights and probability contributions clearly separated from clinical features.
- **Causal Language Policy**: Strictly non-causal statistical association descriptions.

## 2. Representative Multi-Disease Clinical Case Audits

### Case Audit: Essential Hypertension (OMOP `316866` — Cardiometabolic)

- **Patient Profile**: Age 18 | Total Prior Diagnoses: 2 | Observation Window: 7.5 years
- **Active Pre-Existing Conditions**: None (Incident baseline)
- **Estimated Comorbidity Risk**: **8.07%** (Uncalibrated: 15.67% | Calibration: `isotonic` | Tier: **Moderate**)
- **Model Architecture**: 4-Model Stacked Ensemble (LR + RF + XGB + Meta-LR)

**Meta-Learner Model Trust & Base Probabilities**:

| Base Model | Base Predicted Probability | Meta Weight (Trust) | Contribution to Log-Odds |
|---|---|---|---|
| Logistic Regression | 0.7748 | +0.591 | +0.458 |
| Random Forest | 0.9399 | +2.976 | +2.797 |
| Xgboost | 0.9706 | +3.671 | +3.563 |

**Top Factors Increasing Risk (Predictive Associations)**:

| Feature Name | Patient Value | Relative Importance Score | Clinical Context |
|---|---|---|---|
| `age_at_landmark` | 18.00 | **+60.4136** | Statistical comorbidity risk association |
| `age_lt_30` | 1.00 | **+13.8368** | Statistical comorbidity risk association |
| `has_hist_316866` | 0.00 | **+2.3523** | Statistical comorbidity risk association |
| `prior_obs_years` | 7.47 | **+1.9680** | Statistical comorbidity risk association |
| `total_prior_condition_count` | 2.00 | **+1.9538** | Statistical comorbidity risk association |

> *This statistical attribution describes predictive associations observed in population training data. It does not establish causal etiology.*

---

### Case Audit: Type 2 Diabetes Mellitus (OMOP `201826` — Cardiometabolic)

- **Patient Profile**: Age 46 | Total Prior Diagnoses: 2 | Observation Window: 21.0 years
- **Active Pre-Existing Conditions**: None (Incident baseline)
- **Estimated Comorbidity Risk**: **1.88%** (Uncalibrated: 1.06% | Calibration: `isotonic` | Tier: **Low**)
- **Model Architecture**: 4-Model Stacked Ensemble (LR + RF + XGB + Meta-LR)

**Meta-Learner Model Trust & Base Probabilities**:

| Base Model | Base Predicted Probability | Meta Weight (Trust) | Contribution to Log-Odds |
|---|---|---|---|
| Logistic Regression | 0.8696 | +2.033 | +1.768 |
| Random Forest | 0.7752 | +1.490 | +1.155 |
| Xgboost | 0.8409 | +1.918 | +1.613 |

**Top Factors Increasing Risk (Predictive Associations)**:

| Feature Name | Patient Value | Relative Importance Score | Clinical Context |
|---|---|---|---|
| `age_at_landmark` | 46.00 | **+22.9911** | Statistical comorbidity risk association |
| `age_40_49` | 1.00 | **+19.1320** | Statistical comorbidity risk association |
| `total_prior_condition_count` | 2.00 | **+17.8152** | Statistical comorbidity risk association |
| `race_white` | 0.00 | **+13.6490** | Statistical comorbidity risk association |
| `prior_obs_years` | 20.97 | **+5.9113** | Statistical comorbidity risk association |

> *This statistical attribution describes predictive associations observed in population training data. It does not establish causal etiology.*

---

### Case Audit: Coronary Arteriosclerosis (OMOP `317576` — Cardiometabolic)

- **Patient Profile**: Age 50 | Total Prior Diagnoses: 6 | Observation Window: 16.5 years
- **Active Pre-Existing Conditions**: Anemia, Prediabetes
- **Estimated Comorbidity Risk**: **0.56%** (Uncalibrated: 0.07% | Calibration: `isotonic` | Tier: **Low**)
- **Model Architecture**: 4-Model Stacked Ensemble (LR + RF + XGB + Meta-LR)

**Meta-Learner Model Trust & Base Probabilities**:

| Base Model | Base Predicted Probability | Meta Weight (Trust) | Contribution to Log-Odds |
|---|---|---|---|
| Logistic Regression | 0.5504 | -5.083 | -2.798 |
| Random Forest | 0.3172 | +11.370 | +3.607 |
| Xgboost | 0.4293 | +4.660 | +2.000 |

**Top Factors Increasing Risk (Predictive Associations)**:

| Feature Name | Patient Value | Relative Importance Score | Clinical Context |
|---|---|---|---|
| `gender_female` | 0.00 | **+36.4560** | Statistical comorbidity risk association |
| `gender_male` | 1.00 | **+16.0988** | Statistical comorbidity risk association |
| `has_hist_4115276` | 0.00 | **+15.3490** | Statistical comorbidity risk association |
| `age_50_59` | 1.00 | **+11.1269** | Statistical comorbidity risk association |
| `has_hist_317576` | 0.00 | **+10.1121** | Statistical comorbidity risk association |

> *This statistical attribution describes predictive associations observed in population training data. It does not establish causal etiology.*

---

### Case Audit: Hyperlipidemia (OMOP `432867` — Cardiometabolic)

- **Patient Profile**: Age 47 | Total Prior Diagnoses: 6 | Observation Window: 28.9 years
- **Active Pre-Existing Conditions**: Essential Hypertension
- **Estimated Comorbidity Risk**: **1.11%** (Uncalibrated: 0.85% | Calibration: `isotonic` | Tier: **Low**)
- **Model Architecture**: 4-Model Stacked Ensemble (LR + RF + XGB + Meta-LR)

**Meta-Learner Model Trust & Base Probabilities**:

| Base Model | Base Predicted Probability | Meta Weight (Trust) | Contribution to Log-Odds |
|---|---|---|---|
| Logistic Regression | 0.6753 | -2.161 | -1.459 |
| Random Forest | 0.6690 | +3.831 | +2.563 |
| Xgboost | 0.5334 | +8.753 | +4.669 |

**Top Factors Increasing Risk (Predictive Associations)**:

| Feature Name | Patient Value | Relative Importance Score | Clinical Context |
|---|---|---|---|
| `has_hist_432867` | 0.00 | **+49.6301** | Statistical comorbidity risk association |
| `has_hist_4115276` | 0.00 | **+37.7055** | Statistical comorbidity risk association |
| `age_at_landmark` | 47.00 | **+35.3637** | Statistical comorbidity risk association |
| `has_hist_439777` | 0.00 | **+23.1841** | Statistical comorbidity risk association |
| `age_lt_30` | 0.00 | **+12.9451** | Statistical comorbidity risk association |

> *This statistical attribution describes predictive associations observed in population training data. It does not establish causal etiology.*

---

### Case Audit: Chronic Kidney Disease Stage 1 (OMOP `443614` — Renal)

- **Patient Profile**: Age 37 | Total Prior Diagnoses: 5 | Observation Window: 18.0 years
- **Active Pre-Existing Conditions**: Type 2 Diabetes Mellitus, Essential Hypertension, Anemia
- **Estimated Comorbidity Risk**: **2.74%** (Uncalibrated: 1.59% | Calibration: `isotonic` | Tier: **Low**)
- **Model Architecture**: 4-Model Stacked Ensemble (LR + RF + XGB + Meta-LR)

**Meta-Learner Model Trust & Base Probabilities**:

| Base Model | Base Predicted Probability | Meta Weight (Trust) | Contribution to Log-Odds |
|---|---|---|---|
| Logistic Regression | 0.9782 | +2.358 | +2.306 |
| Random Forest | 0.4403 | +2.408 | +1.060 |
| Xgboost | 0.8074 | +2.439 | +1.970 |

**Top Factors Increasing Risk (Predictive Associations)**:

| Feature Name | Patient Value | Relative Importance Score | Clinical Context |
|---|---|---|---|
| `has_hist_201826` | 1.00 | **+58.0220** | Statistical comorbidity risk association |
| `has_hist_192279` | 0.00 | **+6.0511** | Statistical comorbidity risk association |
| `age_30_39` | 1.00 | **+5.1785** | Statistical comorbidity risk association |
| `age_at_landmark` | 37.00 | **+4.6269** | Statistical comorbidity risk association |
| `interaction_diabetes_and_hypertension` | 1.00 | **+3.6835** | Statistical comorbidity risk association |

> *This statistical attribution describes predictive associations observed in population training data. It does not establish causal etiology.*

---

### Case Audit: Epilepsy / Seizure Disorder (OMOP `380378` — Neurological / Mental Health)

- **Patient Profile**: Age 5 | Total Prior Diagnoses: 4 | Observation Window: 5.3 years
- **Active Pre-Existing Conditions**: Seizure Disorder
- **Estimated Comorbidity Risk**: **10.70%** (Uncalibrated: 14.58% | Calibration: `isotonic` | Tier: **Moderate**)
- **Model Architecture**: 4-Model Stacked Ensemble (LR + RF + XGB + Meta-LR)

**Meta-Learner Model Trust & Base Probabilities**:

| Base Model | Base Predicted Probability | Meta Weight (Trust) | Contribution to Log-Odds |
|---|---|---|---|
| Logistic Regression | 0.9897 | +2.281 | +2.257 |
| Random Forest | 0.9493 | +2.106 | +2.000 |
| Xgboost | 0.9756 | +3.244 | +3.165 |

**Top Factors Increasing Risk (Predictive Associations)**:

| Feature Name | Patient Value | Relative Importance Score | Clinical Context |
|---|---|---|---|
| `has_hist_4029498` | 1.00 | **+63.8533** | Statistical comorbidity risk association |
| `age_at_landmark` | 5.00 | **+20.7844** | Statistical comorbidity risk association |
| `prior_obs_years` | 5.33 | **+6.6227** | Statistical comorbidity risk association |
| `has_hist_380378` | 0.00 | **+1.7467** | Statistical comorbidity risk association |
| `bg_viral_sinusitis` | 1.00 | **+1.7350** | Statistical comorbidity risk association |

> *This statistical attribution describes predictive associations observed in population training data. It does not establish causal etiology.*

---

