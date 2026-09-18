# Phase 14: Comprehensive Model Ladder & Multi-Target Evaluation Report

## 1. Master Benchmark Ladder (Validation & Prospective Test Splits)

| Model Family | Split | Macro-AUPRC | Macro-AUROC | Precision@3 | Recall@3 | MAP@3 | Precision@5 | Recall@5 | MAP@5 | Brier Score |
|---|---|---|---|---|---|---|---|---|---|---|
| Prevalence Floor (Phase 6) | Val | **0.0033** | 0.5000 | 9.99% | 26.50% | 0.1744 | 8.84% | 37.89% | 0.2008 | 0.003273 |
| Prevalence Floor (Phase 6) | **Test** | **0.0025** | 0.5000 | 10.65% | 29.46% | 0.1843 | 9.37% | 40.96% | 0.2118 | 0.002451 |
| Tuned Logistic Regression (Phase 7) | Val | **0.0646** | 0.8678 | 21.62% | 51.46% | 0.3999 | 17.10% | 66.65% | 0.4403 | 0.102207 |
| Tuned Logistic Regression (Phase 7) | **Test** | **0.0502** | 0.8676 | 20.94% | 53.15% | 0.4007 | 17.00% | 69.72% | 0.4455 | 0.109898 |
| Tuned Random Forest (Phase 8) | Val | **0.0881** | 0.8754 | 25.35% | 58.84% | 0.4936 | 18.71% | 72.19% | 0.5289 | 0.070454 |
| Tuned Random Forest (Phase 8) | **Test** | **0.0739** | 0.8772 | 25.51% | 63.66% | 0.5315 | 18.13% | 73.80% | 0.5596 | 0.071803 |
| Tuned XGBoost (Phase 9) | Val | **0.1040** | 0.8851 | 26.32% | 62.01% | 0.5124 | 19.75% | 76.75% | 0.5529 | 0.046351 |
| Tuned XGBoost (Phase 9) | **Test** | **0.0816** | 0.8824 | 26.95% | 66.65% | 0.5555 | 18.73% | 76.51% | 0.5811 | 0.049943 |
| Stacked Ensemble (Phase 10) | Val | **0.0904** | 0.8781 | 26.61% | 62.82% | 0.5165 | 19.17% | 74.59% | 0.5489 | 0.003068 |
| Stacked Ensemble (Phase 10) | **Test** | **0.0728** | 0.8693 | 26.97% | 66.38% | 0.5645 | 18.99% | 77.17% | 0.5939 | 0.002329 |
| **Calibrated Stacked Ensemble (Phase 12)** | Val | **0.0950** | 0.8927 | 28.93% | 66.98% | 0.5688 | 20.61% | 79.37% | 0.6018 | 0.002957 |
| **Calibrated Stacked Ensemble (Phase 12)** | **Test** | **0.0680** | 0.8681 | 27.61% | 68.51% | 0.5869 | 19.28% | 77.80% | 0.6134 | 0.002304 |

---

## 2. Stratified Prevalence-Tier Breakdown (Held-Out Test Split)

| Model Family | High Prevalence (>0.5%) Macro-AUPRC | Medium Prevalence (0.1-0.5%) Macro-AUPRC | Low Prevalence (<0.1%) Macro-AUPRC |
|---|---|---|---|
| Prevalence Floor | **0.0074** | **0.0024** | **0.0006** |
| Logistic Regression | **0.1056** | **0.0680** | **0.0128** |
| Random Forest | **0.1736** | **0.0910** | **0.0198** |
| XGBoost | **0.1887** | **0.1073** | **0.0172** |
| Stacked Ensemble | **0.1723** | **0.0896** | **0.0192** |
| **Calibrated Stack** | **0.1646** | **0.0845** | **0.0158** |

---

## 3. Stacked Ensemble vs. Best Single Base Learner Comparison

| Concept ID | Disease Name | Category | Best Base Model | Best Base AUPRC | Stack AUPRC | Delta vs Best Base | Status |
|---|---|---|---|---|---|---|---|
| `436096` | **Chronic Pain** | Musculoskeletal | XGBoost | 0.4781 | **0.4689** | -0.0092 | Single Model Competitive |
| `4120314` | **Hypertriglyceridemia** | Cardiometabolic | XGBoost | 0.4645 | **0.3804** | -0.0841 | Single Model Competitive |
| `43530652` | **Chronic Intractable Migraine** | Musculoskeletal | XGBoost | 0.4030 | **0.3573** | -0.0457 | Single Model Competitive |
| `436940` | **Metabolic Syndrome X** | Cardiometabolic | XGBoost | 0.4361 | **0.3338** | -0.1023 | Single Model Competitive |
| `4214376` | **Hyperglycemia** | Cardiometabolic | XGBoost | 0.3226 | **0.2373** | -0.0852 | Single Model Competitive |
| `316866` | **Essential Hypertension** | Cardiometabolic | XGBoost | 0.1721 | **0.1488** | -0.0233 | Single Model Competitive |
| `378419` | **Alzheimer's Disease** | Neurological / Mental Health | Random Forest | 0.1772 | **0.1050** | -0.0722 | Single Model Competitive |
| `380378` | **Epilepsy / Seizure Disorder** | Neurological / Mental Health | Random Forest | 0.0792 | **0.1008** | +0.0216 | **Stack Outperforms / Ties** |
| `439777` | **Anemia** | Hematology | XGBoost | 0.0802 | **0.0775** | -0.0027 | Single Model Competitive |
| `257012` | **Chronic Sinusitis** | Respiratory / Allergic | XGBoost | 0.1035 | **0.0770** | -0.0266 | Single Model Competitive |
| `4051466` | **Childhood Asthma** | Respiratory / Allergic | XGBoost | 0.0607 | **0.0767** | +0.0159 | **Stack Outperforms / Ties** |
| `4310703` | **Non-Small Cell Carcinoma of Lung, Stage 1** | Oncology / Pre-Malignant | Random Forest | 0.0708 | **0.0741** | +0.0033 | **Stack Outperforms / Ties** |
| `4115276` | **Non-Small Cell Lung Cancer** | Oncology / Pre-Malignant | Random Forest | 0.0834 | **0.0717** | -0.0117 | Single Model Competitive |
| `443614` | **Chronic Kidney Disease Stage 1** | Renal | Random Forest | 0.0636 | **0.0588** | -0.0048 | Single Model Competitive |
| `192279` | **Congestive Heart Failure** | Cardiometabolic | Random Forest | 0.0655 | **0.0583** | -0.0073 | Single Model Competitive |
| `37017023` | **Recurrent Rectal Polyp** | Oncology / Pre-Malignant | XGBoost | 0.0585 | **0.0557** | -0.0028 | Single Model Competitive |
| `80502` | **Osteoporosis** | Musculoskeletal | XGBoost | 0.0465 | **0.0494** | +0.0028 | **Stack Outperforms / Ties** |
| `37016354` | **Neuropathy due to Type 2 Diabetes** | Diabetic Complication | Random Forest | 0.0479 | **0.0366** | -0.0113 | Single Model Competitive |
| `4285898` | **Polyp of Colon** | Oncology / Pre-Malignant | XGBoost | 0.0302 | **0.0272** | -0.0030 | Single Model Competitive |
| `381316` | **Stroke (Cerebrovascular Accident)** | Neurological / Mental Health | Logistic Regression | 0.0551 | **0.0232** | -0.0319 | Single Model Competitive |
| `4311629` | **Prediabetes** | Cardiometabolic | XGBoost | 0.0229 | **0.0217** | -0.0012 | Single Model Competitive |
| `440086` | **Childhood ADHD** | Neurological / Mental Health | XGBoost | 0.0193 | **0.0216** | +0.0023 | **Stack Outperforms / Ties** |
| `4229440` | **Chronic Kidney Disease** | Renal | Logistic Regression | 0.0180 | **0.0154** | -0.0026 | Single Model Competitive |
| `4226121` | **Retinopathy due to Type 2 Diabetes** | Diabetic Complication | XGBoost | 0.0198 | **0.0137** | -0.0061 | Single Model Competitive |
| `4043241` | **Familial Alzheimer's Disease** | Neurological / Mental Health | Random Forest | 0.0180 | **0.0134** | -0.0047 | Single Model Competitive |
| `4180790` | **Malignant Neoplasm of Colon** | Oncology / Pre-Malignant | XGBoost | 0.0109 | **0.0129** | +0.0019 | **Stack Outperforms / Ties** |
| `79740` | **Primary Malignant Neoplasm of Colon** | Oncology / Pre-Malignant | Random Forest | 0.0132 | **0.0126** | -0.0006 | Single Model Competitive |
| `432867` | **Hyperlipidemia** | Cardiometabolic | Random Forest | 0.0127 | **0.0108** | -0.0019 | Single Model Competitive |
| `201826` | **Type 2 Diabetes Mellitus** | Cardiometabolic | XGBoost | 0.0181 | **0.0060** | -0.0121 | Single Model Competitive |
| `37395648` | **Small Cell Carcinoma of Lung, Stage 1** | Oncology / Pre-Malignant | XGBoost | 0.0055 | **0.0054** | -0.0001 | Single Model Competitive |
| `4283893` | **Sinusitis** | Respiratory / Allergic | Logistic Regression | 0.0053 | **0.0047** | -0.0006 | Single Model Competitive |
| `4110591` | **Small Cell Carcinoma of Lung** | Oncology / Pre-Malignant | XGBoost | 0.0061 | **0.0046** | -0.0016 | Single Model Competitive |
| `4129902` | **Neoplasm of Prostate** | Oncology / Pre-Malignant | Logistic Regression | 0.0076 | **0.0045** | -0.0031 | Single Model Competitive |
| `4079750` | **Osteoarthritis of Knee** | Musculoskeletal | Random Forest | 0.0131 | **0.0045** | -0.0086 | Single Model Competitive |
| `317576` | **Coronary Arteriosclerosis** | Cardiometabolic | Random Forest | 0.0083 | **0.0044** | -0.0039 | Single Model Competitive |
| `200970` | **Carcinoma in situ of Prostate** | Oncology / Pre-Malignant | Logistic Regression | 0.0059 | **0.0036** | -0.0022 | Single Model Competitive |
| `321042` | **Cardiac Arrest** | Cardiometabolic | Random Forest | 0.0053 | **0.0025** | -0.0028 | Single Model Competitive |
| `4079749` | **Osteoarthritis of Hip** | Musculoskeletal | Random Forest | 0.0072 | **0.0024** | -0.0048 | Single Model Competitive |
| `75036` | **Localized Osteoarthritis of Hand** | Musculoskeletal | Logistic Regression | 0.0026 | **0.0012** | -0.0014 | Single Model Competitive |
| `4029498` | **Seizure Disorder** | Neurological / Mental Health | Logistic Regression | 0.0018 | **0.0012** | -0.0006 | Single Model Competitive |
| `258780` | **Chronic Obstructive Bronchitis (COPD)** | Respiratory / Allergic | Logistic Regression | 0.0015 | **0.0005** | -0.0010 | Single Model Competitive |
