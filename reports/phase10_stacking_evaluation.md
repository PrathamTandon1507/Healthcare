# Phase 10: Stacked Ensemble Multi-Model Evaluation Report

## 1. Executive Summary & Full Ensemble Comparison Ladder

- **Targets Modeled**: 41 chronic comorbidities
- **Predictor Features**: 81 active clinical features
- **Ensemble Architecture**: 5-Fold Patient-Level OOF Base Learners (LR + RF + XGB) $\rightarrow$ Logistic Regression Meta-Learner
- **Total Runtime**: 1837.67 seconds

| Model Family | Split | Macro-AUPRC | Macro-AUROC | Precision@3 | Recall@3 | MAP@3 | Brier Score |
|---|---|---|---|---|---|---|---|
| Prevalence Floor (Phase 6) | Test | 0.0025 | 0.5000 | 0.81% | 1.83% | 0.0163 | 0.0028 |
| Tuned Logistic Regression (Phase 7) | Test | 0.0502 | 0.8676 | 20.94% | 53.15% | 0.4007 | 0.0527 |
| Tuned Random Forest (Phase 8) | Test | 0.0739 | 0.8772 | 25.51% | 63.66% | 0.5315 | 0.0401 |
| Tuned XGBoost (Phase 9) | Test | 0.0816 | 0.8824 | 26.95% | 66.65% | 0.5555 | 0.0499 |
| **Stacked Ensemble (Phase 10)** | **Val** | **0.0904** | **0.8781** | **26.61%** | **62.82%** | **0.5165** | **0.0031** |
| **Stacked Ensemble (Phase 10)** | **Test** | **0.0728** | **0.8693** | **26.97%** | **66.38%** | **0.5645** | **0.0023** |

## 2. Per-Disease Performance Table (Held-Out Prospective Test Split)

| Concept ID | Disease Name | Category | Test Prevalence | Stack AUPRC | Lift vs Prev | AUROC | LR Weight | RF Weight | XGB Weight |
|---|---|---|---|---|---|---|---|---|---|
| `75036` | **Localized Osteoarthritis of Hand** | Musculoskeletal | 0.021% | **0.0012** | 5.8x | 0.9037 | +2.23 | +2.26 | +2.69 |
| `79740` | **Primary Malignant Neoplasm of Colon** | Oncology / Pre-Malignant | 0.135% | **0.0126** | 9.3x | 0.8907 | +1.63 | +4.10 | +3.87 |
| `80502` | **Osteoporosis** | Musculoskeletal | 0.132% | **0.0494** | 37.4x | 0.9713 | -0.03 | +4.13 | +6.28 |
| `192279` | **Congestive Heart Failure** | Cardiometabolic | 0.096% | **0.0583** | 60.6x | 0.9533 | +2.33 | +2.25 | +2.46 |
| `200970` | **Carcinoma in situ of Prostate** | Oncology / Pre-Malignant | 0.069% | **0.0036** | 5.3x | 0.8904 | -2.10 | +6.86 | +9.56 |
| `201826` | **Type 2 Diabetes Mellitus** | Cardiometabolic | 0.108% | **0.0060** | 5.6x | 0.7486 | +2.03 | +1.49 | +1.92 |
| `257012` | **Chronic Sinusitis** | Respiratory / Allergic | 0.468% | **0.0770** | 16.4x | 0.7255 | -3.55 | +8.04 | +8.35 |
| `258780` | **Chronic Obstructive Bronchitis (COPD)** | Respiratory / Allergic | 0.054% | **0.0005** | 1.0x | 0.3993 | +2.25 | +2.94 | +4.47 |
| `316866` | **Essential Hypertension** | Cardiometabolic | 0.588% | **0.1488** | 25.3x | 0.9684 | +0.59 | +2.98 | +3.67 |
| `317576` | **Coronary Arteriosclerosis** | Cardiometabolic | 0.189% | **0.0044** | 2.3x | 0.7018 | -5.08 | +11.37 | +4.66 |
| `321042` | **Cardiac Arrest** | Cardiometabolic | 0.075% | **0.0025** | 3.3x | 0.7332 | +2.18 | +1.47 | +3.47 |
| `378419` | **Alzheimer's Disease** | Neurological / Mental Health | 0.838% | **0.1050** | 12.5x | 0.9494 | -1.66 | +5.64 | +8.32 |
| `380378` | **Epilepsy / Seizure Disorder** | Neurological / Mental Health | 0.027% | **0.1008** | 373.4x | 0.8975 | +2.28 | +2.11 | +3.24 |
| `381316` | **Stroke (Cerebrovascular Accident)** | Neurological / Mental Health | 0.249% | **0.0232** | 9.3x | 0.8854 | -1.28 | +2.80 | +6.01 |
| `432867` | **Hyperlipidemia** | Cardiometabolic | 0.336% | **0.0108** | 3.2x | 0.8140 | -2.16 | +3.83 | +8.75 |
| `436096` | **Chronic Pain** | Musculoskeletal | 0.844% | **0.4689** | 55.6x | 0.9574 | -1.36 | +5.64 | +4.60 |
| `436940` | **Metabolic Syndrome X** | Cardiometabolic | 0.144% | **0.3338** | 231.6x | 0.9949 | +2.75 | +2.99 | +3.04 |
| `439777` | **Anemia** | Hematology | 0.880% | **0.0775** | 8.8x | 0.8499 | -1.40 | +3.03 | +6.13 |
| `440086` | **Childhood ADHD** | Neurological / Mental Health | 0.042% | **0.0216** | 51.4x | 0.9740 | +2.00 | +2.07 | +1.11 |
| `443614` | **Chronic Kidney Disease Stage 1** | Renal | 0.096% | **0.0588** | 61.2x | 0.9579 | +2.36 | +2.41 | +2.44 |
| `4029498` | **Seizure Disorder** | Neurological / Mental Health | 0.030% | **0.0012** | 4.0x | 0.8484 | +1.47 | +2.21 | +2.20 |
| `4043241` | **Familial Alzheimer's Disease** | Neurological / Mental Health | 0.087% | **0.0134** | 15.3x | 0.8589 | +1.50 | +4.13 | +5.33 |
| `4051466` | **Childhood Asthma** | Respiratory / Allergic | 0.135% | **0.0767** | 56.8x | 0.9853 | +2.79 | +2.32 | +1.36 |
| `4079749` | **Osteoarthritis of Hip** | Musculoskeletal | 0.033% | **0.0024** | 7.2x | 0.9014 | +1.71 | +2.30 | +1.94 |
| `4079750` | **Osteoarthritis of Knee** | Musculoskeletal | 0.099% | **0.0045** | 4.5x | 0.8733 | +1.55 | +1.30 | +3.09 |
| `4110591` | **Small Cell Carcinoma of Lung** | Oncology / Pre-Malignant | 0.078% | **0.0046** | 5.8x | 0.9078 | +1.66 | +2.45 | +2.55 |
| `4115276` | **Non-Small Cell Lung Cancer** | Oncology / Pre-Malignant | 0.408% | **0.0717** | 17.5x | 0.9082 | +0.26 | +2.58 | +6.29 |
| `4120314` | **Hypertriglyceridemia** | Cardiometabolic | 0.126% | **0.3804** | 301.7x | 0.9938 | +3.42 | +2.18 | +3.73 |
| `4129902` | **Neoplasm of Prostate** | Oncology / Pre-Malignant | 0.075% | **0.0045** | 6.0x | 0.5040 | -3.18 | +2.65 | +12.41 |
| `4180790` | **Malignant Neoplasm of Colon** | Oncology / Pre-Malignant | 0.057% | **0.0129** | 22.5x | 0.8200 | +2.11 | +2.45 | +4.86 |
| `4214376` | **Hyperglycemia** | Cardiometabolic | 0.105% | **0.2373** | 225.8x | 0.9951 | +2.49 | +2.77 | +2.88 |
| `4226121` | **Retinopathy due to Type 2 Diabetes** | Diabetic Complication | 0.033% | **0.0137** | 41.6x | 0.9436 | +2.30 | +2.29 | +2.81 |
| `4229440` | **Chronic Kidney Disease** | Renal | 0.318% | **0.0154** | 4.8x | 0.8675 | -4.85 | +9.57 | +7.00 |
| `4283893` | **Sinusitis** | Respiratory / Allergic | 0.360% | **0.0047** | 1.3x | 0.6127 | -3.97 | +7.58 | +9.30 |
| `4285898` | **Polyp of Colon** | Oncology / Pre-Malignant | 0.622% | **0.0272** | 4.4x | 0.8829 | +0.35 | +4.02 | +7.63 |
| `4310703` | **Non-Small Cell Carcinoma of Lung, Stage 1** | Oncology / Pre-Malignant | 0.408% | **0.0741** | 18.2x | 0.9074 | +1.02 | +2.85 | +5.30 |
| `4311629` | **Prediabetes** | Cardiometabolic | 0.517% | **0.0217** | 4.2x | 0.8449 | +0.48 | +3.01 | +4.06 |
| `37016354` | **Neuropathy due to Type 2 Diabetes** | Diabetic Complication | 0.057% | **0.0366** | 64.1x | 0.9869 | +2.53 | +2.08 | +2.06 |
| `37017023` | **Recurrent Rectal Polyp** | Oncology / Pre-Malignant | 0.183% | **0.0557** | 30.4x | 0.9828 | +2.53 | +2.26 | +3.82 |
| `37395648` | **Small Cell Carcinoma of Lung, Stage 1** | Oncology / Pre-Malignant | 0.078% | **0.0054** | 6.9x | 0.9124 | +1.53 | +2.27 | +2.45 |
| `43530652` | **Chronic Intractable Migraine** | Musculoskeletal | 0.886% | **0.3573** | 40.3x | 0.9367 | -1.83 | +7.47 | +3.31 |
