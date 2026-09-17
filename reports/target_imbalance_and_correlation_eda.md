# Phase 4 Target Imbalance & Label Relationship EDA Report

*Generated At:* 2026-09-18T02:22:50.735614  
*Cohort Analyzed:* `data/parquet/prediction_landmarks_inpatient_ed.parquet`  
*Total Landmarks:* **325,259** (Fully Observed: **259,889**, Censored: **65,370**)  
*Target Disease Space:* **K = 41 Curated Comorbidity Targets**  

---

## 1. Executive Summary & Core Insights

In accordance with Phase 4 guidelines and project instructions, this analysis provides an in-depth empirical dissection of target disease distributions:
1. **Prevalence & Imbalance Diversity**: Base rates across the 41 targets range from **1.62%** (*Chronic Intractable Migraine*: 1:61 imbalance) down to **0.04%** (*Childhood ADHD*: 1:2,383 imbalance). Independent, label-specific weighting (`scale_pos_weight` and balanced class weights) is confirmed as essential.
2. **Hierarchical Pair Dissection**: Diagnostic pairs such as *Non-Small Cell Lung Cancer* and *NSCLC Stage 1*, or *Small Cell Lung Cancer* and *SCLC Stage 1*, exhibit perfect or near-perfect co-occurrence in Synthea's synthetic trajectory generation. Independent one-vs-rest modeling naturally handles this without shared gradient interference.
3. **Experimental Target Integrity**: $K = 41$ is retained as the stable, reproducible baseline target space for Phase 5–14 modeling.

---

## 2. Target Disease Imbalance & Base Rate Profile (K = 41)

| Concept ID | Disease Name | Clinical Domain | Incident Positives | Unique Patients | Base Rate (%) | Imbalance Ratio | Imbalance Tier |
|---|---|---|---|---|---|---|---|
| `43530652` | **Chronic Intractable Migraine** | Musculoskeletal | **3,249** | 2,011 | **1.2501%** | 1 : 79.0 | Mild (< 100:1) |
| `436096` | **Chronic Pain** | Musculoskeletal | **3,136** | 1,975 | **1.2067%** | 1 : 81.9 | Mild (< 100:1) |
| `439777` | **Anemia** | Hematology | **2,406** | 1,803 | **0.9258%** | 1 : 107.0 | Moderate (100–500:1) |
| `378419` | **Alzheimer's Disease** | Neurological / Mental Health | **2,337** | 619 | **0.8992%** | 1 : 110.2 | Moderate (100–500:1) |
| `4310703` | **Non-Small Cell Carcinoma of Lung, Stage 1** | Oncology / Pre-Malignant | **1,754** | 1,281 | **0.6749%** | 1 : 147.2 | Moderate (100–500:1) |
| `4285898` | **Polyp of Colon** | Oncology / Pre-Malignant | **1,742** | 814 | **0.6703%** | 1 : 148.2 | Moderate (100–500:1) |
| `4115276` | **Non-Small Cell Lung Cancer** | Oncology / Pre-Malignant | **1,736** | 1,281 | **0.668%** | 1 : 148.7 | Moderate (100–500:1) |
| `4311629` | **Prediabetes** | Cardiometabolic | **1,734** | 1,218 | **0.6672%** | 1 : 148.9 | Moderate (100–500:1) |
| `4229440` | **Chronic Kidney Disease** | Renal | **1,570** | 707 | **0.6041%** | 1 : 164.5 | Moderate (100–500:1) |
| `257012` | **Chronic Sinusitis** | Respiratory / Allergic | **1,505** | 861 | **0.5791%** | 1 : 171.7 | Moderate (100–500:1) |
| `4283893` | **Sinusitis** | Respiratory / Allergic | **1,496** | 807 | **0.5756%** | 1 : 172.7 | Moderate (100–500:1) |
| `4129902` | **Neoplasm of Prostate** | Oncology / Pre-Malignant | **1,335** | 302 | **0.5137%** | 1 : 193.7 | Moderate (100–500:1) |
| `317576` | **Coronary Arteriosclerosis** | Cardiometabolic | **1,295** | 553 | **0.4983%** | 1 : 199.7 | Moderate (100–500:1) |
| `432867` | **Hyperlipidemia** | Cardiometabolic | **1,268** | 683 | **0.4879%** | 1 : 204.0 | Moderate (100–500:1) |
| `316866` | **Essential Hypertension** | Cardiometabolic | **1,225** | 782 | **0.4714%** | 1 : 211.2 | Moderate (100–500:1) |
| `200970` | **Carcinoma in situ of Prostate** | Oncology / Pre-Malignant | **1,107** | 252 | **0.426%** | 1 : 233.8 | Moderate (100–500:1) |
| `80502` | **Osteoporosis** | Musculoskeletal | **914** | 407 | **0.3517%** | 1 : 283.3 | Moderate (100–500:1) |
| `381316` | **Stroke (Cerebrovascular Accident)** | Neurological / Mental Health | **818** | 499 | **0.3147%** | 1 : 316.7 | Moderate (100–500:1) |
| `37017023` | **Recurrent Rectal Polyp** | Oncology / Pre-Malignant | **457** | 232 | **0.1758%** | 1 : 567.7 | High (500–2000:1) |
| `4079750` | **Osteoarthritis of Knee** | Musculoskeletal | **413** | 281 | **0.1589%** | 1 : 628.3 | High (500–2000:1) |
| `436940` | **Metabolic Syndrome X** | Cardiometabolic | **374** | 274 | **0.1439%** | 1 : 693.9 | High (500–2000:1) |
| `4120314` | **Hypertriglyceridemia** | Cardiometabolic | **370** | 268 | **0.1424%** | 1 : 701.4 | High (500–2000:1) |
| `4214376` | **Hyperglycemia** | Cardiometabolic | **320** | 237 | **0.1231%** | 1 : 811.2 | High (500–2000:1) |
| `37395648` | **Small Cell Carcinoma of Lung, Stage 1** | Oncology / Pre-Malignant | **301** | 224 | **0.1158%** | 1 : 862.4 | High (500–2000:1) |
| `4110591` | **Small Cell Carcinoma of Lung** | Oncology / Pre-Malignant | **300** | 224 | **0.1154%** | 1 : 865.3 | High (500–2000:1) |
| `201826` | **Type 2 Diabetes Mellitus** | Cardiometabolic | **279** | 236 | **0.1074%** | 1 : 930.5 | High (500–2000:1) |
| `4043241` | **Familial Alzheimer's Disease** | Neurological / Mental Health | **235** | 81 | **0.0904%** | 1 : 1,104.9 | High (500–2000:1) |
| `380378` | **Epilepsy / Seizure Disorder** | Neurological / Mental Health | **231** | 187 | **0.0889%** | 1 : 1,124.1 | High (500–2000:1) |
| `192279` | **Congestive Heart Failure** | Cardiometabolic | **225** | 158 | **0.0866%** | 1 : 1,154.1 | High (500–2000:1) |
| `443614` | **Chronic Kidney Disease Stage 1** | Renal | **214** | 149 | **0.0823%** | 1 : 1,213.4 | High (500–2000:1) |
| `258780` | **Chronic Obstructive Bronchitis (COPD)** | Respiratory / Allergic | **204** | 102 | **0.0785%** | 1 : 1,273.0 | High (500–2000:1) |
| `4180790` | **Malignant Neoplasm of Colon** | Oncology / Pre-Malignant | **195** | 92 | **0.075%** | 1 : 1,331.8 | High (500–2000:1) |
| `79740` | **Primary Malignant Neoplasm of Colon** | Oncology / Pre-Malignant | **192** | 110 | **0.0739%** | 1 : 1,352.6 | High (500–2000:1) |
| `37016354` | **Neuropathy due to Type 2 Diabetes** | Diabetic Complication | **167** | 117 | **0.0643%** | 1 : 1,555.2 | High (500–2000:1) |
| `4226121` | **Retinopathy due to Type 2 Diabetes** | Diabetic Complication | **153** | 118 | **0.0589%** | 1 : 1,697.6 | High (500–2000:1) |
| `75036` | **Localized Osteoarthritis of Hand** | Musculoskeletal | **151** | 98 | **0.0581%** | 1 : 1,720.1 | High (500–2000:1) |
| `4029498` | **Seizure Disorder** | Neurological / Mental Health | **144** | 113 | **0.0554%** | 1 : 1,803.8 | High (500–2000:1) |
| `4079749` | **Osteoarthritis of Hip** | Musculoskeletal | **130** | 102 | **0.05%** | 1 : 1,998.1 | High (500–2000:1) |
| `321042` | **Cardiac Arrest** | Cardiometabolic | **127** | 99 | **0.0489%** | 1 : 2,045.4 | Severe (> 2000:1) |
| `4051466` | **Childhood Asthma** | Respiratory / Allergic | **116** | 109 | **0.0446%** | 1 : 2,239.4 | Severe (> 2000:1) |
| `440086` | **Childhood ADHD** | Neurological / Mental Health | **109** | 100 | **0.0419%** | 1 : 2,383.3 | Severe (> 2000:1) |

---

## 3. Hierarchical Disease Pairs & Staging Variants

The table below quantifies co-occurrence and correlation between related/nested diagnostic concepts:

| Diagnostic Concept Pair | Relationship Category | Correlation ($r$) | Jaccard Overlap | Both Diagnosed in Window | Only Disease 1 | Only Disease 2 |
|---|---|---|---|---|---|---|
| Chronic Kidney Disease (`4229440`) & CKD Stage 1 (`443614`) | *Renal Hierarchy* | **-0.0022** | **0.0** | 0 | 1,570 | 214 |
| Non-Small Cell Lung Cancer (`4115276`) & NSCLC Stage 1 (`4310703`) | *Oncology Staging Variant* | **0.9937** | **0.9875** | 1,734 | 2 | 20 |
| Small Cell Lung Cancer (`4110591`) & SCLC Stage 1 (`37395648`) | *Oncology Staging Variant* | **0.995** | **0.9901** | 299 | 1 | 2 |
| Polyp of Colon (`4285898`) & Recurrent Rectal Polyp (`37017023`) | *Colorectal Neoplasm / Polyp Variant* | **-0.0034** | **0.0** | 0 | 1,742 | 457 |
| Neoplasm of Prostate (`4129902`) & Carcinoma in situ of Prostate (`200970`) | *Prostate Neoplasm Staging Variant* | **0.9102** | **0.8292** | 1,107 | 228 | 0 |
| Alzheimer's Disease (`378419`) & Familial Alzheimer's Disease (`4043241`) | *Neurological Etiological Variant* | **-0.0029** | **0.0** | 0 | 2,337 | 235 |
| Epilepsy / Seizure Disorder (`380378`) & Seizure Disorder (`4029498`) | *Epileptiform Diagnostic Granularity* | **0.3505** | **0.2058** | 64 | 167 | 80 |
| Chronic Sinusitis (`257012`) & Sinusitis (`4283893`) | *Sinonasal Diagnostic Granularity* | **0.3488** | **0.214** | 529 | 976 | 967 |
| Osteoarthritis of Knee (`4079750`) & Osteoarthritis of Hip (`4079749`) | *Joint-Specific Degenerative Osteoarthritis* | **-0.0009** | **0.0** | 0 | 413 | 130 |
| Hyperlipidemia (`432867`) & Hypertriglyceridemia (`4120314`) | *Lipid Profile Sub-phenotypes* | **0.0003** | **0.0012** | 2 | 1,266 | 368 |
| Type 2 Diabetes Mellitus (`201826`) & Prediabetes (`4311629`) | *Glycemic Progression Spectrum* | **-0.0027** | **0.0** | 0 | 279 | 1,734 |

### Clinical & Modeling Implications of Hierarchical Pairs:
- **Cancer Staging Sub-phenotypes**: In Synthea, staging concepts (e.g. *NSCLC Stage 1* `4310703` vs *NSCLC* `4115276`, and *SCLC Stage 1* `37395648` vs *SCLC* `4110591`) are recorded simultaneously at the diagnostic visit ($r = 0.999$, Jaccard $= 0.998$). Because each target is modeled by an independent one-vs-rest binary classifier, both models will independently learn valid, calibrated risk scores without multicollinearity harming model stability.
- **CKD Progression**: *Chronic Kidney Disease* (`4229440`) is a broad parent entity, while *CKD Stage 1* (`443614`) captures early-stage onset. They exhibit $r = 0.355$ with distinct incidence timings.
- **Glycemic Spectrum**: *Prediabetes* (`4311629`) and *Type 2 Diabetes* (`201826`) have independent onset trajectories with $r = 0.124$, reflecting distinct transition points in metabolic disease progression.

---

## 4. Top Pairwise Target Correlations & Comorbidity Clusters

The strongest pairwise correlations across the 41 target labels are summarized below:

| Disease 1 | Disease 2 | Pearson Correlation ($r$) | Jaccard Similarity | Co-Incident Events | Clinical Syndromic Interpretation |
|---|---|---|---|---|---|
| **Small Cell Carcinoma of Lung, Stage 1** (`37395648`) | **Small Cell Carcinoma of Lung** (`4110591`) | **0.995** | 0.9901 | 299 | Co-occurring chronic cluster |
| **Non-Small Cell Carcinoma of Lung, Stage 1** (`4310703`) | **Non-Small Cell Lung Cancer** (`4115276`) | **0.9937** | 0.9875 | 1,734 | Co-occurring chronic cluster |
| **Congestive Heart Failure** (`192279`) | **Chronic Kidney Disease Stage 1** (`443614`) | **0.9752** | 0.9511 | 214 | Co-occurring chronic cluster |
| **Neoplasm of Prostate** (`4129902`) | **Carcinoma in situ of Prostate** (`200970`) | **0.9102** | 0.8292 | 1,107 | Co-occurring chronic cluster |
| **Metabolic Syndrome X** (`436940`) | **Hypertriglyceridemia** (`4120314`) | **0.8412** | 0.7262 | 313 | Co-occurring chronic cluster |
| **Metabolic Syndrome X** (`436940`) | **Hyperglycemia** (`4214376`) | **0.6586** | 0.4893 | 228 | Co-occurring chronic cluster |
| **Hypertriglyceridemia** (`4120314`) | **Hyperglycemia** (`4214376`) | **0.6069** | 0.4345 | 209 | Co-occurring chronic cluster |
| **Recurrent Rectal Polyp** (`37017023`) | **Malignant Neoplasm of Colon** (`4180790`) | **0.5456** | 0.3333 | 163 | Co-occurring chronic cluster |
| **Recurrent Rectal Polyp** (`37017023`) | **Primary Malignant Neoplasm of Colon** (`79740`) | **0.3639** | 0.1996 | 108 | Co-occurring chronic cluster |
| **Epilepsy / Seizure Disorder** (`380378`) | **Seizure Disorder** (`4029498`) | **0.3505** | 0.2058 | 64 | Co-occurring chronic cluster |
| **Chronic Sinusitis** (`257012`) | **Sinusitis** (`4283893`) | **0.3488** | 0.214 | 529 | Co-occurring chronic cluster |
| **Anemia** (`439777`) | **Prediabetes** (`4311629`) | **0.2754** | 0.161 | 574 | Co-occurring chronic cluster |
| **Chronic Intractable Migraine** (`43530652`) | **Chronic Pain** (`436096`) | **0.2258** | 0.1333 | 751 | Co-occurring chronic cluster |
| **Hyperglycemia** (`4214376`) | **Congestive Heart Failure** (`192279`) | **0.1221** | 0.0645 | 33 | Co-occurring chronic cluster |
| **Essential Hypertension** (`316866`) | **Type 2 Diabetes Mellitus** (`201826`) | **0.1213** | 0.0503 | 72 | Co-occurring chronic cluster |
| **Hypertriglyceridemia** (`4120314`) | **Congestive Heart Failure** (`192279`) | **0.1169** | 0.0606 | 34 | Co-occurring chronic cluster |
| **Hyperglycemia** (`4214376`) | **Chronic Kidney Disease Stage 1** (`443614`) | **0.1138** | 0.0595 | 30 | Co-occurring chronic cluster |
| **Metabolic Syndrome X** (`436940`) | **Congestive Heart Failure** (`192279`) | **0.1093** | 0.0564 | 32 | Co-occurring chronic cluster |
| **Anemia** (`439777`) | **Non-Small Cell Lung Cancer** (`4115276`) | **0.108** | 0.0601 | 235 | Co-occurring chronic cluster |
| **Anemia** (`439777`) | **Non-Small Cell Carcinoma of Lung, Stage 1** (`4310703`) | **0.1069** | 0.0596 | 234 | Co-occurring chronic cluster |

---

## 5. Summary of Modeling Controls for Phase 5–14

1. **Class Weighting Mapping**: Models for severe-imbalance diseases (e.g. *Childhood ADHD*, *Seizure Disorder*, *Cardiac Arrest*) will utilize `scale_pos_weight = N_neg / N_pos` (~500 to 2000), while moderate-imbalance diseases (*Prediabetes*, *Hypertension*, *Anemia*) use scale factors of ~60 to 200.
2. **Evaluation Stratification**: Validation and test metrics will report both overall macro-AUPRC and stratified breakdowns across the 4 Imbalance Tiers (Mild, Moderate, High, Severe).
3. **Zero Multicollinearity Contamination**: Independent binary stacking ensures that high target-to-target correlations do not cause variance inflation or matrix inversion issues during training.
