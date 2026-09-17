# Phase 9: XGBoost Early Stopping & Learning Curve Diagnostics

## 1. Early Stopping Audit Overview

Early stopping was configured with `early_stopping_rounds=15` tracking validation logloss across 200 trees.

| Concept ID | Disease Name | Best Iteration | Train AUPRC | Val AUPRC | Gen Gap (AUPRC) |
|---|---|---|---|---|---|
| `75036` | **Localized Osteoarthritis of Hand** | 199 | 0.5810 | 0.0031 | +0.5779 |
| `79740` | **Primary Malignant Neoplasm of Colon** | 199 | 0.7502 | 0.0271 | +0.7231 |
| `80502` | **Osteoporosis** | 199 | 0.6719 | 0.0950 | +0.5769 |
| `192279` | **Congestive Heart Failure** | 199 | 0.4991 | 0.0267 | +0.4723 |
| `200970` | **Carcinoma in situ of Prostate** | 199 | 0.6889 | 0.0720 | +0.6169 |
| `201826` | **Type 2 Diabetes Mellitus** | 199 | 0.1863 | 0.0059 | +0.1804 |
| `257012` | **Chronic Sinusitis** | 199 | 0.3463 | 0.0700 | +0.2763 |
| `258780` | **Chronic Obstructive Bronchitis (COPD)** | 199 | 0.7900 | 0.0008 | +0.7892 |
| `316866` | **Essential Hypertension** | 199 | 0.3364 | 0.1999 | +0.1365 |
| `317576` | **Coronary Arteriosclerosis** | 199 | 0.2253 | 0.0158 | +0.2095 |
| `321042` | **Cardiac Arrest** | 199 | 0.3217 | 0.0020 | +0.3197 |
| `378419` | **Alzheimer's Disease** | 198 | 0.4196 | 0.0850 | +0.3346 |
| `380378` | **Epilepsy / Seizure Disorder** | 199 | 0.2721 | 0.0857 | +0.1864 |
| `381316` | **Stroke (Cerebrovascular Accident)** | 199 | 0.4554 | 0.0735 | +0.3819 |
| `432867` | **Hyperlipidemia** | 199 | 0.5092 | 0.0104 | +0.4989 |
| `436096` | **Chronic Pain** | 199 | 0.4610 | 0.4335 | +0.0275 |
| `436940` | **Metabolic Syndrome X** | 199 | 0.6652 | 0.5409 | +0.1243 |
| `439777` | **Anemia** | 199 | 0.2438 | 0.0829 | +0.1609 |
| `440086` | **Childhood ADHD** | 199 | 0.5478 | 0.0061 | +0.5417 |
| `443614` | **Chronic Kidney Disease Stage 1** | 199 | 0.5233 | 0.0251 | +0.4981 |
| `4029498` | **Seizure Disorder** | 199 | 0.1982 | 0.0117 | +0.1865 |
| `4043241` | **Familial Alzheimer's Disease** | 199 | 0.7110 | 0.0022 | +0.7088 |
| `4051466` | **Childhood Asthma** | 199 | 0.2258 | 0.0390 | +0.1868 |
| `4079749` | **Osteoarthritis of Hip** | 199 | 0.5419 | 0.0022 | +0.5397 |
| `4079750` | **Osteoarthritis of Knee** | 199 | 0.1722 | 0.0051 | +0.1671 |
| `4110591` | **Small Cell Carcinoma of Lung** | 199 | 0.3819 | 0.0167 | +0.3652 |
| `4115276` | **Non-Small Cell Lung Cancer** | 199 | 0.2225 | 0.1745 | +0.0480 |
| `4120314` | **Hypertriglyceridemia** | 199 | 0.7205 | 0.6152 | +0.1054 |
| `4129902` | **Neoplasm of Prostate** | 199 | 0.6926 | 0.0852 | +0.6075 |
| `4180790` | **Malignant Neoplasm of Colon** | 198 | 0.9184 | 0.0158 | +0.9026 |
| `4214376` | **Hyperglycemia** | 199 | 0.5779 | 0.4865 | +0.0914 |
| `4226121` | **Retinopathy due to Type 2 Diabetes** | 197 | 0.5043 | 0.0269 | +0.4773 |
| `4229440` | **Chronic Kidney Disease** | 199 | 0.2911 | 0.0396 | +0.2515 |
| `4283893` | **Sinusitis** | 199 | 0.3043 | 0.0099 | +0.2944 |
| `4285898` | **Polyp of Colon** | 199 | 0.1990 | 0.0368 | +0.1622 |
| `4310703` | **Non-Small Cell Carcinoma of Lung, Stage 1** | 199 | 0.2193 | 0.1731 | +0.0462 |
| `4311629` | **Prediabetes** | 199 | 0.3258 | 0.0233 | +0.3026 |
| `37016354` | **Neuropathy due to Type 2 Diabetes** | 199 | 0.7551 | 0.0442 | +0.7110 |
| `37017023` | **Recurrent Rectal Polyp** | 199 | 0.5867 | 0.1196 | +0.4671 |
| `37395648` | **Small Cell Carcinoma of Lung, Stage 1** | 199 | 0.3648 | 0.0232 | +0.3415 |
| `43530652` | **Chronic Intractable Migraine** | 199 | 0.4466 | 0.4539 | -0.0073 |
