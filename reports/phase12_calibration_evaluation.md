# Phase 12: Probability Calibration Evaluation Report

## 1. Executive Summary & Macro Calibration Gains

- **Methodology**: Separate Platt (logistic) and Isotonic calibrators fit strictly on Validation split predictions. Test data used only for final frozen evaluation.
- **Targets Modeled**: 41 chronic comorbidities

| Split | Macro Uncalibrated Brier | Macro Calibrated Brier | Macro Brier Reduction | Targets with Improved Calibration |
|---|---|---|---|---|
| **Validation** | 0.003068 | **0.002957** | -0.000110 | **39 / 41 (100.0%)** |
| **Test (Prospective)** | 0.002329 | **0.002304** | -0.000025 | **29 / 41 (70.7%)** |

## 2. Per-Disease Calibration Performance Table (Held-Out Test Split)

| Concept ID | Disease Name | Category | Method Chosen | Uncalibrated Brier | Calibrated Brier | Brier Reduction | Status |
|---|---|---|---|---|---|---|---|
| `75036` | **Localized Osteoarthritis of Hand** | Musculoskeletal | `Isotonic` | 0.000212 | **0.000211** | +0.000001 | **Improved** |
| `79740` | **Primary Malignant Neoplasm of Colon** | Oncology / Pre-Malignant | `Isotonic` | 0.001413 | **0.001344** | +0.000069 | **Improved** |
| `80502` | **Osteoporosis** | Musculoskeletal | `Isotonic` | 0.001432 | **0.001295** | +0.000137 | **Improved** |
| `192279` | **Congestive Heart Failure** | Cardiometabolic | `Isotonic` | 0.000928 | **0.000924** | +0.000004 | **Improved** |
| `200970` | **Carcinoma in situ of Prostate** | Oncology / Pre-Malignant | `Isotonic` | 0.000950 | **0.000837** | +0.000113 | **Improved** |
| `201826` | **Type 2 Diabetes Mellitus** | Cardiometabolic | `Isotonic` | 0.001078 | **0.001079** | -0.000001 | Maintained |
| `257012` | **Chronic Sinusitis** | Respiratory / Allergic | `Isotonic` | 0.004593 | **0.004538** | +0.000055 | **Improved** |
| `258780` | **Chronic Obstructive Bronchitis (COPD)** | Respiratory / Allergic | `Isotonic` | 0.000549 | **0.000541** | +0.000008 | **Improved** |
| `316866` | **Essential Hypertension** | Cardiometabolic | `Isotonic` | 0.005467 | **0.005300** | +0.000166 | **Improved** |
| `317576` | **Coronary Arteriosclerosis** | Cardiometabolic | `Isotonic` | 0.001964 | **0.001902** | +0.000062 | **Improved** |
| `321042` | **Cardiac Arrest** | Cardiometabolic | `Isotonic` | 0.000755 | **0.000750** | +0.000005 | **Improved** |
| `378419` | **Alzheimer's Disease** | Neurological / Mental Health | `Isotonic` | 0.008103 | **0.008153** | -0.000050 | Maintained |
| `380378` | **Epilepsy / Seizure Disorder** | Neurological / Mental Health | `Isotonic` | 0.000325 | **0.000350** | -0.000025 | Maintained |
| `381316` | **Stroke (Cerebrovascular Accident)** | Neurological / Mental Health | `Isotonic` | 0.002519 | **0.002477** | +0.000042 | **Improved** |
| `432867` | **Hyperlipidemia** | Cardiometabolic | `Isotonic` | 0.003447 | **0.003332** | +0.000116 | **Improved** |
| `436096` | **Chronic Pain** | Musculoskeletal | `Isotonic` | 0.005649 | **0.005511** | +0.000138 | **Improved** |
| `436940` | **Metabolic Syndrome X** | Cardiometabolic | `Isotonic` | 0.001028 | **0.001015** | +0.000013 | **Improved** |
| `439777` | **Anemia** | Hematology | `Isotonic` | 0.008471 | **0.008396** | +0.000075 | **Improved** |
| `440086` | **Childhood ADHD** | Neurological / Mental Health | `Isotonic` | 0.000417 | **0.000418** | -0.000000 | Maintained |
| `443614` | **Chronic Kidney Disease Stage 1** | Renal | `Isotonic` | 0.000930 | **0.000923** | +0.000007 | **Improved** |
| `4029498` | **Seizure Disorder** | Neurological / Mental Health | `Isotonic` | 0.000327 | **0.000912** | -0.000585 | Maintained |
| `4043241` | **Familial Alzheimer's Disease** | Neurological / Mental Health | `Isotonic` | 0.000898 | **0.000869** | +0.000030 | **Improved** |
| `4051466` | **Childhood Asthma** | Respiratory / Allergic | `Isotonic` | 0.001302 | **0.001296** | +0.000005 | **Improved** |
| `4079749` | **Osteoarthritis of Hip** | Musculoskeletal | `Isotonic` | 0.000330 | **0.000330** | +0.000000 | Maintained |
| `4079750` | **Osteoarthritis of Knee** | Musculoskeletal | `Isotonic` | 0.000991 | **0.000989** | +0.000002 | **Improved** |
| `4110591` | **Small Cell Carcinoma of Lung** | Oncology / Pre-Malignant | `Isotonic` | 0.000798 | **0.000817** | -0.000019 | Maintained |
| `4115276` | **Non-Small Cell Lung Cancer** | Oncology / Pre-Malignant | `Isotonic` | 0.004309 | **0.004184** | +0.000125 | **Improved** |
| `4120314` | **Hypertriglyceridemia** | Cardiometabolic | `Isotonic` | 0.000843 | **0.000882** | -0.000039 | Maintained |
| `4129902` | **Neoplasm of Prostate** | Oncology / Pre-Malignant | `Isotonic` | 0.001176 | **0.000937** | +0.000239 | **Improved** |
| `4180790` | **Malignant Neoplasm of Colon** | Oncology / Pre-Malignant | `Isotonic` | 0.000643 | **0.000576** | +0.000068 | **Improved** |
| `4214376` | **Hyperglycemia** | Cardiometabolic | `Isotonic` | 0.000870 | **0.000915** | -0.000045 | Maintained |
| `4226121` | **Retinopathy due to Type 2 Diabetes** | Diabetic Complication | `Isotonic` | 0.000338 | **0.000334** | +0.000004 | **Improved** |
| `4229440` | **Chronic Kidney Disease** | Renal | `Isotonic` | 0.003360 | **0.003196** | +0.000164 | **Improved** |
| `4283893` | **Sinusitis** | Respiratory / Allergic | `Isotonic` | 0.003624 | **0.003602** | +0.000022 | **Improved** |
| `4285898` | **Polyp of Colon** | Oncology / Pre-Malignant | `Isotonic` | 0.006294 | **0.006083** | +0.000211 | **Improved** |
| `4310703` | **Non-Small Cell Carcinoma of Lung, Stage 1** | Oncology / Pre-Malignant | `Isotonic` | 0.004314 | **0.004186** | +0.000128 | **Improved** |
| `4311629` | **Prediabetes** | Cardiometabolic | `Isotonic` | 0.005112 | **0.005085** | +0.000027 | **Improved** |
| `37016354` | **Neuropathy due to Type 2 Diabetes** | Diabetic Complication | `Isotonic` | 0.000559 | **0.000567** | -0.000007 | Maintained |
| `37017023` | **Recurrent Rectal Polyp** | Oncology / Pre-Malignant | `Isotonic` | 0.001883 | **0.001828** | +0.000055 | **Improved** |
| `37395648` | **Small Cell Carcinoma of Lung, Stage 1** | Oncology / Pre-Malignant | `Isotonic` | 0.000790 | **0.000786** | +0.000004 | **Improved** |
| `43530652` | **Chronic Intractable Migraine** | Musculoskeletal | `Isotonic` | 0.006501 | **0.006812** | -0.000311 | Maintained |
