# Phase 7: Logistic Regression Base Model Evaluation Report
**Model**: Standalone L2-Regularized Logistic Regression with Feature Preprocessing & C-Tuning  
**Target Diseases**: K = 41 Curated Chronic Comorbidities  
**Features**: 81 Active Clinical Predictors (StandardScaler on continuous, passthrough on binary)  

## 1. Headline Benchmark Performance

| Metric | Validation Split | Prospective Temporal Test Split | Prevalence Floor Benchmark |
|---|---|---|---|
| **Macro-AUPRC** | **0.0646** | **0.0502** | 0.0025 (17.8x Lift) |
| **Macro-AUROC** | 0.8678 | 0.8676 | 0.5000 |
| **Macro-Brier Score** | 0.1022 | 0.1099 | 0.0025 |
| **Macro-F1 (Tuned)** | 0.1130 | 0.1010 | 0.0000 |
| **Precision@3** | — | 0.2094 (21.0%) | 10.65% |
| **Recall@3** | — | 0.5315 (53.6%) | 29.46% |
| **MAP@3** | — | 0.4007 | 0.1843 |

---

## 2. Per-Disease Performance & Regularization Tuning

| Concept ID | Disease Name | Category | Best C | Val AUPRC | Test AUPRC | Test AUROC | Test Prevalence |
|---|---|---|---|---|---|---|---|
| `436940` | **Metabolic Syndrome X** | Cardiometabolic | `0.01` | 0.3377 | **0.3100** | 0.9935 | 0.0014 |
| `4120314` | **Hypertriglyceridemia** | Cardiometabolic | `0.01` | 0.4035 | **0.3085** | 0.9903 | 0.0013 |
| `43530652` | **Chronic Intractable Migraine** | Musculoskeletal | `0.01` | 0.3407 | **0.2712** | 0.8937 | 0.0089 |
| `436096` | **Chronic Pain** | Musculoskeletal | `0.01` | 0.3264 | **0.2421** | 0.8912 | 0.0084 |
| `4214376` | **Hyperglycemia** | Cardiometabolic | `0.01` | 0.1989 | **0.1235** | 0.9928 | 0.0011 |
| `378419` | **Alzheimer's Disease** | Neurological / Mental Health | `10.0` | 0.0562 | **0.1216** | 0.9595 | 0.0084 |
| `4051466` | **Childhood Asthma** | Respiratory / Allergic | `1.0` | 0.0374 | **0.0591** | 0.9838 | 0.0014 |
| `443614` | **Chronic Kidney Disease Stage 1** | Renal | `0.01` | 0.0278 | **0.0554** | 0.9336 | 0.0010 |
| `381316` | **Stroke (Cerebrovascular Accident)** | Neurological / Mental Health | `0.01` | 0.0246 | **0.0551** | 0.9109 | 0.0025 |
| `192279` | **Congestive Heart Failure** | Cardiometabolic | `0.01` | 0.0301 | **0.0535** | 0.9314 | 0.0010 |
| `4115276` | **Non-Small Cell Lung Cancer** | Oncology / Pre-Malignant | `0.01` | 0.1053 | **0.0431** | 0.8891 | 0.0041 |
| `4310703` | **Non-Small Cell Carcinoma of Lung, Stage 1** | Oncology / Pre-Malignant | `10.0` | 0.1104 | **0.0427** | 0.8887 | 0.0041 |
| `439777` | **Anemia** | Hematology | `0.01` | 0.0446 | **0.0420** | 0.8247 | 0.0088 |
| `37017023` | **Recurrent Rectal Polyp** | Oncology / Pre-Malignant | `0.1` | 0.0732 | **0.0413** | 0.9788 | 0.0018 |
| `257012` | **Chronic Sinusitis** | Respiratory / Allergic | `0.01` | 0.0252 | **0.0405** | 0.8134 | 0.0047 |
| `37016354` | **Neuropathy due to Type 2 Diabetes** | Diabetic Complication | `0.01` | 0.0289 | **0.0385** | 0.9841 | 0.0006 |
| `380378` | **Epilepsy / Seizure Disorder** | Neurological / Mental Health | `0.01` | 0.0696 | **0.0282** | 0.9080 | 0.0003 |
| `316866` | **Essential Hypertension** | Cardiometabolic | `0.01` | 0.0292 | **0.0277** | 0.8689 | 0.0059 |
| `4311629` | **Prediabetes** | Cardiometabolic | `0.01` | 0.0164 | **0.0197** | 0.8389 | 0.0052 |
| `4229440` | **Chronic Kidney Disease** | Renal | `0.01` | 0.0365 | **0.0180** | 0.8804 | 0.0032 |
| `4285898` | **Polyp of Colon** | Oncology / Pre-Malignant | `10.0` | 0.0176 | **0.0150** | 0.7841 | 0.0062 |
| `79740` | **Primary Malignant Neoplasm of Colon** | Oncology / Pre-Malignant | `10.0` | 0.0033 | **0.0125** | 0.8465 | 0.0014 |
| `432867` | **Hyperlipidemia** | Cardiometabolic | `1.0` | 0.0095 | **0.0102** | 0.8410 | 0.0034 |
| `80502` | **Osteoporosis** | Musculoskeletal | `0.01` | 0.0139 | **0.0077** | 0.8952 | 0.0013 |
| `4129902` | **Neoplasm of Prostate** | Oncology / Pre-Malignant | `0.01` | 0.0729 | **0.0076** | 0.9374 | 0.0008 |
| `317576` | **Coronary Arteriosclerosis** | Cardiometabolic | `0.01` | 0.0123 | **0.0069** | 0.7628 | 0.0019 |
| `4226121` | **Retinopathy due to Type 2 Diabetes** | Diabetic Complication | `0.01` | 0.0214 | **0.0069** | 0.8929 | 0.0003 |
| `200970` | **Carcinoma in situ of Prostate** | Oncology / Pre-Malignant | `0.01` | 0.0659 | **0.0059** | 0.9188 | 0.0007 |
| `4283893` | **Sinusitis** | Respiratory / Allergic | `0.01` | 0.0072 | **0.0053** | 0.6003 | 0.0036 |
| `4110591` | **Small Cell Carcinoma of Lung** | Oncology / Pre-Malignant | `1.0` | 0.0290 | **0.0050** | 0.8775 | 0.0008 |
| `37395648` | **Small Cell Carcinoma of Lung, Stage 1** | Oncology / Pre-Malignant | `10.0` | 0.0294 | **0.0049** | 0.8699 | 0.0008 |
| `4180790` | **Malignant Neoplasm of Colon** | Oncology / Pre-Malignant | `0.1` | 0.0095 | **0.0044** | 0.7927 | 0.0006 |
| `4079750` | **Osteoarthritis of Knee** | Musculoskeletal | `0.01` | 0.0066 | **0.0037** | 0.8638 | 0.0010 |
| `440086` | **Childhood ADHD** | Neurological / Mental Health | `10.0` | 0.0027 | **0.0035** | 0.9364 | 0.0004 |
| `201826` | **Type 2 Diabetes Mellitus** | Cardiometabolic | `0.01` | 0.0076 | **0.0032** | 0.7379 | 0.0011 |
| `4043241` | **Familial Alzheimer's Disease** | Neurological / Mental Health | `0.1` | 0.0029 | **0.0028** | 0.8289 | 0.0009 |
| `75036` | **Localized Osteoarthritis of Hand** | Musculoskeletal | `0.01` | 0.0029 | **0.0026** | 0.9291 | 0.0002 |
| `4079749` | **Osteoarthritis of Hip** | Musculoskeletal | `0.01` | 0.0020 | **0.0026** | 0.8913 | 0.0003 |
| `321042` | **Cardiac Arrest** | Cardiometabolic | `0.01` | 0.0017 | **0.0020** | 0.7125 | 0.0008 |
| `4029498` | **Seizure Disorder** | Neurological / Mental Health | `0.01` | 0.0045 | **0.0018** | 0.8689 | 0.0003 |
| `258780` | **Chronic Obstructive Bronchitis (COPD)** | Respiratory / Allergic | `1.0` | 0.0015 | **0.0015** | 0.4301 | 0.0005 |
