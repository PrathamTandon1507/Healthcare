# Empirical Disease Incidence & Target Space Curation Report

*Generated At:* 2026-09-18T02:15:40.895066  
*Specification:* `COMORBIDITY_ENSEMBLE_ML_PLAN.md` (Sections 1.4, 8)  

---

## 1. Methodological & Numerical Reconciliations

Before final target space curation, three numerical transitions between exploratory Phase 2 profiling and strict Phase 3 prediction cohort materialization are documented:

1. **$144 \rightarrow 143$ Distinct Condition Concepts**:
   - In the raw `condition_occurrence` table, 144 distinct `condition_concept_id` values exist, including concept `0` (`No matching concept` / unmapped source strings).
   - Concept `0` represents unmapped administrative or free-text diagnoses without semantic clinical definitions. In accordance with OMOP standards and our multi-label prediction formulation, concept `0` is excluded from the modeled target space, leaving exactly **143 valid clinical condition concepts**.

2. **$325,359 \rightarrow 325,259$ Cohort A (Inpatient / ED) Landmarks ($\Delta = 100$)**:
   - In preliminary Phase 2 exploratory profiling, any visit row with $\ge 1$ condition occurrence row in history (including concept `0`) was counted as 325,359.
   - Under strict Phase 3 eligibility enforcement requiring $\ge 1$ *valid, non-zero* distinct condition concept diagnosed on or before $T$, exactly 100 landmarks whose only historical condition was concept `0` were excluded, yielding **325,259 fully eligible landmarks**.

3. **$3,365,062 \rightarrow 3,364,928$ Cohort B (General) Landmarks ($\Delta = 134$)**:
   - Identical resolution on the general encounter cohort: 134 landmarks had only concept `0` in their pre-landmark history and were excluded under strict eligibility, yielding **3,364,928 eligible landmarks**.


---

## 2. Clinical Target Space Curation Rationale

A core requirement of the **Comorbidity Network + Prediction Tool** is that the target prediction space $K$ must represent **genuine future comorbidities** (chronic, progressive, or recurring disease entities) rather than acute, transient events or administrative artifacts.

Selection was performed using **both** statistical incidence and clinical suitability:

- **Statistical Threshold**: $\ge 100$ incident positive landmarks in Cohort A (and $\ge 50$ unique incident patients) to ensure robust sample sizes for 5-fold cross-validation (at least $\ge 20$ positive events per validation fold).
- **Clinical Exclusion Criteria**:
  1. **Acute / Transient Infections**: Self-limiting upper respiratory and localized infections (e.g. *Viral sinusitis*, *Acute bronchitis*, *Streptococcal sore throat*, *Acute viral pharyngitis*, *Otitis media*, *Acute cystitis*, *Appendicitis*).
  2. **Acute Mechanical Trauma & Injuries**: Accidental fractures, sprains, lacerations, burns, whiplash, and accidental poisonings (e.g. *Rib fracture*, *Ankle sprain*, *Wrist sprain*, *Lacerations*, *Burn injuries*, *Concussions*).
  3. **Obstetric & Normal Pregnancy**: Physiologic status codes and pregnancy complications (e.g. *Normal pregnancy*, *Miscarriage*, *Tubal pregnancy*, *Pre-eclampsia*).
  4. **Administrative & Non-Disease Findings**: Screening and non-pathological status codes (e.g. *Normal BMI*, *Suspected condition*, *Postoperative state*).

### Target Selection Summary (Cohort A — Inpatient / ED)
- **Total OMOP Condition Concepts Evaluated**: **143**
- **Statistically Qualifying Concepts ($\ge 100$ positives)**: **86**
- **Curated Chronic Comorbidity Targets**: **42 diseases** (Retained for ML modeling)
- **Excluded Acute / Non-Comorbid Conditions**: **44 conditions** (Filtered out)


---

## 3. Curated Comorbidity Target Space (K = 42 Diseases)

| Concept ID | Disease Name | Clinical Domain | Pre-existing at $T$ | At-Risk Landmarks | Incident Positive Events | Unique Patients | Incidence Rate (%) |
|---|---|---|---|---|---|---|---|
| `4311629` | **Prediabetes** | Cardiometabolic | 93,931 | 165,958 | **1,734** | **1,218** | **1.045%** |
| `317576` | **Coronary Arteriosclerosis** | Cardiometabolic | 19,475 | 240,414 | **1,295** | **553** | **0.539%** |
| `432867` | **Hyperlipidemia** | Cardiometabolic | 35,130 | 224,759 | **1,268** | **683** | **0.564%** |
| `316866` | **Essential Hypertension** | Cardiometabolic | 81,227 | 178,662 | **1,225** | **782** | **0.686%** |
| `436940` | **Metabolic Syndrome X** | Cardiometabolic | 49,058 | 210,831 | **374** | **274** | **0.177%** |
| `4120314` | **Hypertriglyceridemia** | Cardiometabolic | 49,307 | 210,582 | **370** | **268** | **0.176%** |
| `4214376` | **Hyperglycemia** | Cardiometabolic | 36,713 | 223,176 | **320** | **237** | **0.143%** |
| `201826` | **Type 2 Diabetes Mellitus** | Cardiometabolic | 50,116 | 209,773 | **279** | **236** | **0.133%** |
| `192279` | **Congestive Heart Failure** | Cardiometabolic | 41,163 | 218,726 | **225** | **158** | **0.103%** |
| `321042` | **Cardiac Arrest** | Cardiometabolic | 12,175 | 247,714 | **127** | **99** | **0.051%** |
| `37016354` | **Neuropathy due to Type 2 Diabetes** | Diabetic Complication | 20,628 | 239,261 | **167** | **117** | **0.07%** |
| `4226121` | **Retinopathy due to Type 2 Diabetes** | Diabetic Complication | 15,652 | 244,237 | **153** | **118** | **0.063%** |
| `439777` | **Anemia** | Hematology | 103,382 | 156,507 | **2,406** | **1,803** | **1.537%** |
| `43530652` | **Chronic Intractable Migraine** | Musculoskeletal | 59,694 | 200,195 | **3,249** | **2,011** | **1.623%** |
| `436096` | **Chronic Pain** | Musculoskeletal | 59,975 | 199,914 | **3,136** | **1,975** | **1.569%** |
| `80502` | **Osteoporosis** | Musculoskeletal | 18,532 | 241,357 | **914** | **407** | **0.379%** |
| `4079750` | **Osteoarthritis of Knee** | Musculoskeletal | 15,228 | 244,661 | **413** | **281** | **0.169%** |
| `75036` | **Localized Osteoarthritis of Hand** | Musculoskeletal | 6,104 | 253,785 | **151** | **98** | **0.059%** |
| `4079749` | **Osteoarthritis of Hip** | Musculoskeletal | 6,333 | 253,556 | **130** | **102** | **0.051%** |
| `378419` | **Alzheimer's Disease** | Neurological / Mental Health | 19,873 | 240,016 | **2,337** | **619** | **0.974%** |
| `381316` | **Stroke (Cerebrovascular Accident)** | Neurological / Mental Health | 19,841 | 240,048 | **818** | **499** | **0.341%** |
| `4043241` | **Familial Alzheimer's Disease** | Neurological / Mental Health | 2,807 | 257,082 | **235** | **81** | **0.091%** |
| `380378` | **Epilepsy / Seizure Disorder** | Neurological / Mental Health | 5,169 | 254,720 | **231** | **187** | **0.091%** |
| `4029498` | **Seizure Disorder** | Neurological / Mental Health | 9,778 | 250,111 | **144** | **113** | **0.058%** |
| `440086` | **Childhood ADHD** | Neurological / Mental Health | 2,054 | 257,835 | **109** | **100** | **0.042%** |
| `4310703` | **Non-Small Cell Carcinoma of Lung, Stage 1** | Oncology / Pre-Malignant | 37,731 | 222,158 | **1,754** | **1,281** | **0.79%** |
| `4285898` | **Polyp of Colon** | Oncology / Pre-Malignant | 17,632 | 242,257 | **1,742** | **814** | **0.719%** |
| `4115276` | **Non-Small Cell Lung Cancer** | Oncology / Pre-Malignant | 37,751 | 222,138 | **1,736** | **1,281** | **0.781%** |
| `4129902` | **Neoplasm of Prostate** | Oncology / Pre-Malignant | 25,872 | 234,017 | **1,335** | **302** | **0.57%** |
| `200970` | **Carcinoma in situ of Prostate** | Oncology / Pre-Malignant | 25,448 | 234,441 | **1,107** | **252** | **0.472%** |
| `37017023` | **Recurrent Rectal Polyp** | Oncology / Pre-Malignant | 5,735 | 254,154 | **457** | **232** | **0.18%** |
| `37395648` | **Small Cell Carcinoma of Lung, Stage 1** | Oncology / Pre-Malignant | 8,324 | 251,565 | **301** | **224** | **0.12%** |
| `4110591` | **Small Cell Carcinoma of Lung** | Oncology / Pre-Malignant | 8,326 | 251,563 | **300** | **224** | **0.119%** |
| `4180790` | **Malignant Neoplasm of Colon** | Oncology / Pre-Malignant | 1,516 | 258,373 | **195** | **92** | **0.075%** |
| `79740` | **Primary Malignant Neoplasm of Colon** | Oncology / Pre-Malignant | 1,422 | 258,467 | **192** | **110** | **0.074%** |
| `197500` | **Primary Malignant Neoplasm of Colon** | Oncology / Pre-Malignant | 672 | 259,217 | **107** | **41** | **0.041%** |
| `4229440` | **Chronic Kidney Disease** | Renal | 4,247 | 255,642 | **1,570** | **707** | **0.614%** |
| `443614` | **Chronic Kidney Disease Stage 1** | Renal | 37,800 | 222,089 | **214** | **149** | **0.096%** |
| `257012` | **Chronic Sinusitis** | Respiratory / Allergic | 61,983 | 197,906 | **1,505** | **861** | **0.76%** |
| `4283893` | **Sinusitis** | Respiratory / Allergic | 8,453 | 251,436 | **1,496** | **807** | **0.595%** |
| `258780` | **Chronic Obstructive Bronchitis (COPD)** | Respiratory / Allergic | 3,770 | 256,119 | **204** | **102** | **0.08%** |
| `4051466` | **Childhood Asthma** | Respiratory / Allergic | 5,456 | 254,433 | **116** | **109** | **0.046%** |

---

## 4. Excluded Qualifying Conditions with Clinical Rationales (N = 44)

| Concept ID | Condition Name | Clinical Category | Incident Positives | Unique Patients | Primary Clinical Exclusion Rationale |
|---|---|---|---|---|---|
| `40481087` | Viral Sinusitis | *Acute Infection* | 14,035 | 8,731 | Acute transient infection; self-limiting, not a chronic comorbidity |
| `4112343` | Normal Body Mass Index | *Administrative / Finding* | 10,063 | 6,134 | Non-disease screening finding or administrative status code |
| `260139` | Acute Bronchitis | *Acute Infection* | 8,860 | 5,393 | Acute transient infection; self-limiting, not a chronic comorbidity |
| `4055754` | Fracture of Rib | *Acute Injury / Trauma* | 3,121 | 1,965 | Acute mechanical trauma / accidental injury; not a chronic comorbidity |
| `28060` | Normal Pregnancy | *Obstetric / Pregnancy* | 2,807 | 1,770 | Obstetric / pregnancy-related physiological condition |
| `4217975` | Normal Pregnancy | *Obstetric / Pregnancy* | 2,361 | 1,573 | Obstetric / pregnancy-related physiological condition |
| `81151` | Sprain of Ankle | *Acute Injury / Trauma* | 1,768 | 974 | Acute mechanical trauma / accidental injury; not a chronic comorbidity |
| `4208104` | Drug Overdose | *Acute Injury / Trauma* | 1,728 | 870 | Acute mechanical trauma / accidental injury; not a chronic comorbidity |
| `4294548` | Acute Viral Pharyngitis | *Acute Infection* | 1,535 | 894 | Acute transient infection; self-limiting, not a chronic comorbidity |
| `372328` | Otitis Media | *Acute Infection* | 1,088 | 848 | Acute transient infection; self-limiting, not a chronic comorbidity |
| `4078393` | Miscarriage (Spontaneous Abortion) | *Obstetric / Pregnancy* | 1,040 | 810 | Obstetric / pregnancy-related physiological condition |
| `378001` | Concussion Injury | *Acute Injury / Trauma* | 1,035 | 585 | Acute mechanical trauma / accidental injury; not a chronic comorbidity |
| `313217` | Suspected Respiratory Finding | *Administrative / Finding* | 978 | 380 | Non-disease screening finding or administrative status code |
| `4218389` | Whiplash Injury to Neck | *Acute Injury / Trauma* | 875 | 504 | Acute mechanical trauma / accidental injury; not a chronic comorbidity |
| `4278672` | Fracture of Forearm | *Acute Injury / Trauma* | 852 | 371 | Acute mechanical trauma / accidental injury; not a chronic comorbidity |
| `40318618` | Complete Miscarriage | *Obstetric / Pregnancy* | 837 | 641 | Obstetric / pregnancy-related physiological condition |
| `78272` | Sprain of Wrist | *Acute Injury / Trauma* | 728 | 436 | Acute mechanical trauma / accidental injury; not a chronic comorbidity |
| `4237458` | Fracture of Upper Limb | *Acute Injury / Trauma* | 717 | 330 | Acute mechanical trauma / accidental injury; not a chronic comorbidity |
| `4109685` | Laceration of Foot | *Acute Injury / Trauma* | 708 | 334 | Acute mechanical trauma / accidental injury; not a chronic comorbidity |
| `4059173` | Fracture of Ankle | *Acute Injury / Trauma* | 704 | 284 | Acute mechanical trauma / accidental injury; not a chronic comorbidity |
| `4116491` | Infectious Process | *Acute Infection* | 685 | 482 | Acute transient infection; self-limiting, not a chronic comorbidity |
| `40480160` | Burn Injury | *Acute Injury / Trauma* | 668 | 208 | Acute mechanical trauma / accidental injury; not a chronic comorbidity |
| `4155034` | Laceration of Forearm | *Acute Injury / Trauma* | 654 | 311 | Acute mechanical trauma / accidental injury; not a chronic comorbidity |
| `4113008` | Laceration of Hand | *Acute Injury / Trauma* | 641 | 322 | Acute mechanical trauma / accidental injury; not a chronic comorbidity |
| `4156265` | Facial Laceration | *Acute Injury / Trauma* | 630 | 310 | Acute mechanical trauma / accidental injury; not a chronic comorbidity |
| `4134304` | Acute Upper Respiratory Infection | *Acute Infection* | 576 | 289 | Acute transient infection; self-limiting, not a chronic comorbidity |
| `4152936` | Laceration of Thigh | *Acute Injury / Trauma* | 573 | 313 | Acute mechanical trauma / accidental injury; not a chronic comorbidity |
| `4296204` | First Degree Burn | *Acute Injury / Trauma* | 475 | 248 | Acute mechanical trauma / accidental injury; not a chronic comorbidity |
| `195588` | Cystitis (Urinary Tract Infection) | *Acute Infection* | 445 | 320 | Acute transient infection; self-limiting, not a chronic comorbidity |
| `439393` | Pre-Eclampsia | *Obstetric / Pregnancy* | 391 | 288 | Obstetric / pregnancy-related physiological condition |
| `4262136` | Drug Overdose / Poisoning | *Acute Injury / Trauma* | 376 | 287 | Acute mechanical trauma / accidental injury; not a chronic comorbidity |
| `4196262` | Suicidal Deliberate Poisoning | *Acute Injury / Trauma* | 376 | 90 | Acute mechanical trauma / accidental injury; not a chronic comorbidity |
| `261325` | Suspected Condition | *Administrative / Finding* | 372 | 220 | Non-disease screening finding or administrative status code |
| `4142905` | Fracture of Clavicle | *Acute Injury / Trauma* | 367 | 151 | Acute mechanical trauma / accidental injury; not a chronic comorbidity |
| `137613` | Eclampsia in Pregnancy | *Obstetric / Pregnancy* | 352 | 272 | Obstetric / pregnancy-related physiological condition |
| `4296205` | Second Degree Burn | *Acute Injury / Trauma* | 337 | 156 | Acute mechanical trauma / accidental injury; not a chronic comorbidity |
| `4230399` | Closed Fracture of Wrist | *Acute Injury / Trauma* | 320 | 129 | Acute mechanical trauma / accidental injury; not a chronic comorbidity |
| `375671` | Concussion with Loss of Consciousness | *Acute Injury / Trauma* | 287 | 162 | Acute mechanical trauma / accidental injury; not a chronic comorbidity |
| `199076` | Tubal Pregnancy | *Obstetric / Pregnancy* | 261 | 215 | Obstetric / pregnancy-related physiological condition |
| `4146173` | Postoperative State | *Administrative / Finding* | 258 | 144 | Non-disease screening finding or administrative status code |
| `4084167` | Acute Allergic Reaction | *Respiratory / Allergic* | 210 | 149 | Non-chronic condition unsuitable for comorbidity network prediction |
| `440448` | Appendicitis | *Acute Infection* | 186 | 141 | Acute transient infection; self-limiting, not a chronic comorbidity |
| `40479422` | Second Degree Burn | *Acute Injury / Trauma* | 119 | 70 | Acute mechanical trauma / accidental injury; not a chronic comorbidity |
| `4149245` | Rupture of Patellar Tendon | *Acute Injury / Trauma* | 109 | 59 | Acute mechanical trauma / accidental injury; not a chronic comorbidity |

---

## 5. Complete Empirical Incidence Table: All 143 Evaluated Condition Concepts

For full research transparency, the complete empirical distribution across all 143 candidate concepts in Cohort A is presented below:

| Concept ID | Condition Name | Domain | Status | Pre-existing at $T$ | At-Risk Landmarks | Incident Positives | Unique Patients | Incidence Rate (%) |
|---|---|---|---|---|---|---|---|---|
| `40481087` | Viral Sinusitis | Acute Infection | Excluded (Acute/Trauma/Obs) | 99,892 | 159,997 | 14,035 | 8,731 | 8.772% |
| `4112343` | Normal Body Mass Index | Administrative / Finding | Excluded (Acute/Trauma/Obs) | 62,482 | 197,407 | 10,063 | 6,134 | 5.098% |
| `260139` | Acute Bronchitis | Acute Infection | Excluded (Acute/Trauma/Obs) | 54,230 | 205,659 | 8,860 | 5,393 | 4.308% |
| `43530652` | Chronic Intractable Migraine | Musculoskeletal | 🎯 **Curated Target** | 59,694 | 200,195 | 3,249 | 2,011 | 1.623% |
| `436096` | Chronic Pain | Musculoskeletal | 🎯 **Curated Target** | 59,975 | 199,914 | 3,136 | 1,975 | 1.569% |
| `4055754` | Fracture of Rib | Acute Injury / Trauma | Excluded (Acute/Trauma/Obs) | 59,735 | 200,154 | 3,121 | 1,965 | 1.559% |
| `28060` | Normal Pregnancy | Obstetric / Pregnancy | Excluded (Acute/Trauma/Obs) | 16,329 | 243,560 | 2,807 | 1,770 | 1.152% |
| `439777` | Anemia | Hematology | 🎯 **Curated Target** | 103,382 | 156,507 | 2,406 | 1,803 | 1.537% |
| `4217975` | Normal Pregnancy | Obstetric / Pregnancy | Excluded (Acute/Trauma/Obs) | 44,090 | 215,799 | 2,361 | 1,573 | 1.094% |
| `378419` | Alzheimer's Disease | Neurological / Mental Health | 🎯 **Curated Target** | 19,873 | 240,016 | 2,337 | 619 | 0.974% |
| `81151` | Sprain of Ankle | Acute Injury / Trauma | Excluded (Acute/Trauma/Obs) | 21,719 | 238,170 | 1,768 | 974 | 0.742% |
| `4310703` | Non-Small Cell Carcinoma of Lung, Stage 1 | Oncology / Pre-Malignant | 🎯 **Curated Target** | 37,731 | 222,158 | 1,754 | 1,281 | 0.79% |
| `4285898` | Polyp of Colon | Oncology / Pre-Malignant | 🎯 **Curated Target** | 17,632 | 242,257 | 1,742 | 814 | 0.719% |
| `4115276` | Non-Small Cell Lung Cancer | Oncology / Pre-Malignant | 🎯 **Curated Target** | 37,751 | 222,138 | 1,736 | 1,281 | 0.781% |
| `4311629` | Prediabetes | Cardiometabolic | 🎯 **Curated Target** | 93,931 | 165,958 | 1,734 | 1,218 | 1.045% |
| `4208104` | Drug Overdose | Acute Injury / Trauma | Excluded (Acute/Trauma/Obs) | 36,831 | 223,058 | 1,728 | 870 | 0.775% |
| `4229440` | Chronic Kidney Disease | Renal | 🎯 **Curated Target** | 4,247 | 255,642 | 1,570 | 707 | 0.614% |
| `4294548` | Acute Viral Pharyngitis | Acute Infection | Excluded (Acute/Trauma/Obs) | 8,694 | 251,195 | 1,535 | 894 | 0.611% |
| `257012` | Chronic Sinusitis | Respiratory / Allergic | 🎯 **Curated Target** | 61,983 | 197,906 | 1,505 | 861 | 0.76% |
| `4283893` | Sinusitis | Respiratory / Allergic | 🎯 **Curated Target** | 8,453 | 251,436 | 1,496 | 807 | 0.595% |
| `4129902` | Neoplasm of Prostate | Oncology / Pre-Malignant | 🎯 **Curated Target** | 25,872 | 234,017 | 1,335 | 302 | 0.57% |
| `317576` | Coronary Arteriosclerosis | Cardiometabolic | 🎯 **Curated Target** | 19,475 | 240,414 | 1,295 | 553 | 0.539% |
| `432867` | Hyperlipidemia | Cardiometabolic | 🎯 **Curated Target** | 35,130 | 224,759 | 1,268 | 683 | 0.564% |
| `316866` | Essential Hypertension | Cardiometabolic | 🎯 **Curated Target** | 81,227 | 178,662 | 1,225 | 782 | 0.686% |
| `200970` | Carcinoma in situ of Prostate | Oncology / Pre-Malignant | 🎯 **Curated Target** | 25,448 | 234,441 | 1,107 | 252 | 0.472% |
| `372328` | Otitis Media | Acute Infection | Excluded (Acute/Trauma/Obs) | 8,948 | 250,941 | 1,088 | 848 | 0.434% |
| `4078393` | Miscarriage (Spontaneous Abortion) | Obstetric / Pregnancy | Excluded (Acute/Trauma/Obs) | 42,793 | 217,096 | 1,040 | 810 | 0.479% |
| `378001` | Concussion Injury | Acute Injury / Trauma | Excluded (Acute/Trauma/Obs) | 12,627 | 247,262 | 1,035 | 585 | 0.419% |
| `313217` | Suspected Respiratory Finding | Administrative / Finding | Excluded (Acute/Trauma/Obs) | 14,440 | 245,449 | 978 | 380 | 0.398% |
| `80502` | Osteoporosis | Musculoskeletal | 🎯 **Curated Target** | 18,532 | 241,357 | 914 | 407 | 0.379% |
| `4218389` | Whiplash Injury to Neck | Acute Injury / Trauma | Excluded (Acute/Trauma/Obs) | 10,130 | 249,759 | 875 | 504 | 0.35% |
| `4278672` | Fracture of Forearm | Acute Injury / Trauma | Excluded (Acute/Trauma/Obs) | 9,885 | 250,004 | 852 | 371 | 0.341% |
| `40318618` | Complete Miscarriage | Obstetric / Pregnancy | Excluded (Acute/Trauma/Obs) | 4,252 | 255,637 | 837 | 641 | 0.327% |
| `381316` | Stroke (Cerebrovascular Accident) | Neurological / Mental Health | 🎯 **Curated Target** | 19,841 | 240,048 | 818 | 499 | 0.341% |
| `78272` | Sprain of Wrist | Acute Injury / Trauma | Excluded (Acute/Trauma/Obs) | 9,534 | 250,355 | 728 | 436 | 0.291% |
| `4237458` | Fracture of Upper Limb | Acute Injury / Trauma | Excluded (Acute/Trauma/Obs) | 7,424 | 252,465 | 717 | 330 | 0.284% |
| `4109685` | Laceration of Foot | Acute Injury / Trauma | Excluded (Acute/Trauma/Obs) | 6,675 | 253,214 | 708 | 334 | 0.28% |
| `4059173` | Fracture of Ankle | Acute Injury / Trauma | Excluded (Acute/Trauma/Obs) | 6,910 | 252,979 | 704 | 284 | 0.278% |
| `4116491` | Infectious Process | Acute Infection | Excluded (Acute/Trauma/Obs) | 3,316 | 256,573 | 685 | 482 | 0.267% |
| `40480160` | Burn Injury | Acute Injury / Trauma | Excluded (Acute/Trauma/Obs) | 5,255 | 254,634 | 668 | 208 | 0.262% |
| `4155034` | Laceration of Forearm | Acute Injury / Trauma | Excluded (Acute/Trauma/Obs) | 5,889 | 254,000 | 654 | 311 | 0.257% |
| `4113008` | Laceration of Hand | Acute Injury / Trauma | Excluded (Acute/Trauma/Obs) | 6,585 | 253,304 | 641 | 322 | 0.253% |
| `4156265` | Facial Laceration | Acute Injury / Trauma | Excluded (Acute/Trauma/Obs) | 6,496 | 253,393 | 630 | 310 | 0.249% |
| `4134304` | Acute Upper Respiratory Infection | Acute Infection | Excluded (Acute/Trauma/Obs) | 6,699 | 253,190 | 576 | 289 | 0.227% |
| `4152936` | Laceration of Thigh | Acute Injury / Trauma | Excluded (Acute/Trauma/Obs) | 6,473 | 253,416 | 573 | 313 | 0.226% |
| `4296204` | First Degree Burn | Acute Injury / Trauma | Excluded (Acute/Trauma/Obs) | 5,058 | 254,831 | 475 | 248 | 0.186% |
| `37017023` | Recurrent Rectal Polyp | Oncology / Pre-Malignant | 🎯 **Curated Target** | 5,735 | 254,154 | 457 | 232 | 0.18% |
| `195588` | Cystitis (Urinary Tract Infection) | Acute Infection | Excluded (Acute/Trauma/Obs) | 2,552 | 257,337 | 445 | 320 | 0.173% |
| `4079750` | Osteoarthritis of Knee | Musculoskeletal | 🎯 **Curated Target** | 15,228 | 244,661 | 413 | 281 | 0.169% |
| `439393` | Pre-Eclampsia | Obstetric / Pregnancy | Excluded (Acute/Trauma/Obs) | 4,130 | 255,759 | 391 | 288 | 0.153% |
| `4262136` | Drug Overdose / Poisoning | Acute Injury / Trauma | Excluded (Acute/Trauma/Obs) | 1,917 | 257,972 | 376 | 287 | 0.146% |
| `4196262` | Suicidal Deliberate Poisoning | Acute Injury / Trauma | Excluded (Acute/Trauma/Obs) | 790 | 259,099 | 376 | 90 | 0.145% |
| `436940` | Metabolic Syndrome X | Cardiometabolic | 🎯 **Curated Target** | 49,058 | 210,831 | 374 | 274 | 0.177% |
| `261325` | Suspected Condition | Administrative / Finding | Excluded (Acute/Trauma/Obs) | 5,459 | 254,430 | 372 | 220 | 0.146% |
| `4120314` | Hypertriglyceridemia | Cardiometabolic | 🎯 **Curated Target** | 49,307 | 210,582 | 370 | 268 | 0.176% |
| `4142905` | Fracture of Clavicle | Acute Injury / Trauma | Excluded (Acute/Trauma/Obs) | 3,471 | 256,418 | 367 | 151 | 0.143% |
| `137613` | Eclampsia in Pregnancy | Obstetric / Pregnancy | Excluded (Acute/Trauma/Obs) | 4,445 | 255,444 | 352 | 272 | 0.138% |
| `4296205` | Second Degree Burn | Acute Injury / Trauma | Excluded (Acute/Trauma/Obs) | 3,331 | 256,558 | 337 | 156 | 0.131% |
| `4214376` | Hyperglycemia | Cardiometabolic | 🎯 **Curated Target** | 36,713 | 223,176 | 320 | 237 | 0.143% |
| `4230399` | Closed Fracture of Wrist | Acute Injury / Trauma | Excluded (Acute/Trauma/Obs) | 2,618 | 257,271 | 320 | 129 | 0.124% |
| `37395648` | Small Cell Carcinoma of Lung, Stage 1 | Oncology / Pre-Malignant | 🎯 **Curated Target** | 8,324 | 251,565 | 301 | 224 | 0.12% |
| `4110591` | Small Cell Carcinoma of Lung | Oncology / Pre-Malignant | 🎯 **Curated Target** | 8,326 | 251,563 | 300 | 224 | 0.119% |
| `375671` | Concussion with Loss of Consciousness | Acute Injury / Trauma | Excluded (Acute/Trauma/Obs) | 3,330 | 256,559 | 287 | 162 | 0.112% |
| `201826` | Type 2 Diabetes Mellitus | Cardiometabolic | 🎯 **Curated Target** | 50,116 | 209,773 | 279 | 236 | 0.133% |
| `199076` | Tubal Pregnancy | Obstetric / Pregnancy | Excluded (Acute/Trauma/Obs) | 6,026 | 253,863 | 261 | 215 | 0.103% |
| `4146173` | Postoperative State | Administrative / Finding | Excluded (Acute/Trauma/Obs) | 1,743 | 258,146 | 258 | 144 | 0.1% |
| `4043241` | Familial Alzheimer's Disease | Neurological / Mental Health | 🎯 **Curated Target** | 2,807 | 257,082 | 235 | 81 | 0.091% |
| `380378` | Epilepsy / Seizure Disorder | Neurological / Mental Health | 🎯 **Curated Target** | 5,169 | 254,720 | 231 | 187 | 0.091% |
| `192279` | Congestive Heart Failure | Cardiometabolic | 🎯 **Curated Target** | 41,163 | 218,726 | 225 | 158 | 0.103% |
| `443614` | Chronic Kidney Disease Stage 1 | Renal | 🎯 **Curated Target** | 37,800 | 222,089 | 214 | 149 | 0.096% |
| `4084167` | Acute Allergic Reaction | Respiratory / Allergic | Excluded (Acute/Trauma/Obs) | 2,518 | 257,371 | 210 | 149 | 0.082% |
| `258780` | Chronic Obstructive Bronchitis (COPD) | Respiratory / Allergic | 🎯 **Curated Target** | 3,770 | 256,119 | 204 | 102 | 0.08% |
| `4180790` | Malignant Neoplasm of Colon | Oncology / Pre-Malignant | 🎯 **Curated Target** | 1,516 | 258,373 | 195 | 92 | 0.075% |
| `79740` | Primary Malignant Neoplasm of Colon | Oncology / Pre-Malignant | 🎯 **Curated Target** | 1,422 | 258,467 | 192 | 110 | 0.074% |
| `440448` | Appendicitis | Acute Infection | Excluded (Acute/Trauma/Obs) | 20,560 | 239,329 | 186 | 141 | 0.078% |
| `37016354` | Neuropathy due to Type 2 Diabetes | Diabetic Complication | 🎯 **Curated Target** | 20,628 | 239,261 | 167 | 117 | 0.07% |
| `4226121` | Retinopathy due to Type 2 Diabetes | Diabetic Complication | 🎯 **Curated Target** | 15,652 | 244,237 | 153 | 118 | 0.063% |
| `75036` | Localized Osteoarthritis of Hand | Musculoskeletal | 🎯 **Curated Target** | 6,104 | 253,785 | 151 | 98 | 0.059% |
| `4029498` | Seizure Disorder | Neurological / Mental Health | 🎯 **Curated Target** | 9,778 | 250,111 | 144 | 113 | 0.058% |
| `4079749` | Osteoarthritis of Hip | Musculoskeletal | 🎯 **Curated Target** | 6,333 | 253,556 | 130 | 102 | 0.051% |
| `321042` | Cardiac Arrest | Cardiometabolic | 🎯 **Curated Target** | 12,175 | 247,714 | 127 | 99 | 0.051% |
| `40479422` | Second Degree Burn | Acute Injury / Trauma | Excluded (Acute/Trauma/Obs) | 2,566 | 257,323 | 119 | 70 | 0.046% |
| `4051466` | Childhood Asthma | Respiratory / Allergic | 🎯 **Curated Target** | 5,456 | 254,433 | 116 | 109 | 0.046% |
| `440086` | Childhood ADHD | Neurological / Mental Health | 🎯 **Curated Target** | 2,054 | 257,835 | 109 | 100 | 0.042% |
| `4149245` | Rupture of Patellar Tendon | Acute Injury / Trauma | Excluded (Acute/Trauma/Obs) | 1,770 | 258,119 | 109 | 59 | 0.042% |
| `197500` | Primary Malignant Neoplasm of Colon | Oncology / Pre-Malignant | 🎯 **Curated Target** | 672 | 259,217 | 107 | 41 | 0.041% |
| `40486433` | Perennial Allergic Rhinitis | Respiratory / Allergic | Excluded (<100 Positives) | 6,318 | 253,571 | 99 | 92 | 0.039% |
| `4048171` | Childhood Asthma Exacerbation / Peritonitis | Respiratory / Allergic | Excluded (<100 Positives) | 6,606 | 253,283 | 93 | 87 | 0.037% |
| `134438` | Contact Dermatitis | Administrative / Finding | Excluded (<100 Positives) | 551 | 259,338 | 88 | 80 | 0.034% |
| `40479768` | Injury of Anterior Cruciate Ligament | Acute Injury / Trauma | Excluded (<100 Positives) | 1,481 | 258,408 | 86 | 54 | 0.033% |
| `45769905` | Microalbuminuria due to Type 2 Diabetes | Diabetic Complication | Excluded (<100 Positives) | 13,158 | 246,731 | 83 | 54 | 0.034% |
| `43530656` | Nonproliferative Retinopathy due to Type 2 Diabetes | Diabetic Complication | Excluded (<100 Positives) | 9,113 | 250,776 | 79 | 66 | 0.032% |
| `255848` | Pneumonia | Acute Infection | Excluded (<100 Positives) | 113 | 259,776 | 78 | 16 | 0.03% |
| `4309027` | Hypothyroidism | Cardiometabolic | Excluded (<100 Positives) | 1,622 | 258,267 | 75 | 44 | 0.029% |
| `4035415` | Tear of Meniscus of Knee | Acute Injury / Trauma | Excluded (<100 Positives) | 1,034 | 258,855 | 73 | 47 | 0.028% |
| `4166224` | Ruptured Appendix | Acute Infection | Excluded (<100 Positives) | 6,418 | 253,471 | 73 | 41 | 0.029% |
| `4001336` | Concussion Injury of Brain | Acute Injury / Trauma | Excluded (<100 Positives) | 733 | 259,156 | 71 | 37 | 0.027% |
| `4094814` | Postoperative Finding | Administrative / Finding | Excluded (<100 Positives) | 580 | 259,309 | 62 | 36 | 0.024% |
| `4341247` | Protracted Diarrhea | Acute Infection | Excluded (<100 Positives) | 916 | 258,973 | 60 | 41 | 0.023% |
| `4245614` | Bleeding from Anus | Administrative / Finding | Excluded (<100 Positives) | 916 | 258,973 | 60 | 41 | 0.023% |
| `4329847` | Myocardial Infarction | Cardiometabolic | Excluded (<100 Positives) | 1,603 | 258,286 | 59 | 49 | 0.023% |
| `80809` | Rheumatoid Arthritis | Musculoskeletal | Excluded (<100 Positives) | 817 | 259,072 | 58 | 17 | 0.022% |
| `443601` | Chronic Kidney Disease Stage 1 | Renal | Excluded (<100 Positives) | 11,287 | 248,602 | 55 | 41 | 0.022% |
| `43530685` | Proliferative Retinopathy due to Type 2 Diabetes | Diabetic Complication | Excluded (<100 Positives) | 2,577 | 257,312 | 55 | 29 | 0.021% |
| `4280726` | Seasonal Allergic Rhinitis | Respiratory / Allergic | Excluded (<100 Positives) | 3,179 | 256,710 | 54 | 52 | 0.021% |
| `196456` | Gallbladder Calculus (Gallstone) | Acute Infection | Excluded (<100 Positives) | 426 | 259,463 | 53 | 30 | 0.02% |
| `198809` | Acute Cholecystitis | Acute Infection | Excluded (<100 Positives) | 426 | 259,463 | 53 | 30 | 0.02% |
| `133834` | Atopic Dermatitis / Eczema | Respiratory / Allergic | Excluded (<100 Positives) | 3,864 | 256,025 | 51 | 43 | 0.02% |
| `440674` | Gout | Cardiometabolic | Excluded (<100 Positives) | 3,726 | 256,163 | 50 | 36 | 0.02% |
| `4056621` | Recurrent Urinary Tract Infection | Renal | Excluded (<100 Positives) | 2,601 | 257,288 | 49 | 45 | 0.019% |
| `436676` | Posttraumatic Stress Disorder | Neurological / Mental Health | Excluded (<100 Positives) | 210 | 259,679 | 44 | 14 | 0.017% |
| `4311765` | Secondary Malignant Neoplasm of Colon | Oncology / Pre-Malignant | Excluded (<100 Positives) | 175 | 259,714 | 43 | 31 | 0.017% |
| `45757499` | Proteinuria due to Type 2 Diabetes | Diabetic Complication | Excluded (<100 Positives) | 3,360 | 256,529 | 36 | 19 | 0.014% |
| `443597` | Chronic Kidney Disease Stage 2 | Renal | Excluded (<100 Positives) | 3,184 | 256,705 | 36 | 19 | 0.014% |
| `4218106` | Alcoholism / Alcohol Dependence | Cardiometabolic | Excluded (<100 Positives) | 8,238 | 251,651 | 28 | 19 | 0.011% |
| `438130` | Opioid Abuse / Harmful Use | Cardiometabolic | Excluded (<100 Positives) | 6,941 | 252,948 | 28 | 13 | 0.011% |
| `4316217` | Fibromyalgia Syndrome | Neurological / Mental Health | Excluded (<100 Positives) | 2,352 | 257,537 | 26 | 21 | 0.01% |
| `45770830` | Macular Edema due to Type 2 Diabetes | Diabetic Complication | Excluded (<100 Positives) | 3,145 | 256,744 | 24 | 21 | 0.009% |
| `4299128` | Third Degree Burn | Acute Injury / Trauma | Excluded (<100 Positives) | 343 | 259,546 | 21 | 16 | 0.008% |
| `4166590` | Postoperative State | Administrative / Finding | Excluded (<100 Positives) | 2,437 | 257,452 | 19 | 14 | 0.007% |
| `198199` | Pyelonephritis | Acute Infection | Excluded (<100 Positives) | 89 | 259,800 | 11 | 9 | 0.004% |
| `4152280` | Major Depressive Disorder | Neurological / Mental Health | Excluded (<100 Positives) | 2,525 | 257,364 | 11 | 7 | 0.004% |
| `317009` | Asthma | Respiratory / Allergic | Excluded (<100 Positives) | 393 | 259,496 | 10 | 8 | 0.004% |
| `4048695` | Fracture of Vertebral Column | Acute Injury / Trauma | Excluded (<100 Positives) | 169 | 259,720 | 9 | 8 | 0.003% |
| `4282096` | Major Depression, Single Episode | Neurological / Mental Health | Excluded (<100 Positives) | 22 | 259,867 | 8 | 5 | 0.003% |
| `4066995` | Fracture of Vertebral Column with Spinal Cord Injury | Acute Injury / Trauma | Excluded (<100 Positives) | 29 | 259,860 | 4 | 3 | 0.002% |
| `45763582` | Blindness due to Type 2 Diabetes | Diabetic Complication | Excluded (<100 Positives) | 80 | 259,809 | 4 | 3 | 0.002% |
| `441267` | Cystic Fibrosis | Administrative / Finding | Excluded (<100 Positives) | 56 | 259,833 | 2 | 2 | 0.001% |
| `4144583` | Diabetes Mellitus due to Cystic Fibrosis | Administrative / Finding | Excluded (<100 Positives) | 52 | 259,837 | 2 | 2 | 0.001% |
| `44782520` | Chronic Paralysis due to Spinal Cord Lesion | Neurological / Mental Health | Excluded (<100 Positives) | 422 | 259,467 | 2 | 2 | 0.001% |
| `444362` | Suicidal Poisoning | Acute Injury / Trauma | Excluded (<100 Positives) | 9 | 259,880 | 2 | 1 | 0.001% |
| `45769019` | Female Infertility due to Cystic Fibrosis | Administrative / Finding | Excluded (<100 Positives) | 32 | 259,857 | 1 | 1 | 0.0% |
| `40491961` | Pseudomonas Sepsis | Acute Infection | Excluded (<100 Positives) | 13 | 259,876 | 1 | 1 | 0.0% |
| `4021336` | At Risk for Suicide | Administrative / Finding | Excluded (<100 Positives) | 82 | 259,807 | 1 | 1 | 0.0% |
| `4008261` | Pseudomonas Aeruginosa Infection | Acute Infection | Excluded (<100 Positives) | 20 | 259,869 | 1 | 1 | 0.0% |
| `4188598` | High Risk Pregnancy | Obstetric / Pregnancy | Excluded (<100 Positives) | 22 | 259,867 | 0 | 0 | 0.0% |
| `4132546` | Traumatic Brain Injury | Acute Injury / Trauma | Excluded (<100 Positives) | 264 | 259,625 | 0 | 0 | 0.0% |
| `319049` | Clinical Finding | Administrative / Finding | Excluded (<100 Positives) | 1 | 259,888 | 0 | 0 | 0.0% |
| `433125` | Clinical Finding | Administrative / Finding | Excluded (<100 Positives) | 12 | 259,877 | 0 | 0 | 0.0% |
| `443612` | Chronic Kidney Disease Stage 4 | Renal | Excluded (<100 Positives) | 182 | 259,707 | 0 | 0 | 0.0% |
| `255891` | Clinical Finding | Administrative / Finding | Excluded (<100 Positives) | 7 | 259,882 | 0 | 0 | 0.0% |
| `193591` | Clinical Finding | Administrative / Finding | Excluded (<100 Positives) | 13 | 259,876 | 0 | 0 | 0.0% |
| `40489907` | Staphylococcus Aureus Sepsis | Acute Infection | Excluded (<100 Positives) | 3 | 259,886 | 0 | 0 | 0.0% |