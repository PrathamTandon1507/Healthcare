# Phase 5: Train / Validation / Test Split Characteristics & Validation Audit
**Status**: Complete and Verified  
**Temporal Holdout Cutoff**: `2016-01-01`  
**Train/Val Split Ratio**: `70/30` (Deterministic Seed: `42`)  
**Patient Partitioning**: Strict patient-level disjointness (0% patient overlap across all split pairs)  

---

## 1. Splitting Methodology & Leakage Protection

In accordance with **Section 6** of `COMORBIDITY_ENSEMBLE_ML_PLAN.md`:
1. **Unit of Splitting**: Splitting is executed strictly at the **patient level (`person_id`)**, never row-level. A patient appears in exactly one of Train, Validation, or Test across their entire longitudinal history.
2. **Prospective Temporal Holdout (`test`)**: Patients whose majority of landmarks occur on or after `2016-01-01` are assigned to the prospective temporal test set (spanning 2016-01-01 to dataset end 2019-05-17). This provides an authentic prospective evaluation of temporal generalization.
3. **Historical Split (`train` & `val`)**: Patients with the majority of their landmarks prior to `2016-01-01` are assigned to the training pool, randomly partitioned into **Train (70%)** and **Validation (30%)** using deterministic hashing.
4. **Multi-Snapshot Boundary Handling (Minority Row Dropping)**: To prevent temporal leakage across the cutoff date for multi-snapshot patients, rows occurring on the minority side of the temporal cutoff are excluded from model training/testing rather than split across boundaries.

---

## 2. Cohort A (Inpatient & ED Encounters) Split Overview

| Split | Patients | % of Patients | Landmarks | % of Retained Landmarks | Min Date | Max Date | Mean Age | Male LM | Female LM |
|---|---|---|---|---|---|---|---|---|---|
| **Train** | 44,661 | 55.5% | 174,660 | 61.97% | 1910-02-08 | 2015-12-31 | 51.02 | 99,812 | 74,848 |
| **Val** | 19,106 | 23.74% | 73,862 | 26.21% | 1910-04-23 | 2015-12-31 | 51.21 | 41,694 | 32,168 |
| **Test** | 16,700 | 20.75% | 33,304 | 11.82% | 2016-01-01 | 2019-05-17 | 42.05 | 15,848 | 17,456 |

- **Raw Eligible Landmarks**: 325,259 across 80,467 patients
- **Retained Landmarks**: 281,826 (Dropped minority boundary rows: 43,433)
- **Patient Overlap across splits**: **0** (Strictly disjoint)

---

## 3. Cohort B (General Encounters) Split Overview

| Split | Patients | % of Patients | Landmarks | % of Retained Landmarks | Min Date | Max Date | Mean Age | Male LM | Female LM |
|---|---|---|---|---|---|---|---|---|---|
| **Train** | 69,537 | 60.35% | 1,651,678 | 63.63% | 1909-10-28 | 2015-12-31 | 47.62 | 764,103 | 887,575 |
| **Val** | 29,659 | 25.74% | 718,546 | 27.68% | 1909-09-09 | 2015-12-31 | 48.42 | 329,930 | 388,616 |
| **Test** | 16,027 | 13.91% | 225,727 | 8.7% | 2016-01-01 | 2019-05-20 | 27.61 | 81,864 | 143,863 |

- **Raw Eligible Landmarks**: 3,364,928 across 115,223 patients
- **Retained Landmarks**: 2,595,951 (Dropped minority boundary rows: 768,977)
- **Patient Overlap across splits**: **0** (Strictly disjoint)

---

## 4. Target Disease Incidence Across Splits (Cohort A - Inpatient/ED)

Verification of positive label counts and class balance across Train, Validation, and Test for all $K = 41$ modeled comorbidity targets:

| Concept ID | Clinical Name | Category | Train Pos (%) | Val Pos (%) | Test Pos (%) |
|---|---|---|---|---|---|
| `192279` | **Congestive Heart Failure** | Cardiometabolic | 103 (0.06%) | 71 (0.10%) | 32 (0.10%) |
| `200970` | **Carcinoma in situ of Prostate** | Oncology / Pre-Malignant | 766 (0.44%) | 409 (0.55%) | 23 (0.07%) |
| `201826` | **Type 2 Diabetes Mellitus** | Cardiometabolic | 174 (0.10%) | 71 (0.10%) | 36 (0.11%) |
| `257012` | **Chronic Sinusitis** | Respiratory / Allergic | 907 (0.52%) | 445 (0.60%) | 156 (0.47%) |
| `258780` | **Chronic Obstructive Bronchitis (COPD)** | Respiratory / Allergic | 118 (0.07%) | 64 (0.09%) | 18 (0.05%) |
| `316866` | **Essential Hypertension** | Cardiometabolic | 678 (0.39%) | 279 (0.38%) | 196 (0.59%) |
| `317576` | **Coronary Arteriosclerosis** | Cardiometabolic | 839 (0.48%) | 367 (0.50%) | 63 (0.19%) |
| `321042` | **Cardiac Arrest** | Cardiometabolic | 137 (0.08%) | 57 (0.08%) | 25 (0.08%) |
| `37016354` | **Neuropathy due to Type 2 Diabetes** | Diabetic Complication | 98 (0.06%) | 55 (0.07%) | 19 (0.06%) |
| `37017023` | **Recurrent Rectal Polyp** | Oncology / Pre-Malignant | 343 (0.20%) | 103 (0.14%) | 61 (0.18%) |
| `37395648` | **Small Cell Carcinoma of Lung, Stage 1** | Oncology / Pre-Malignant | 181 (0.10%) | 88 (0.12%) | 26 (0.08%) |
| `378419` | **Alzheimer's Disease** | Neurological / Mental Health | 1,591 (0.91%) | 566 (0.77%) | 279 (0.84%) |
| `380378` | **Epilepsy / Seizure Disorder** | Neurological / Mental Health | 175 (0.10%) | 58 (0.08%) | 9 (0.03%) |
| `381316` | **Stroke (Cerebrovascular Accident)** | Neurological / Mental Health | 703 (0.40%) | 303 (0.41%) | 83 (0.25%) |
| `4029498` | **Seizure Disorder** | Neurological / Mental Health | 92 (0.05%) | 55 (0.07%) | 10 (0.03%) |
| `4043241` | **Familial Alzheimer's Disease** | Neurological / Mental Health | 164 (0.09%) | 30 (0.04%) | 29 (0.09%) |
| `4051466` | **Childhood Asthma** | Respiratory / Allergic | 47 (0.03%) | 26 (0.04%) | 45 (0.14%) |
| `4079749` | **Osteoarthritis of Hip** | Musculoskeletal | 87 (0.05%) | 29 (0.04%) | 11 (0.03%) |
| `4079750` | **Osteoarthritis of Knee** | Musculoskeletal | 252 (0.14%) | 139 (0.19%) | 33 (0.10%) |
| `4110591` | **Small Cell Carcinoma of Lung** | Oncology / Pre-Malignant | 181 (0.10%) | 87 (0.12%) | 26 (0.08%) |
| `4115276` | **Non-Small Cell Lung Cancer** | Oncology / Pre-Malignant | 1,114 (0.64%) | 462 (0.63%) | 136 (0.41%) |
| `4120314` | **Hypertriglyceridemia** | Cardiometabolic | 210 (0.12%) | 88 (0.12%) | 42 (0.13%) |
| `4129902` | **Neoplasm of Prostate** | Oncology / Pre-Malignant | 973 (0.56%) | 457 (0.62%) | 25 (0.08%) |
| `4180790` | **Malignant Neoplasm of Colon** | Oncology / Pre-Malignant | 142 (0.08%) | 46 (0.06%) | 19 (0.06%) |
| `4214376` | **Hyperglycemia** | Cardiometabolic | 185 (0.11%) | 79 (0.11%) | 35 (0.11%) |
| `4226121` | **Retinopathy due to Type 2 Diabetes** | Diabetic Complication | 108 (0.06%) | 53 (0.07%) | 11 (0.03%) |
| `4229440` | **Chronic Kidney Disease** | Renal | 1,177 (0.67%) | 496 (0.67%) | 106 (0.32%) |
| `4283893` | **Sinusitis** | Respiratory / Allergic | 831 (0.48%) | 461 (0.62%) | 120 (0.36%) |
| `4285898` | **Polyp of Colon** | Oncology / Pre-Malignant | 1,139 (0.65%) | 505 (0.68%) | 207 (0.62%) |
| `4310703` | **Non-Small Cell Carcinoma of Lung, Stage 1** | Oncology / Pre-Malignant | 1,126 (0.64%) | 467 (0.63%) | 136 (0.41%) |
| `4311629` | **Prediabetes** | Cardiometabolic | 1,029 (0.59%) | 440 (0.60%) | 172 (0.52%) |
| `432867` | **Hyperlipidemia** | Cardiometabolic | 802 (0.46%) | 309 (0.42%) | 112 (0.34%) |
| `43530652` | **Chronic Intractable Migraine** | Musculoskeletal | 2,034 (1.16%) | 852 (1.15%) | 295 (0.89%) |
| `436096` | **Chronic Pain** | Musculoskeletal | 1,983 (1.14%) | 871 (1.18%) | 281 (0.84%) |
| `436940` | **Metabolic Syndrome X** | Cardiometabolic | 210 (0.12%) | 90 (0.12%) | 48 (0.14%) |
| `439777` | **Anemia** | Hematology | 1,423 (0.81%) | 592 (0.80%) | 293 (0.88%) |
| `440086` | **Childhood ADHD** | Neurological / Mental Health | 61 (0.03%) | 15 (0.02%) | 14 (0.04%) |
| `443614` | **Chronic Kidney Disease Stage 1** | Renal | 96 (0.06%) | 69 (0.09%) | 32 (0.10%) |
| `75036` | **Localized Osteoarthritis of Hand** | Musculoskeletal | 91 (0.05%) | 51 (0.07%) | 7 (0.02%) |
| `79740` | **Primary Malignant Neoplasm of Colon** | Oncology / Pre-Malignant | 153 (0.09%) | 44 (0.06%) | 45 (0.14%) |
| `80502` | **Osteoporosis** | Musculoskeletal | 636 (0.36%) | 225 (0.30%) | 44 (0.13%) |

---

## 5. Summary & Readiness for Base Model Training

- **Patient Isolation**: Verified 0 patient overlap across Train, Validation, and Test.
- **Temporal Integrity**: All test landmarks occur $\ge 2016-01-01$, and all train/val landmarks occur $< 2016-01-01$.
- **Target Distribution**: Target positive rates remain highly stable between Train and Validation folds (confirming random split fidelity), while exhibiting realistic clinical drift on the prospective temporal Test set.
- **Next Step**: Proceed to **Phase 6: Baseline Models & Evaluation Metric Harness** (`src/models/baseline.py`, `src/models/metrics.py`).
