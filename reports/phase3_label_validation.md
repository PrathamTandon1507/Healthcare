# Phase 3 Manual Label Validation Report

*Generated At:* 2026-09-18T02:16:36.929505  
*Total Manual Audit Cases:* 18  

---

## Summary Table of 18 Audit Cases

| Case # | Category | Patient ID | Landmark Date ($T$) | Future Window ($T, T+365]$ | Pre-existing Conditions at $T$ | Diagnoses in Future Window | Incident Comorbidity Labels ($=1$) | Censored? | Leakage Audit |
|---|---|---|---|---|---|---|---|---|---|
| `1` | Multiple Incident Future Diagnoses | `22598` | `2013-12-05` | `2013-12-05 → 2014-12-05` | 14 conditions | 2 conditions | **1 positive(s)** | No (Complete) | ✅ PASS |
| `2` | Multiple Incident Future Diagnoses | `22598` | `2012-12-16` | `2012-12-16 → 2013-12-16` | 14 conditions | 2 conditions | None (All 0s) | No (Complete) | ✅ PASS |
| `3` | Multiple Incident Future Diagnoses | `22598` | `2012-10-20` | `2012-10-20 → 2013-10-20` | 14 conditions | 2 conditions | None (All 0s) | No (Complete) | ✅ PASS |
| `4` | Multiple Incident Future Diagnoses | `22598` | `2012-04-20` | `2012-04-20 → 2013-04-20` | 14 conditions | 2 conditions | None (All 0s) | No (Complete) | ✅ PASS |
| `5` | Pre-existing Condition Repeated in Future Window | `24157` | `2006-11-03` | `2006-11-03 → 2007-11-03` | 20 conditions | 1 conditions | **1 positive(s)** | No (Complete) | ✅ PASS |
| `6` | Pre-existing Condition Repeated in Future Window | `22598` | `2013-12-05` | `2013-12-05 → 2014-12-05` | 14 conditions | 2 conditions | **1 positive(s)** | No (Complete) | ✅ PASS |
| `7` | Pre-existing Condition Repeated in Future Window | `22598` | `2012-12-16` | `2012-12-16 → 2013-12-16` | 14 conditions | 2 conditions | None (All 0s) | No (Complete) | ✅ PASS |
| `8` | Pre-existing Condition Repeated in Future Window | `22598` | `2012-10-20` | `2012-10-20 → 2013-10-20` | 14 conditions | 2 conditions | None (All 0s) | No (Complete) | ✅ PASS |
| `9` | Zero Future Diagnoses (True Negative under active observation) | `110142` | `1971-12-13` | `1971-12-13 → 1972-12-12` | 16 conditions | 0 conditions | None (All 0s) | No (Complete) | ✅ PASS |
| `10` | Zero Future Diagnoses (True Negative under active observation) | `110142` | `1971-09-10` | `1971-09-10 → 1972-09-09` | 16 conditions | 0 conditions | None (All 0s) | No (Complete) | ✅ PASS |
| `11` | Zero Future Diagnoses (True Negative under active observation) | `16706` | `1980-08-14` | `1980-08-14 → 1981-08-14` | 18 conditions | 0 conditions | None (All 0s) | No (Complete) | ✅ PASS |
| `12` | Zero Future Diagnoses (True Negative under active observation) | `16706` | `1980-07-30` | `1980-07-30 → 1981-07-30` | 18 conditions | 0 conditions | None (All 0s) | No (Complete) | ✅ PASS |
| `13` | Censored Observation Window (<365 days future obs) | `17108` | `2019-02-07` | `2019-02-07 → 2020-02-07` | 6 conditions | 0 conditions | None (All 0s) | **YES (Censored)** | ✅ PASS |
| `14` | Censored Observation Window (<365 days future obs) | `17258` | `2018-10-08` | `2018-10-08 → 2019-10-08` | 4 conditions | 0 conditions | None (All 0s) | **YES (Censored)** | ✅ PASS |
| `15` | Censored Observation Window (<365 days future obs) | `17353` | `2018-09-26` | `2018-09-26 → 2019-09-26` | 2 conditions | 0 conditions | None (All 0s) | **YES (Censored)** | ✅ PASS |
| `16` | Repeated Landmark Snapshots for Same Patient | `51` | `2013-12-24` | `2013-12-24 → 2014-12-24` | 2 conditions | 0 conditions | None (All 0s) | No (Complete) | ✅ PASS |
| `17` | Repeated Landmark Snapshots for Same Patient | `51` | `2014-02-25` | `2014-02-25 → 2015-02-25` | 2 conditions | 0 conditions | None (All 0s) | No (Complete) | ✅ PASS |
| `18` | Repeated Landmark Snapshots for Same Patient | `51` | `2015-12-26` | `2015-12-26 → 2016-12-25` | 6 conditions | 0 conditions | None (All 0s) | No (Complete) | ✅ PASS |

---

## Detailed Landmark Traces

### Case #1: Patient `22598` — *Multiple Incident Future Diagnoses*
- **Index Encounter**: `2013-12-05` (Outpatient Visit, ID: `1001831`)
- **Observation Status**: Prior Obs = **89.34 yrs**, Future Obs = **5.43 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 14 distinct conditions present in historical state
  • Burn Injury (concept_id: `40480160`)
  • Anemia (concept_id: `439777`)
  • Essential Hypertension (concept_id: `316866`)
  • Type 2 Diabetes Mellitus (concept_id: `201826`)
  • Osteoarthritis of Knee (concept_id: `4079750`)
  • Hyperglycemia (concept_id: `4214376`)
  • Metabolic Syndrome X (concept_id: `436940`)
  • Fracture of Forearm (concept_id: `4278672`)
  • *[... 6 more historical conditions]*
- **Outcome Window Events ($T < date <= T + 365$)**:
  • **Burn Injury** (`40480160`) $\rightarrow$ **MASKED / EXCLUDED (Pre-existing in history)**
  • **Closed Fracture of Wrist** (`4230399`) $\rightarrow$ 🎯 **POSITIVE INCIDENT LABEL = 1**

------------------------------------------------------------

### Case #2: Patient `22598` — *Multiple Incident Future Diagnoses*
- **Index Encounter**: `2012-12-16` (Outpatient Visit, ID: `1001712`)
- **Observation Status**: Prior Obs = **88.37 yrs**, Future Obs = **6.4 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 14 distinct conditions present in historical state
  • Burn Injury (concept_id: `40480160`)
  • Anemia (concept_id: `439777`)
  • Type 2 Diabetes Mellitus (concept_id: `201826`)
  • Essential Hypertension (concept_id: `316866`)
  • Osteoarthritis of Knee (concept_id: `4079750`)
  • Hyperglycemia (concept_id: `4214376`)
  • Metabolic Syndrome X (concept_id: `436940`)
  • Fracture of Forearm (concept_id: `4278672`)
  • *[... 6 more historical conditions]*
- **Outcome Window Events ($T < date <= T + 365$)**:
  • **Fracture of Forearm** (`4278672`) $\rightarrow$ **MASKED / EXCLUDED (Pre-existing in history)**
  • **Burn Injury** (`40480160`) $\rightarrow$ **MASKED / EXCLUDED (Pre-existing in history)**

------------------------------------------------------------

### Case #3: Patient `22598` — *Multiple Incident Future Diagnoses*
- **Index Encounter**: `2012-10-20` (Outpatient Visit, ID: `1001693`)
- **Observation Status**: Prior Obs = **88.21 yrs**, Future Obs = **6.55 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 14 distinct conditions present in historical state
  • Burn Injury (concept_id: `40480160`)
  • Anemia (concept_id: `439777`)
  • Essential Hypertension (concept_id: `316866`)
  • Type 2 Diabetes Mellitus (concept_id: `201826`)
  • Osteoarthritis of Knee (concept_id: `4079750`)
  • Hyperglycemia (concept_id: `4214376`)
  • Metabolic Syndrome X (concept_id: `436940`)
  • Fracture of Forearm (concept_id: `4278672`)
  • *[... 6 more historical conditions]*
- **Outcome Window Events ($T < date <= T + 365$)**:
  • **Burn Injury** (`40480160`) $\rightarrow$ **MASKED / EXCLUDED (Pre-existing in history)**
  • **Fracture of Forearm** (`4278672`) $\rightarrow$ **MASKED / EXCLUDED (Pre-existing in history)**

------------------------------------------------------------

### Case #4: Patient `22598` — *Multiple Incident Future Diagnoses*
- **Index Encounter**: `2012-04-20` (Outpatient Visit, ID: `1001632`)
- **Observation Status**: Prior Obs = **87.71 yrs**, Future Obs = **7.06 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 14 distinct conditions present in historical state
  • Burn Injury (concept_id: `40480160`)
  • Anemia (concept_id: `439777`)
  • Essential Hypertension (concept_id: `316866`)
  • Type 2 Diabetes Mellitus (concept_id: `201826`)
  • Osteoarthritis of Knee (concept_id: `4079750`)
  • Hyperglycemia (concept_id: `4214376`)
  • Metabolic Syndrome X (concept_id: `436940`)
  • Fracture of Forearm (concept_id: `4278672`)
  • *[... 6 more historical conditions]*
- **Outcome Window Events ($T < date <= T + 365$)**:
  • **Fracture of Forearm** (`4278672`) $\rightarrow$ **MASKED / EXCLUDED (Pre-existing in history)**
  • **Burn Injury** (`40480160`) $\rightarrow$ **MASKED / EXCLUDED (Pre-existing in history)**

------------------------------------------------------------

### Case #5: Patient `24157` — *Pre-existing Condition Repeated in Future Window*
- **Index Encounter**: `2006-11-03` (Outpatient Visit, ID: `1047548`)
- **Observation Status**: Prior Obs = **73.91 yrs**, Future Obs = **4.97 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 20 distinct conditions present in historical state
  • Carcinoma in situ of Prostate (concept_id: `200970`)
  • Fracture of Forearm (concept_id: `4278672`)
  • Congestive Heart Failure (concept_id: `192279`)
  • Nonproliferative Retinopathy due to Type 2 Diabetes (concept_id: `43530656`)
  • Burn Injury (concept_id: `40480160`)
  • Proliferative Retinopathy due to Type 2 Diabetes (concept_id: `43530685`)
  • Essential Hypertension (concept_id: `316866`)
  • Retinopathy due to Type 2 Diabetes (concept_id: `4226121`)
  • *[... 12 more historical conditions]*
- **Outcome Window Events ($T < date <= T + 365$)**:
  • **Normal Body Mass Index** (`4112343`) $\rightarrow$ 🎯 **POSITIVE INCIDENT LABEL = 1**

------------------------------------------------------------

### Case #6: Patient `22598` — *Pre-existing Condition Repeated in Future Window*
- **Index Encounter**: `2013-12-05` (Outpatient Visit, ID: `1001831`)
- **Observation Status**: Prior Obs = **89.34 yrs**, Future Obs = **5.43 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 14 distinct conditions present in historical state
  • Burn Injury (concept_id: `40480160`)
  • Anemia (concept_id: `439777`)
  • Essential Hypertension (concept_id: `316866`)
  • Type 2 Diabetes Mellitus (concept_id: `201826`)
  • Osteoarthritis of Knee (concept_id: `4079750`)
  • Hyperglycemia (concept_id: `4214376`)
  • Metabolic Syndrome X (concept_id: `436940`)
  • Fracture of Forearm (concept_id: `4278672`)
  • *[... 6 more historical conditions]*
- **Outcome Window Events ($T < date <= T + 365$)**:
  • **Burn Injury** (`40480160`) $\rightarrow$ **MASKED / EXCLUDED (Pre-existing in history)**
  • **Closed Fracture of Wrist** (`4230399`) $\rightarrow$ 🎯 **POSITIVE INCIDENT LABEL = 1**

------------------------------------------------------------

### Case #7: Patient `22598` — *Pre-existing Condition Repeated in Future Window*
- **Index Encounter**: `2012-12-16` (Outpatient Visit, ID: `1001712`)
- **Observation Status**: Prior Obs = **88.37 yrs**, Future Obs = **6.4 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 14 distinct conditions present in historical state
  • Burn Injury (concept_id: `40480160`)
  • Anemia (concept_id: `439777`)
  • Type 2 Diabetes Mellitus (concept_id: `201826`)
  • Essential Hypertension (concept_id: `316866`)
  • Osteoarthritis of Knee (concept_id: `4079750`)
  • Hyperglycemia (concept_id: `4214376`)
  • Metabolic Syndrome X (concept_id: `436940`)
  • Fracture of Forearm (concept_id: `4278672`)
  • *[... 6 more historical conditions]*
- **Outcome Window Events ($T < date <= T + 365$)**:
  • **Fracture of Forearm** (`4278672`) $\rightarrow$ **MASKED / EXCLUDED (Pre-existing in history)**
  • **Burn Injury** (`40480160`) $\rightarrow$ **MASKED / EXCLUDED (Pre-existing in history)**

------------------------------------------------------------

### Case #8: Patient `22598` — *Pre-existing Condition Repeated in Future Window*
- **Index Encounter**: `2012-10-20` (Outpatient Visit, ID: `1001693`)
- **Observation Status**: Prior Obs = **88.21 yrs**, Future Obs = **6.55 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 14 distinct conditions present in historical state
  • Burn Injury (concept_id: `40480160`)
  • Anemia (concept_id: `439777`)
  • Essential Hypertension (concept_id: `316866`)
  • Type 2 Diabetes Mellitus (concept_id: `201826`)
  • Osteoarthritis of Knee (concept_id: `4079750`)
  • Hyperglycemia (concept_id: `4214376`)
  • Metabolic Syndrome X (concept_id: `436940`)
  • Fracture of Forearm (concept_id: `4278672`)
  • *[... 6 more historical conditions]*
- **Outcome Window Events ($T < date <= T + 365$)**:
  • **Burn Injury** (`40480160`) $\rightarrow$ **MASKED / EXCLUDED (Pre-existing in history)**
  • **Fracture of Forearm** (`4278672`) $\rightarrow$ **MASKED / EXCLUDED (Pre-existing in history)**

------------------------------------------------------------

### Case #9: Patient `110142` — *Zero Future Diagnoses (True Negative under active observation)*
- **Index Encounter**: `1971-12-13` (Outpatient Visit, ID: `3509480`)
- **Observation Status**: Prior Obs = **37.3 yrs**, Future Obs = **3.76 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 16 distinct conditions present in historical state
  • Nonproliferative Retinopathy due to Type 2 Diabetes (concept_id: `43530656`)
  • Anemia (concept_id: `439777`)
  • Neuropathy due to Type 2 Diabetes (concept_id: `37016354`)
  • Type 2 Diabetes Mellitus (concept_id: `201826`)
  • Osteoarthritis of Knee (concept_id: `4079750`)
  • Retinopathy due to Type 2 Diabetes (concept_id: `4226121`)
  • Acute Bronchitis (concept_id: `260139`)
  • Metabolic Syndrome X (concept_id: `436940`)
  • *[... 8 more historical conditions]*
- **Outcome Window Events ($T < date <= T + 365$)**:
  • *No diagnoses recorded during outcome window $\rightarrow$ All target comorbidity labels = 0 (True Negative)*

------------------------------------------------------------

### Case #10: Patient `110142` — *Zero Future Diagnoses (True Negative under active observation)*
- **Index Encounter**: `1971-09-10` (Outpatient Visit, ID: `3508953`)
- **Observation Status**: Prior Obs = **37.04 yrs**, Future Obs = **4.01 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 16 distinct conditions present in historical state
  • Nonproliferative Retinopathy due to Type 2 Diabetes (concept_id: `43530656`)
  • Anemia (concept_id: `439777`)
  • Neuropathy due to Type 2 Diabetes (concept_id: `37016354`)
  • Type 2 Diabetes Mellitus (concept_id: `201826`)
  • Osteoarthritis of Knee (concept_id: `4079750`)
  • Retinopathy due to Type 2 Diabetes (concept_id: `4226121`)
  • Acute Bronchitis (concept_id: `260139`)
  • Metabolic Syndrome X (concept_id: `436940`)
  • *[... 8 more historical conditions]*
- **Outcome Window Events ($T < date <= T + 365$)**:
  • *No diagnoses recorded during outcome window $\rightarrow$ All target comorbidity labels = 0 (True Negative)*

------------------------------------------------------------

### Case #11: Patient `16706` — *Zero Future Diagnoses (True Negative under active observation)*
- **Index Encounter**: `1980-08-14` (Outpatient Visit, ID: `822985`)
- **Observation Status**: Prior Obs = **44.31 yrs**, Future Obs = **4.25 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 18 distinct conditions present in historical state
  • Nonproliferative Retinopathy due to Type 2 Diabetes (concept_id: `43530656`)
  • Anemia (concept_id: `439777`)
  • Type 2 Diabetes Mellitus (concept_id: `201826`)
  • Hyperlipidemia (concept_id: `432867`)
  • Essential Hypertension (concept_id: `316866`)
  • Hyperglycemia (concept_id: `4214376`)
  • Retinopathy due to Type 2 Diabetes (concept_id: `4226121`)
  • Acute Bronchitis (concept_id: `260139`)
  • *[... 10 more historical conditions]*
- **Outcome Window Events ($T < date <= T + 365$)**:
  • *No diagnoses recorded during outcome window $\rightarrow$ All target comorbidity labels = 0 (True Negative)*

------------------------------------------------------------

### Case #12: Patient `16706` — *Zero Future Diagnoses (True Negative under active observation)*
- **Index Encounter**: `1980-07-30` (Outpatient Visit, ID: `822980`)
- **Observation Status**: Prior Obs = **44.27 yrs**, Future Obs = **4.29 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 18 distinct conditions present in historical state
  • Nonproliferative Retinopathy due to Type 2 Diabetes (concept_id: `43530656`)
  • Anemia (concept_id: `439777`)
  • Essential Hypertension (concept_id: `316866`)
  • Hyperlipidemia (concept_id: `432867`)
  • Type 2 Diabetes Mellitus (concept_id: `201826`)
  • Hyperglycemia (concept_id: `4214376`)
  • Retinopathy due to Type 2 Diabetes (concept_id: `4226121`)
  • Acute Bronchitis (concept_id: `260139`)
  • *[... 10 more historical conditions]*
- **Outcome Window Events ($T < date <= T + 365$)**:
  • *No diagnoses recorded during outcome window $\rightarrow$ All target comorbidity labels = 0 (True Negative)*

------------------------------------------------------------

### Case #13: Patient `17108` — *Censored Observation Window (<365 days future obs)*
- **Index Encounter**: `2019-02-07` (Inpatient Visit, ID: `36467`)
- **Observation Status**: Prior Obs = **34.94 yrs**, Future Obs = **0.0 yrs** (Completeness Flag: `0`)
- **Pre-Landmark Conditions ($<= T$)**: 6 distinct conditions present in historical state
  • Anemia (concept_id: `439777`)
  • Essential Hypertension (concept_id: `316866`)
  • Hyperlipidemia (concept_id: `432867`)
  • Prediabetes (concept_id: `4311629`)
  • Injury of Anterior Cruciate Ligament (concept_id: `40479768`)
  • Viral Sinusitis (concept_id: `40481087`)
- **Outcome Window Events ($T < date <= T + 365$)**:
  • *No diagnoses recorded during outcome window $\rightarrow$ All target comorbidity labels = 0 (True Negative)*

------------------------------------------------------------

### Case #14: Patient `17258` — *Censored Observation Window (<365 days future obs)*
- **Index Encounter**: `2018-10-08` (Outpatient Visit, ID: `843890`)
- **Observation Status**: Prior Obs = **9.33 yrs**, Future Obs = **0.0 yrs** (Completeness Flag: `0`)
- **Pre-Landmark Conditions ($<= T$)**: 4 distinct conditions present in historical state
  • Otitis Media (concept_id: `372328`)
  • Normal Body Mass Index (concept_id: `4112343`)
  • Acute Bronchitis (concept_id: `260139`)
  • Viral Sinusitis (concept_id: `40481087`)
- **Outcome Window Events ($T < date <= T + 365$)**:
  • *No diagnoses recorded during outcome window $\rightarrow$ All target comorbidity labels = 0 (True Negative)*

------------------------------------------------------------

### Case #15: Patient `17353` — *Censored Observation Window (<365 days future obs)*
- **Index Encounter**: `2018-09-26` (Outpatient Visit, ID: `846870`)
- **Observation Status**: Prior Obs = **38.03 yrs**, Future Obs = **0.0 yrs** (Completeness Flag: `0`)
- **Pre-Landmark Conditions ($<= T$)**: 2 distinct conditions present in historical state
  • Seasonal Allergic Rhinitis (concept_id: `4280726`)
  • Viral Sinusitis (concept_id: `40481087`)
- **Outcome Window Events ($T < date <= T + 365$)**:
  • *No diagnoses recorded during outcome window $\rightarrow$ All target comorbidity labels = 0 (True Negative)*

------------------------------------------------------------

### Case #16: Patient `51` — *Repeated Landmark Snapshots for Same Patient*
- **Index Encounter**: `2013-12-24` (Outpatient Visit, ID: `346951`)
- **Observation Status**: Prior Obs = **9.84 yrs**, Future Obs = **4.98 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 2 distinct conditions present in historical state
  • Chronic Sinusitis (concept_id: `257012`)
  • Normal Pregnancy (concept_id: `4217975`)
- **Outcome Window Events ($T < date <= T + 365$)**:
  • *No diagnoses recorded during outcome window $\rightarrow$ All target comorbidity labels = 0 (True Negative)*

------------------------------------------------------------

### Case #17: Patient `51` — *Repeated Landmark Snapshots for Same Patient*
- **Index Encounter**: `2014-02-25` (Outpatient Visit, ID: `346953`)
- **Observation Status**: Prior Obs = **10.02 yrs**, Future Obs = **4.81 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 2 distinct conditions present in historical state
  • Chronic Sinusitis (concept_id: `257012`)
  • Normal Pregnancy (concept_id: `4217975`)
- **Outcome Window Events ($T < date <= T + 365$)**:
  • *No diagnoses recorded during outcome window $\rightarrow$ All target comorbidity labels = 0 (True Negative)*

------------------------------------------------------------

### Case #18: Patient `51` — *Repeated Landmark Snapshots for Same Patient*
- **Index Encounter**: `2015-12-26` (Outpatient Visit, ID: `346957`)
- **Observation Status**: Prior Obs = **11.85 yrs**, Future Obs = **2.98 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 6 distinct conditions present in historical state
  • Anemia (concept_id: `439777`)
  • Prediabetes (concept_id: `4311629`)
  • Normal Body Mass Index (concept_id: `4112343`)
  • Chronic Sinusitis (concept_id: `257012`)
  • Normal Pregnancy (concept_id: `4217975`)
  • Viral Sinusitis (concept_id: `40481087`)
- **Outcome Window Events ($T < date <= T + 365$)**:
  • *No diagnoses recorded during outcome window $\rightarrow$ All target comorbidity labels = 0 (True Negative)*

------------------------------------------------------------
