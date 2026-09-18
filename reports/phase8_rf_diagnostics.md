# Phase 8: Random Forest Overfitting & Generalization Diagnostics
**Diagnostic Framework**: Train vs. Out-Of-Bag (OOB) vs. Validation vs. Temporal Test Gaps (Section 8)  

## 1. Generalization Gap Table

| Concept ID | Disease Name | Train AUPRC | OOB AUPRC | Val AUPRC | Test AUPRC | OOB-to-Val Gap | Overfitting Assessment |
|---|---|---|---|---|---|---|---|
| `436096` | **Chronic Pain** | 0.4974 | 0.0114 | 0.4002 | 0.4268 | -0.3888 | **Large Gap** |
| `4120314` | **Hypertriglyceridemia** | 0.6060 | 0.0012 | 0.5139 | 0.3987 | -0.5127 | **Large Gap** |
| `436940` | **Metabolic Syndrome X** | 0.8471 | 0.0012 | 0.3884 | 0.3596 | -0.3872 | **Large Gap** |
| `43530652` | **Chronic Intractable Migraine** | 0.5117 | 0.0116 | 0.4289 | 0.3588 | -0.4172 | **Large Gap** |
| `4214376` | **Hyperglycemia** | 0.7360 | 0.0011 | 0.2865 | 0.2438 | -0.2855 | **Large Gap** |
| `378419` | **Alzheimer's Disease** | 0.3820 | 0.0091 | 0.0861 | 0.1772 | -0.0770 | **Moderate Gap** |
| `316866` | **Essential Hypertension** | 0.3251 | 0.0039 | 0.1877 | 0.1375 | -0.1838 | **Large Gap** |
| `4115276` | **Non-Small Cell Lung Cancer** | 0.1894 | 0.0064 | 0.1520 | 0.0834 | -0.1456 | **Moderate Gap** |
| `380378` | **Epilepsy / Seizure Disorder** | 0.3220 | 0.0010 | 0.0984 | 0.0792 | -0.0974 | **Moderate Gap** |
| `439777` | **Anemia** | 0.1909 | 0.0081 | 0.0711 | 0.0776 | -0.0630 | **Moderate Gap** |
| `4310703` | **Non-Small Cell Carcinoma of Lung, Stage 1** | 0.1882 | 0.0064 | 0.1514 | 0.0708 | -0.1450 | **Moderate Gap** |
| `257012` | **Chronic Sinusitis** | 0.3376 | 0.0052 | 0.0560 | 0.0704 | -0.0508 | **Moderate Gap** |
| `192279` | **Congestive Heart Failure** | 0.7232 | 0.0006 | 0.0324 | 0.0655 | -0.0318 | **Well-Generalizing** |
| `443614` | **Chronic Kidney Disease Stage 1** | 0.7308 | 0.0006 | 0.0366 | 0.0636 | -0.0360 | **Well-Generalizing** |
| `37017023` | **Recurrent Rectal Polyp** | 0.8586 | 0.0020 | 0.0724 | 0.0541 | -0.0704 | **Moderate Gap** |
| `4051466` | **Childhood Asthma** | 0.0878 | 0.0003 | 0.0334 | 0.0518 | -0.0331 | **Well-Generalizing** |
| `37016354` | **Neuropathy due to Type 2 Diabetes** | 0.4525 | 0.0006 | 0.0392 | 0.0479 | -0.0386 | **Well-Generalizing** |
| `80502` | **Osteoporosis** | 0.6206 | 0.0036 | 0.0879 | 0.0450 | -0.0843 | **Moderate Gap** |
| `4285898` | **Polyp of Colon** | 0.2277 | 0.0065 | 0.0271 | 0.0187 | -0.0206 | **Well-Generalizing** |
| `4311629` | **Prediabetes** | 0.2863 | 0.0059 | 0.0211 | 0.0186 | -0.0152 | **Well-Generalizing** |
| `4226121` | **Retinopathy due to Type 2 Diabetes** | 0.4563 | 0.0006 | 0.0263 | 0.0181 | -0.0256 | **Well-Generalizing** |
| `4043241` | **Familial Alzheimer's Disease** | 0.7152 | 0.0009 | 0.0021 | 0.0180 | -0.0012 | **Well-Generalizing** |
| `381316` | **Stroke (Cerebrovascular Accident)** | 0.2759 | 0.0040 | 0.0881 | 0.0178 | -0.0841 | **Moderate Gap** |
| `4229440` | **Chronic Kidney Disease** | 0.4882 | 0.0067 | 0.0426 | 0.0174 | -0.0359 | **Well-Generalizing** |
| `79740` | **Primary Malignant Neoplasm of Colon** | 0.9832 | 0.0009 | 0.0076 | 0.0132 | -0.0067 | **Well-Generalizing** |
| `4079750` | **Osteoarthritis of Knee** | 0.1041 | 0.0014 | 0.0058 | 0.0131 | -0.0044 | **Well-Generalizing** |
| `432867` | **Hyperlipidemia** | 0.3039 | 0.0046 | 0.0105 | 0.0127 | -0.0059 | **Well-Generalizing** |
| `440086` | **Childhood ADHD** | 0.3275 | 0.0003 | 0.0062 | 0.0093 | -0.0058 | **Well-Generalizing** |
| `317576` | **Coronary Arteriosclerosis** | 0.5209 | 0.0048 | 0.0110 | 0.0083 | -0.0062 | **Well-Generalizing** |
| `4079749` | **Osteoarthritis of Hip** | 0.8932 | 0.0005 | 0.0024 | 0.0072 | -0.0019 | **Well-Generalizing** |
| `4180790` | **Malignant Neoplasm of Colon** | 0.9008 | 0.0008 | 0.0164 | 0.0069 | -0.0156 | **Well-Generalizing** |
| `4129902` | **Neoplasm of Prostate** | 0.4563 | 0.0056 | 0.0837 | 0.0065 | -0.0782 | **Moderate Gap** |
| `321042` | **Cardiac Arrest** | 0.4711 | 0.0008 | 0.0018 | 0.0053 | -0.0010 | **Well-Generalizing** |
| `4283893` | **Sinusitis** | 0.3173 | 0.0048 | 0.0064 | 0.0049 | -0.0017 | **Well-Generalizing** |
| `37395648` | **Small Cell Carcinoma of Lung, Stage 1** | 0.3335 | 0.0010 | 0.0171 | 0.0049 | -0.0160 | **Well-Generalizing** |
| `200970` | **Carcinoma in situ of Prostate** | 0.6751 | 0.0044 | 0.0606 | 0.0047 | -0.0562 | **Moderate Gap** |
| `4110591` | **Small Cell Carcinoma of Lung** | 0.6335 | 0.0010 | 0.0201 | 0.0043 | -0.0190 | **Well-Generalizing** |
| `201826` | **Type 2 Diabetes Mellitus** | 0.0401 | 0.0010 | 0.0099 | 0.0040 | -0.0089 | **Well-Generalizing** |
| `4029498` | **Seizure Disorder** | 0.2584 | 0.0005 | 0.0125 | 0.0011 | -0.0119 | **Well-Generalizing** |
| `75036` | **Localized Osteoarthritis of Hand** | 0.5785 | 0.0005 | 0.0090 | 0.0007 | -0.0084 | **Well-Generalizing** |
| `258780` | **Chronic Obstructive Bronchitis (COPD)** | 0.6101 | 0.0007 | 0.0008 | 0.0004 | -0.0001 | **Well-Generalizing** |
