# Phase 8: Random Forest Base Model Evaluation Report
**Model**: Standalone Tuned Random Forest (100 Trees, Balanced Class Weighting, OOB Tracking)  
**Target Diseases**: K = 41 Curated Chronic Comorbidities  
**Features**: 81 Active Clinical Predictors  

## 1. Headline Benchmark Performance

| Metric | Validation Split | Prospective Temporal Test Split | Prevalence Floor Benchmark | Tuned LR (Phase 7) |
|---|---|---|---|---|
| **Macro-AUPRC** | **0.0881** | **0.0739** | 0.0025 | 0.0502 |
| **Macro-AUROC** | 0.8754 | 0.8772 | 0.5000 | 0.8676 |
| **Macro-Brier Score** | 0.0705 | 0.0718 | 0.0025 | 0.1099 |
| **Precision@3** | — | 0.2551 (25.0%) | 10.65% | 20.94% |
| **Recall@3** | — | 0.6366 (62.6%) | 29.46% | 53.15% |
| **MAP@3** | — | 0.5315 | 0.1843 | 0.4007 |

---

## 2. Per-Disease Performance & Regularization Tuning

| Concept ID | Disease Name | Category | Best Config | Val AUPRC | Test AUPRC | Test AUROC | Test Prevalence |
|---|---|---|---|---|---|---|---|
| `436096` | **Chronic Pain** | Musculoskeletal | `d=10, l=5, f=0.3` | 0.4002 | **0.4268** | 0.9518 | 0.0084 |
| `4120314` | **Hypertriglyceridemia** | Cardiometabolic | `d=8, l=10, f=sqrt` | 0.5139 | **0.3987** | 0.9954 | 0.0013 |
| `436940` | **Metabolic Syndrome X** | Cardiometabolic | `d=10, l=5, f=0.3` | 0.3884 | **0.3596** | 0.9967 | 0.0014 |
| `43530652` | **Chronic Intractable Migraine** | Musculoskeletal | `d=10, l=5, f=0.3` | 0.4289 | **0.3588** | 0.9332 | 0.0089 |
| `4214376` | **Hyperglycemia** | Cardiometabolic | `d=10, l=5, f=0.3` | 0.2865 | **0.2438** | 0.9962 | 0.0011 |
| `378419` | **Alzheimer's Disease** | Neurological / Mental Health | `d=10, l=5, f=0.3` | 0.0861 | **0.1772** | 0.9546 | 0.0084 |
| `316866` | **Essential Hypertension** | Cardiometabolic | `d=10, l=5, f=0.3` | 0.1877 | **0.1375** | 0.9648 | 0.0059 |
| `4115276` | **Non-Small Cell Lung Cancer** | Oncology / Pre-Malignant | `d=10, l=5, f=0.3` | 0.1520 | **0.0834** | 0.9109 | 0.0041 |
| `380378` | **Epilepsy / Seizure Disorder** | Neurological / Mental Health | `d=10, l=5, f=sqrt` | 0.0984 | **0.0792** | 0.8779 | 0.0003 |
| `439777` | **Anemia** | Hematology | `d=10, l=5, f=0.3` | 0.0711 | **0.0776** | 0.8562 | 0.0088 |
| `4310703` | **Non-Small Cell Carcinoma of Lung, Stage 1** | Oncology / Pre-Malignant | `d=10, l=5, f=0.3` | 0.1514 | **0.0708** | 0.9093 | 0.0041 |
| `257012` | **Chronic Sinusitis** | Respiratory / Allergic | `d=8, l=10, f=sqrt` | 0.0560 | **0.0704** | 0.7469 | 0.0047 |
| `192279` | **Congestive Heart Failure** | Cardiometabolic | `d=10, l=5, f=sqrt` | 0.0324 | **0.0655** | 0.9704 | 0.0010 |
| `443614` | **Chronic Kidney Disease Stage 1** | Renal | `d=10, l=5, f=sqrt` | 0.0366 | **0.0636** | 0.9728 | 0.0010 |
| `37017023` | **Recurrent Rectal Polyp** | Oncology / Pre-Malignant | `d=10, l=5, f=sqrt` | 0.0724 | **0.0541** | 0.9817 | 0.0018 |
| `4051466` | **Childhood Asthma** | Respiratory / Allergic | `d=10, l=5, f=sqrt` | 0.0334 | **0.0518** | 0.9852 | 0.0014 |
| `37016354` | **Neuropathy due to Type 2 Diabetes** | Diabetic Complication | `d=8, l=10, f=sqrt` | 0.0392 | **0.0479** | 0.9850 | 0.0006 |
| `80502` | **Osteoporosis** | Musculoskeletal | `d=10, l=5, f=0.3` | 0.0879 | **0.0450** | 0.9627 | 0.0013 |
| `4285898` | **Polyp of Colon** | Oncology / Pre-Malignant | `d=10, l=5, f=0.3` | 0.0271 | **0.0187** | 0.8305 | 0.0062 |
| `4311629` | **Prediabetes** | Cardiometabolic | `d=10, l=5, f=0.3` | 0.0211 | **0.0186** | 0.8371 | 0.0052 |
| `4226121` | **Retinopathy due to Type 2 Diabetes** | Diabetic Complication | `d=8, l=10, f=sqrt` | 0.0263 | **0.0181** | 0.9544 | 0.0003 |
| `4043241` | **Familial Alzheimer's Disease** | Neurological / Mental Health | `d=8, l=10, f=sqrt` | 0.0021 | **0.0180** | 0.8759 | 0.0009 |
| `381316` | **Stroke (Cerebrovascular Accident)** | Neurological / Mental Health | `d=10, l=5, f=0.3` | 0.0881 | **0.0178** | 0.9032 | 0.0025 |
| `4229440` | **Chronic Kidney Disease** | Renal | `d=10, l=5, f=sqrt` | 0.0426 | **0.0174** | 0.8952 | 0.0032 |
| `79740` | **Primary Malignant Neoplasm of Colon** | Oncology / Pre-Malignant | `d=14, l=2, f=sqrt` | 0.0076 | **0.0132** | 0.8994 | 0.0014 |
| `4079750` | **Osteoarthritis of Knee** | Musculoskeletal | `d=8, l=10, f=sqrt` | 0.0058 | **0.0131** | 0.8555 | 0.0010 |
| `432867` | **Hyperlipidemia** | Cardiometabolic | `d=10, l=5, f=0.3` | 0.0105 | **0.0127** | 0.8474 | 0.0034 |
| `440086` | **Childhood ADHD** | Neurological / Mental Health | `d=14, l=2, f=sqrt` | 0.0062 | **0.0093** | 0.9693 | 0.0004 |
| `317576` | **Coronary Arteriosclerosis** | Cardiometabolic | `d=10, l=5, f=sqrt` | 0.0110 | **0.0083** | 0.7359 | 0.0019 |
| `4079749` | **Osteoarthritis of Hip** | Musculoskeletal | `d=14, l=2, f=sqrt` | 0.0024 | **0.0072** | 0.9048 | 0.0003 |
| `4180790` | **Malignant Neoplasm of Colon** | Oncology / Pre-Malignant | `d=10, l=5, f=0.3` | 0.0164 | **0.0069** | 0.8340 | 0.0006 |
| `4129902` | **Neoplasm of Prostate** | Oncology / Pre-Malignant | `d=8, l=10, f=sqrt` | 0.0837 | **0.0065** | 0.9146 | 0.0008 |
| `321042` | **Cardiac Arrest** | Cardiometabolic | `d=8, l=10, f=sqrt` | 0.0018 | **0.0053** | 0.7310 | 0.0008 |
| `4283893` | **Sinusitis** | Respiratory / Allergic | `d=8, l=10, f=sqrt` | 0.0064 | **0.0049** | 0.6288 | 0.0036 |
| `37395648` | **Small Cell Carcinoma of Lung, Stage 1** | Oncology / Pre-Malignant | `d=10, l=5, f=0.3` | 0.0171 | **0.0049** | 0.9044 | 0.0008 |
| `200970` | **Carcinoma in situ of Prostate** | Oncology / Pre-Malignant | `d=10, l=5, f=sqrt` | 0.0606 | **0.0047** | 0.9094 | 0.0007 |
| `4110591` | **Small Cell Carcinoma of Lung** | Oncology / Pre-Malignant | `d=14, l=2, f=sqrt` | 0.0201 | **0.0043** | 0.8987 | 0.0008 |
| `201826` | **Type 2 Diabetes Mellitus** | Cardiometabolic | `d=8, l=10, f=sqrt` | 0.0099 | **0.0040** | 0.7429 | 0.0011 |
| `4029498` | **Seizure Disorder** | Neurological / Mental Health | `d=10, l=5, f=0.3` | 0.0125 | **0.0011** | 0.7983 | 0.0003 |
| `75036` | **Localized Osteoarthritis of Hand** | Musculoskeletal | `d=10, l=5, f=sqrt` | 0.0090 | **0.0007** | 0.8305 | 0.0002 |
| `258780` | **Chronic Obstructive Bronchitis (COPD)** | Respiratory / Allergic | `d=10, l=5, f=0.3` | 0.0008 | **0.0004** | 0.3126 | 0.0005 |
