# Phase 11: Frozen Hyperparameter Manifest & Registry Report

## 1. Overview & Discipline

- **Methodological Rule**: All hyperparameters selected strictly using inner-validation and training/validation splits. Zero test data was touched during tuning.
- **Targets Covered**: 41 comorbidity targets
- **Registry File**: `models/configs/frozen_hyperparameters.json`

## 2. Frozen Base Model Configurations

| Concept ID | Disease Name | Category | LR C | RF Depth | RF Min Leaf | RF Max Feat | XGB Depth | XGB LR | XGB L2 |
|---|---|---|---|---|---|---|---|---|---|
| `75036` | **Localized Osteoarthritis of Hand** | Musculoskeletal | `0.01` | `10` | `5` | `sqrt` | `6` | `0.03` | `5.0` |
| `79740` | **Primary Malignant Neoplasm of Colon** | Oncology / Pre-Malignant | `10.0` | `14` | `2` | `sqrt` | `6` | `0.03` | `5.0` |
| `80502` | **Osteoporosis** | Musculoskeletal | `0.01` | `10` | `5` | `0.3` | `6` | `0.05` | `1.0` |
| `192279` | **Congestive Heart Failure** | Cardiometabolic | `0.01` | `10` | `5` | `sqrt` | `4` | `0.05` | `1.0` |
| `200970` | **Carcinoma in situ of Prostate** | Oncology / Pre-Malignant | `0.01` | `10` | `5` | `sqrt` | `8` | `0.03` | `5.0` |
| `201826` | **Type 2 Diabetes Mellitus** | Cardiometabolic | `0.01` | `8` | `10` | `sqrt` | `6` | `0.03` | `5.0` |
| `257012` | **Chronic Sinusitis** | Respiratory / Allergic | `0.01` | `8` | `10` | `sqrt` | `6` | `0.03` | `5.0` |
| `258780` | **Chronic Obstructive Bronchitis (COPD)** | Respiratory / Allergic | `1.0` | `10` | `5` | `0.3` | `8` | `0.03` | `5.0` |
| `316866` | **Essential Hypertension** | Cardiometabolic | `0.01` | `10` | `5` | `0.3` | `6` | `0.05` | `1.0` |
| `317576` | **Coronary Arteriosclerosis** | Cardiometabolic | `0.01` | `10` | `5` | `sqrt` | `4` | `0.05` | `1.0` |
| `321042` | **Cardiac Arrest** | Cardiometabolic | `0.01` | `8` | `10` | `sqrt` | `4` | `0.05` | `1.0` |
| `378419` | **Alzheimer's Disease** | Neurological / Mental Health | `10.0` | `10` | `5` | `0.3` | `6` | `0.03` | `5.0` |
| `380378` | **Epilepsy / Seizure Disorder** | Neurological / Mental Health | `0.01` | `10` | `5` | `sqrt` | `6` | `0.03` | `5.0` |
| `381316` | **Stroke (Cerebrovascular Accident)** | Neurological / Mental Health | `0.01` | `10` | `5` | `0.3` | `8` | `0.03` | `5.0` |
| `432867` | **Hyperlipidemia** | Cardiometabolic | `1.0` | `10` | `5` | `0.3` | `6` | `0.05` | `1.0` |
| `436096` | **Chronic Pain** | Musculoskeletal | `0.01` | `10` | `5` | `0.3` | `6` | `0.03` | `5.0` |
| `436940` | **Metabolic Syndrome X** | Cardiometabolic | `0.01` | `10` | `5` | `0.3` | `4` | `0.05` | `1.0` |
| `439777` | **Anemia** | Hematology | `0.01` | `10` | `5` | `0.3` | `6` | `0.05` | `1.0` |
| `440086` | **Childhood ADHD** | Neurological / Mental Health | `10.0` | `14` | `2` | `sqrt` | `6` | `0.05` | `1.0` |
| `443614` | **Chronic Kidney Disease Stage 1** | Renal | `0.01` | `10` | `5` | `sqrt` | `4` | `0.05` | `1.0` |
| `4029498` | **Seizure Disorder** | Neurological / Mental Health | `0.01` | `10` | `5` | `0.3` | `6` | `0.03` | `5.0` |
| `4043241` | **Familial Alzheimer's Disease** | Neurological / Mental Health | `0.1` | `8` | `10` | `sqrt` | `4` | `0.05` | `1.0` |
| `4051466` | **Childhood Asthma** | Respiratory / Allergic | `1.0` | `10` | `5` | `sqrt` | `6` | `0.03` | `5.0` |
| `4079749` | **Osteoarthritis of Hip** | Musculoskeletal | `0.01` | `14` | `2` | `sqrt` | `6` | `0.03` | `5.0` |
| `4079750` | **Osteoarthritis of Knee** | Musculoskeletal | `0.01` | `8` | `10` | `sqrt` | `4` | `0.05` | `1.0` |
| `4110591` | **Small Cell Carcinoma of Lung** | Oncology / Pre-Malignant | `1.0` | `14` | `2` | `sqrt` | `6` | `0.03` | `5.0` |
| `4115276` | **Non-Small Cell Lung Cancer** | Oncology / Pre-Malignant | `0.01` | `10` | `5` | `0.3` | `6` | `0.03` | `5.0` |
| `4120314` | **Hypertriglyceridemia** | Cardiometabolic | `0.01` | `8` | `10` | `sqrt` | `4` | `0.05` | `1.0` |
| `4129902` | **Neoplasm of Prostate** | Oncology / Pre-Malignant | `0.01` | `8` | `10` | `sqrt` | `8` | `0.03` | `5.0` |
| `4180790` | **Malignant Neoplasm of Colon** | Oncology / Pre-Malignant | `0.1` | `10` | `5` | `0.3` | `6` | `0.05` | `1.0` |
| `4214376` | **Hyperglycemia** | Cardiometabolic | `0.01` | `10` | `5` | `0.3` | `6` | `0.03` | `5.0` |
| `4226121` | **Retinopathy due to Type 2 Diabetes** | Diabetic Complication | `0.01` | `8` | `10` | `sqrt` | `4` | `0.05` | `1.0` |
| `4229440` | **Chronic Kidney Disease** | Renal | `0.01` | `10` | `5` | `sqrt` | `6` | `0.03` | `5.0` |
| `4283893` | **Sinusitis** | Respiratory / Allergic | `0.01` | `8` | `10` | `sqrt` | `4` | `0.05` | `1.0` |
| `4285898` | **Polyp of Colon** | Oncology / Pre-Malignant | `10.0` | `10` | `5` | `0.3` | `4` | `0.05` | `1.0` |
| `4310703` | **Non-Small Cell Carcinoma of Lung, Stage 1** | Oncology / Pre-Malignant | `10.0` | `10` | `5` | `0.3` | `6` | `0.03` | `5.0` |
| `4311629` | **Prediabetes** | Cardiometabolic | `0.01` | `10` | `5` | `0.3` | `8` | `0.03` | `5.0` |
| `37016354` | **Neuropathy due to Type 2 Diabetes** | Diabetic Complication | `0.01` | `8` | `10` | `sqrt` | `8` | `0.03` | `5.0` |
| `37017023` | **Recurrent Rectal Polyp** | Oncology / Pre-Malignant | `0.1` | `10` | `5` | `sqrt` | `6` | `0.03` | `5.0` |
| `37395648` | **Small Cell Carcinoma of Lung, Stage 1** | Oncology / Pre-Malignant | `10.0` | `10` | `5` | `0.3` | `6` | `0.03` | `5.0` |
| `43530652` | **Chronic Intractable Migraine** | Musculoskeletal | `0.01` | `10` | `5` | `0.3` | `4` | `0.05` | `1.0` |
