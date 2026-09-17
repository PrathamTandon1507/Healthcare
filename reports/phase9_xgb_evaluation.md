# Phase 9: Standalone XGBoost Base Model Evaluation Report

## 1. Executive Summary & Benchmark Comparison

- **Targets Modeled**: 41 chronic comorbidities
- **Predictor Features**: 81 active clinical features (0 network placeholders)
- **Inference Source**: Pre-trained & Persisted Model Artifacts (`models/saved/xgb_tuned/`)

| Model Family | Split | Macro-AUPRC | Macro-AUROC | Precision@3 | Recall@3 | MAP@3 | Brier Score |
|---|---|---|---|---|---|---|---|
| Prevalence Floor (Phase 6) | Test | 0.0025 | 0.5000 | 0.81% | 1.83% | 0.0163 | 0.0028 |
| Tuned Logistic Regression (Phase 7) | Test | 0.0502 | 0.8676 | 20.94% | 53.15% | 0.4007 | 0.0527 |
| Tuned Random Forest (Phase 8) | Test | 0.0739 | 0.8772 | 25.51% | 63.66% | 0.5315 | 0.0401 |
| **Tuned XGBoost (Phase 9)** | **Val** | **0.1040** | **0.8851** | **26.32%** | **62.01%** | **0.5124** | **0.0464** |
| **Tuned XGBoost (Phase 9)** | **Test** | **0.0816** | **0.8824** | **26.95%** | **66.65%** | **0.5555** | **0.0499** |

## 2. Per-Disease Performance Table (Held-Out Prospective Test Split)

| Concept ID | Disease Name | Category | Test Prevalence | AUPRC | Lift vs Prev | AUROC | Best Params | Best Iter |
|---|---|---|---|---|---|---|---|---|
| `75036` | **Localized Osteoarthritis of Hand** | Musculoskeletal | 0.021% | **0.0012** | 5.5x | 0.8872 | `d=6, lr=0.03, l2=5.0` | 199 |
| `79740` | **Primary Malignant Neoplasm of Colon** | Oncology / Pre-Malignant | 0.135% | **0.0114** | 8.4x | 0.8804 | `d=6, lr=0.03, l2=5.0` | 199 |
| `80502` | **Osteoporosis** | Musculoskeletal | 0.132% | **0.0465** | 35.2x | 0.9739 | `d=6, lr=0.05, l2=1.0` | 199 |
| `192279` | **Congestive Heart Failure** | Cardiometabolic | 0.096% | **0.0555** | 57.7x | 0.9672 | `d=4, lr=0.05, l2=1.0` | 199 |
| `200970` | **Carcinoma in situ of Prostate** | Oncology / Pre-Malignant | 0.069% | **0.0045** | 6.5x | 0.9060 | `d=8, lr=0.03, l2=5.0` | 199 |
| `201826` | **Type 2 Diabetes Mellitus** | Cardiometabolic | 0.108% | **0.0181** | 16.8x | 0.8173 | `d=6, lr=0.03, l2=5.0` | 199 |
| `257012` | **Chronic Sinusitis** | Respiratory / Allergic | 0.468% | **0.1035** | 22.1x | 0.7524 | `d=6, lr=0.03, l2=5.0` | 199 |
| `258780` | **Chronic Obstructive Bronchitis (COPD)** | Respiratory / Allergic | 0.054% | **0.0005** | 0.8x | 0.3654 | `d=8, lr=0.03, l2=5.0` | 199 |
| `316866` | **Essential Hypertension** | Cardiometabolic | 0.588% | **0.1721** | 29.2x | 0.9749 | `d=6, lr=0.05, l2=1.0` | 199 |
| `317576` | **Coronary Arteriosclerosis** | Cardiometabolic | 0.189% | **0.0058** | 3.1x | 0.7116 | `d=4, lr=0.05, l2=1.0` | 199 |
| `321042` | **Cardiac Arrest** | Cardiometabolic | 0.075% | **0.0022** | 2.9x | 0.7292 | `d=4, lr=0.05, l2=1.0` | 199 |
| `378419` | **Alzheimer's Disease** | Neurological / Mental Health | 0.838% | **0.1345** | 16.1x | 0.9529 | `d=6, lr=0.03, l2=5.0` | 198 |
| `380378` | **Epilepsy / Seizure Disorder** | Neurological / Mental Health | 0.027% | **0.0663** | 245.7x | 0.8557 | `d=6, lr=0.03, l2=5.0` | 199 |
| `381316` | **Stroke (Cerebrovascular Accident)** | Neurological / Mental Health | 0.249% | **0.0237** | 9.5x | 0.8885 | `d=8, lr=0.03, l2=5.0` | 199 |
| `432867` | **Hyperlipidemia** | Cardiometabolic | 0.336% | **0.0109** | 3.2x | 0.8398 | `d=6, lr=0.05, l2=1.0` | 199 |
| `436096` | **Chronic Pain** | Musculoskeletal | 0.844% | **0.4781** | 56.7x | 0.9582 | `d=6, lr=0.03, l2=5.0` | 199 |
| `436940` | **Metabolic Syndrome X** | Cardiometabolic | 0.144% | **0.4361** | 302.6x | 0.9948 | `d=4, lr=0.05, l2=1.0` | 199 |
| `439777` | **Anemia** | Hematology | 0.880% | **0.0802** | 9.1x | 0.8526 | `d=6, lr=0.05, l2=1.0` | 199 |
| `440086` | **Childhood ADHD** | Neurological / Mental Health | 0.042% | **0.0193** | 45.9x | 0.9728 | `d=6, lr=0.05, l2=1.0` | 199 |
| `443614` | **Chronic Kidney Disease Stage 1** | Renal | 0.096% | **0.0563** | 58.5x | 0.9719 | `d=4, lr=0.05, l2=1.0` | 199 |
| `4029498` | **Seizure Disorder** | Neurological / Mental Health | 0.030% | **0.0011** | 3.6x | 0.8076 | `d=6, lr=0.03, l2=5.0` | 199 |
| `4043241` | **Familial Alzheimer's Disease** | Neurological / Mental Health | 0.087% | **0.0117** | 13.5x | 0.8654 | `d=4, lr=0.05, l2=1.0` | 199 |
| `4051466` | **Childhood Asthma** | Respiratory / Allergic | 0.135% | **0.0607** | 45.0x | 0.9854 | `d=6, lr=0.03, l2=5.0` | 199 |
| `4079749` | **Osteoarthritis of Hip** | Musculoskeletal | 0.033% | **0.0018** | 5.3x | 0.9003 | `d=6, lr=0.03, l2=5.0` | 199 |
| `4079750` | **Osteoarthritis of Knee** | Musculoskeletal | 0.099% | **0.0056** | 5.7x | 0.8707 | `d=4, lr=0.05, l2=1.0` | 199 |
| `4110591` | **Small Cell Carcinoma of Lung** | Oncology / Pre-Malignant | 0.078% | **0.0061** | 7.8x | 0.9198 | `d=6, lr=0.03, l2=5.0` | 199 |
| `4115276` | **Non-Small Cell Lung Cancer** | Oncology / Pre-Malignant | 0.408% | **0.0657** | 16.1x | 0.9062 | `d=6, lr=0.03, l2=5.0` | 199 |
| `4120314` | **Hypertriglyceridemia** | Cardiometabolic | 0.126% | **0.4645** | 368.4x | 0.9898 | `d=4, lr=0.05, l2=1.0` | 199 |
| `4129902` | **Neoplasm of Prostate** | Oncology / Pre-Malignant | 0.075% | **0.0066** | 8.9x | 0.9205 | `d=8, lr=0.03, l2=5.0` | 199 |
| `4180790` | **Malignant Neoplasm of Colon** | Oncology / Pre-Malignant | 0.057% | **0.0109** | 19.1x | 0.8568 | `d=6, lr=0.05, l2=1.0` | 198 |
| `4214376` | **Hyperglycemia** | Cardiometabolic | 0.105% | **0.3226** | 306.9x | 0.9884 | `d=6, lr=0.03, l2=5.0` | 199 |
| `4226121` | **Retinopathy due to Type 2 Diabetes** | Diabetic Complication | 0.033% | **0.0198** | 60.0x | 0.9575 | `d=4, lr=0.05, l2=1.0` | 197 |
| `4229440` | **Chronic Kidney Disease** | Renal | 0.318% | **0.0122** | 3.8x | 0.8603 | `d=6, lr=0.03, l2=5.0` | 199 |
| `4283893` | **Sinusitis** | Respiratory / Allergic | 0.360% | **0.0050** | 1.4x | 0.6188 | `d=4, lr=0.05, l2=1.0` | 199 |
| `4285898` | **Polyp of Colon** | Oncology / Pre-Malignant | 0.622% | **0.0302** | 4.9x | 0.8939 | `d=4, lr=0.05, l2=1.0` | 199 |
| `4310703` | **Non-Small Cell Carcinoma of Lung, Stage 1** | Oncology / Pre-Malignant | 0.408% | **0.0706** | 17.3x | 0.9054 | `d=6, lr=0.03, l2=5.0` | 199 |
| `4311629` | **Prediabetes** | Cardiometabolic | 0.517% | **0.0229** | 4.4x | 0.8510 | `d=8, lr=0.03, l2=5.0` | 199 |
| `37016354` | **Neuropathy due to Type 2 Diabetes** | Diabetic Complication | 0.057% | **0.0345** | 60.4x | 0.9873 | `d=8, lr=0.03, l2=5.0` | 199 |
| `37017023` | **Recurrent Rectal Polyp** | Oncology / Pre-Malignant | 0.183% | **0.0585** | 31.9x | 0.9833 | `d=6, lr=0.03, l2=5.0` | 199 |
| `37395648` | **Small Cell Carcinoma of Lung, Stage 1** | Oncology / Pre-Malignant | 0.078% | **0.0055** | 7.0x | 0.9165 | `d=6, lr=0.03, l2=5.0` | 199 |
| `43530652` | **Chronic Intractable Migraine** | Musculoskeletal | 0.886% | **0.4030** | 45.5x | 0.9417 | `d=4, lr=0.05, l2=1.0` | 199 |
