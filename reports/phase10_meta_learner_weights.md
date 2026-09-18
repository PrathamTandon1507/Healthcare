# Phase 10: Meta-Learner Weight Attribution & Base Model Trust Audit

## 1. Meta-Learner Trust Coefficients per Comorbidity Target

| Concept ID | Disease Name | Category | Intercept | LR Weight (Linear Anchor) | RF Weight (Bagged Non-Linear) | XGB Weight (Boosted Trees) | Dominant Base Model |
|---|---|---|---|---|---|---|---|
| `75036` | **Localized Osteoarthritis of Hand** | Musculoskeletal | -9.41 | +2.229 | +2.256 | +2.691 | **XGBoost** |
| `79740` | **Primary Malignant Neoplasm of Colon** | Oncology / Pre-Malignant | -9.75 | +1.632 | +4.100 | +3.870 | **Random Forest** |
| `80502` | **Osteoporosis** | Musculoskeletal | -10.42 | -0.026 | +4.128 | +6.277 | **XGBoost** |
| `192279` | **Congestive Heart Failure** | Cardiometabolic | -9.23 | +2.331 | +2.247 | +2.463 | **XGBoost** |
| `200970` | **Carcinoma in situ of Prostate** | Oncology / Pre-Malignant | -13.81 | -2.101 | +6.861 | +9.559 | **XGBoost** |
| `201826` | **Type 2 Diabetes Mellitus** | Cardiometabolic | -9.07 | +2.033 | +1.490 | +1.918 | **Logistic Regression** |
| `257012` | **Chronic Sinusitis** | Respiratory / Allergic | -11.32 | -3.553 | +8.044 | +8.350 | **XGBoost** |
| `258780` | **Chronic Obstructive Bronchitis (COPD)** | Respiratory / Allergic | -9.83 | +2.254 | +2.944 | +4.467 | **XGBoost** |
| `316866` | **Essential Hypertension** | Cardiometabolic | -8.50 | +0.590 | +2.976 | +3.671 | **XGBoost** |
| `317576` | **Coronary Arteriosclerosis** | Cardiometabolic | -10.12 | -5.083 | +11.370 | +4.659 | **Random Forest** |
| `321042` | **Cardiac Arrest** | Cardiometabolic | -9.33 | +2.181 | +1.471 | +3.469 | **XGBoost** |
| `378419` | **Alzheimer's Disease** | Neurological / Mental Health | -12.45 | -1.656 | +5.638 | +8.324 | **XGBoost** |
| `380378` | **Epilepsy / Seizure Disorder** | Neurological / Mental Health | -9.19 | +2.281 | +2.106 | +3.244 | **XGBoost** |
| `381316` | **Stroke (Cerebrovascular Accident)** | Neurological / Mental Health | -8.56 | -1.278 | +2.795 | +6.014 | **XGBoost** |
| `432867` | **Hyperlipidemia** | Cardiometabolic | -10.54 | -2.161 | +3.831 | +8.753 | **XGBoost** |
| `436096` | **Chronic Pain** | Musculoskeletal | -8.96 | -1.360 | +5.639 | +4.602 | **Random Forest** |
| `436940` | **Metabolic Syndrome X** | Cardiometabolic | -9.15 | +2.753 | +2.986 | +3.037 | **XGBoost** |
| `439777` | **Anemia** | Hematology | -8.86 | -1.396 | +3.032 | +6.132 | **XGBoost** |
| `440086` | **Childhood ADHD** | Neurological / Mental Health | -8.75 | +1.999 | +2.074 | +1.114 | **Random Forest** |
| `443614` | **Chronic Kidney Disease Stage 1** | Renal | -9.46 | +2.358 | +2.408 | +2.439 | **XGBoost** |
| `4029498` | **Seizure Disorder** | Neurological / Mental Health | -8.99 | +1.474 | +2.211 | +2.202 | **Random Forest** |
| `4043241` | **Familial Alzheimer's Disease** | Neurological / Mental Health | -10.99 | +1.504 | +4.126 | +5.328 | **XGBoost** |
| `4051466` | **Childhood Asthma** | Respiratory / Allergic | -9.23 | +2.791 | +2.325 | +1.361 | **Logistic Regression** |
| `4079749` | **Osteoarthritis of Hip** | Musculoskeletal | -9.20 | +1.706 | +2.296 | +1.938 | **Random Forest** |
| `4079750` | **Osteoarthritis of Knee** | Musculoskeletal | -9.11 | +1.546 | +1.304 | +3.089 | **XGBoost** |
| `4110591` | **Small Cell Carcinoma of Lung** | Oncology / Pre-Malignant | -9.13 | +1.663 | +2.447 | +2.548 | **XGBoost** |
| `4115276` | **Non-Small Cell Lung Cancer** | Oncology / Pre-Malignant | -10.26 | +0.261 | +2.585 | +6.287 | **XGBoost** |
| `4120314` | **Hypertriglyceridemia** | Cardiometabolic | -9.33 | +3.422 | +2.183 | +3.733 | **XGBoost** |
| `4129902` | **Neoplasm of Prostate** | Oncology / Pre-Malignant | -11.85 | -3.185 | +2.651 | +12.411 | **XGBoost** |
| `4180790` | **Malignant Neoplasm of Colon** | Oncology / Pre-Malignant | -9.48 | +2.107 | +2.453 | +4.858 | **XGBoost** |
| `4214376` | **Hyperglycemia** | Cardiometabolic | -9.03 | +2.490 | +2.773 | +2.881 | **XGBoost** |
| `4226121` | **Retinopathy due to Type 2 Diabetes** | Diabetic Complication | -9.44 | +2.303 | +2.288 | +2.809 | **XGBoost** |
| `4229440` | **Chronic Kidney Disease** | Renal | -10.91 | -4.846 | +9.567 | +6.998 | **Random Forest** |
| `4283893` | **Sinusitis** | Respiratory / Allergic | -11.39 | -3.972 | +7.580 | +9.303 | **XGBoost** |
| `4285898` | **Polyp of Colon** | Oncology / Pre-Malignant | -12.09 | +0.346 | +4.015 | +7.632 | **XGBoost** |
| `4310703` | **Non-Small Cell Carcinoma of Lung, Stage 1** | Oncology / Pre-Malignant | -10.30 | +1.016 | +2.849 | +5.296 | **XGBoost** |
| `4311629` | **Prediabetes** | Cardiometabolic | -9.02 | +0.479 | +3.010 | +4.060 | **XGBoost** |
| `37016354` | **Neuropathy due to Type 2 Diabetes** | Diabetic Complication | -8.86 | +2.535 | +2.083 | +2.063 | **Logistic Regression** |
| `37017023` | **Recurrent Rectal Polyp** | Oncology / Pre-Malignant | -9.64 | +2.533 | +2.264 | +3.821 | **XGBoost** |
| `37395648` | **Small Cell Carcinoma of Lung, Stage 1** | Oncology / Pre-Malignant | -9.13 | +1.531 | +2.266 | +2.452 | **XGBoost** |
| `43530652` | **Chronic Intractable Migraine** | Musculoskeletal | -8.98 | -1.832 | +7.471 | +3.311 | **Random Forest** |
