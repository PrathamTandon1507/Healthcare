# Phase 3 Manual Label Validation Report

*Generated At:* 2026-09-18T02:03:49.627250  
*Total Manual Audit Cases:* 18  

---

## Summary Table of 18 Audit Cases

| Case # | Category | Patient ID | Landmark Date ($T$) | Future Window ($T, T+365]$ | Pre-existing Conditions at $T$ | Diagnoses in Future Window | Incident Comorbidity Labels ($=1$) | Censored? | Leakage Audit |
|---|---|---|---|---|---|---|---|---|---|
| `1` | Multiple Incident Future Diagnoses | `55509` | `2012-10-06` | `2012-10-06 → 2013-10-06` | 14 conditions | 3 conditions | **3 positive(s)** | No (Complete) | ✅ PASS |
| `2` | Multiple Incident Future Diagnoses | `56264` | `2016-03-29` | `2016-03-29 → 2017-03-29` | 11 conditions | 2 conditions | **1 positive(s)** | No (Complete) | ✅ PASS |
| `3` | Multiple Incident Future Diagnoses | `15802` | `2006-09-30` | `2006-09-30 → 2007-09-30` | 7 conditions | 2 conditions | **2 positive(s)** | No (Complete) | ✅ PASS |
| `4` | Multiple Incident Future Diagnoses | `54636` | `2014-08-26` | `2014-08-26 → 2015-08-26` | 10 conditions | 2 conditions | None (All 0s) | No (Complete) | ✅ PASS |
| `5` | Pre-existing Condition Repeated in Future Window | `55509` | `2012-10-06` | `2012-10-06 → 2013-10-06` | 14 conditions | 3 conditions | **3 positive(s)** | No (Complete) | ✅ PASS |
| `6` | Pre-existing Condition Repeated in Future Window | `55740` | `2013-06-29` | `2013-06-29 → 2014-06-29` | 4 conditions | 1 conditions | **1 positive(s)** | No (Complete) | ✅ PASS |
| `7` | Pre-existing Condition Repeated in Future Window | `56253` | `2016-02-03` | `2016-02-03 → 2017-02-02` | 17 conditions | 1 conditions | None (All 0s) | No (Complete) | ✅ PASS |
| `8` | Pre-existing Condition Repeated in Future Window | `56171` | `2015-04-06` | `2015-04-06 → 2016-04-05` | 2 conditions | 1 conditions | None (All 0s) | No (Complete) | ✅ PASS |
| `9` | Zero Future Diagnoses (True Negative under active observation) | `70938` | `2017-05-29` | `2017-05-29 → 2018-05-29` | 8 conditions | 0 conditions | None (All 0s) | No (Complete) | ✅ PASS |
| `10` | Zero Future Diagnoses (True Negative under active observation) | `71928` | `2015-10-10` | `2015-10-10 → 2016-10-09` | 12 conditions | 0 conditions | None (All 0s) | No (Complete) | ✅ PASS |
| `11` | Zero Future Diagnoses (True Negative under active observation) | `71086` | `2013-11-03` | `2013-11-03 → 2014-11-03` | 12 conditions | 0 conditions | None (All 0s) | No (Complete) | ✅ PASS |
| `12` | Zero Future Diagnoses (True Negative under active observation) | `72344` | `2009-07-13` | `2009-07-13 → 2010-07-13` | 5 conditions | 0 conditions | None (All 0s) | No (Complete) | ✅ PASS |
| `13` | Censored Observation Window (<365 days future obs) | `73966` | `2003-03-05` | `2003-03-05 → 2004-03-04` | 19 conditions | 0 conditions | None (All 0s) | **YES (Censored)** | ✅ PASS |
| `14` | Censored Observation Window (<365 days future obs) | `75163` | `2018-11-27` | `2018-11-27 → 2019-11-27` | 16 conditions | 0 conditions | None (All 0s) | **YES (Censored)** | ✅ PASS |
| `15` | Censored Observation Window (<365 days future obs) | `75163` | `2018-09-04` | `2018-09-04 → 2019-09-04` | 16 conditions | 0 conditions | None (All 0s) | **YES (Censored)** | ✅ PASS |
| `16` | Repeated Landmark Snapshots for Same Patient | `51` | `2014-03-12` | `2014-03-12 → 2015-03-12` | 2 conditions | 0 conditions | None (All 0s) | No (Complete) | ✅ PASS |
| `17` | Repeated Landmark Snapshots for Same Patient | `51` | `2013-12-24` | `2013-12-24 → 2014-12-24` | 2 conditions | 0 conditions | None (All 0s) | No (Complete) | ✅ PASS |
| `18` | Repeated Landmark Snapshots for Same Patient | `51` | `2013-10-01` | `2013-10-01 → 2014-10-01` | 2 conditions | 0 conditions | None (All 0s) | No (Complete) | ✅ PASS |

---

## Detailed Landmark Traces

### Case #1: Patient `55509` — *Multiple Incident Future Diagnoses*
- **Index Encounter**: `2012-10-06` (Outpatient Visit, ID: `1934289`)
- **Observation Status**: Prior Obs = **44.67 yrs**, Future Obs = **6.4 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 14 distinct conditions present in historical state
  • Anemia (concept_id: `439777`)
  • Type 2 diabetes mellitus (concept_id: `201826`)
  • Hypertensive disorder (concept_id: `316866`)
  • Osteoarthritis of knee (concept_id: `4079750`)
  • Hyperglycemia (concept_id: `4214376`)
  • Acute bronchitis (concept_id: `260139`)
  • Metabolic syndrome X (concept_id: `436940`)
  • Prediabetes (concept_id: `4311629`)
  • *[... 6 more historical conditions]*
- **Outcome Window Events ($T < date <= T + 365$)**:
  • **Acute viral pharyngitis** (`4294548`) $\rightarrow$ 🎯 **POSITIVE INCIDENT LABEL = 1**
  • **Hyperglycemia** (`432867`) $\rightarrow$ 🎯 **POSITIVE INCIDENT LABEL = 1**
  • **Chronic sinusitis** (`257012`) $\rightarrow$ 🎯 **POSITIVE INCIDENT LABEL = 1**

------------------------------------------------------------

### Case #2: Patient `56264` — *Multiple Incident Future Diagnoses*
- **Index Encounter**: `2016-03-29` (Outpatient Visit, ID: `1955411`)
- **Observation Status**: Prior Obs = **20.34 yrs**, Future Obs = **2.99 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 11 distinct conditions present in historical state
  • Condition (concept_id: 436096) (concept_id: `436096`)
  • Hypertensive disorder (concept_id: `316866`)
  • Condition (concept_id: 4208104) (concept_id: `4208104`)
  • Fracture of rib (concept_id: `4055754`)
  • Normal pregnancy (concept_id: `4217975`)
  • Condition (concept_id: 43530652) (concept_id: `43530652`)
  • Prediabetes (concept_id: `4311629`)
  • Chronic sinusitis (concept_id: `257012`)
  • *[... 3 more historical conditions]*
- **Outcome Window Events ($T < date <= T + 365$)**:
  • **Normal pregnancy** (`4217975`) $\rightarrow$ **MASKED / EXCLUDED (Pre-existing in history)**
  • **Viral sinusitis** (`40481087`) $\rightarrow$ 🎯 **POSITIVE INCIDENT LABEL = 1**

------------------------------------------------------------

### Case #3: Patient `15802` — *Multiple Incident Future Diagnoses*
- **Index Encounter**: `2006-09-30` (Inpatient Visit, ID: `1529`)
- **Observation Status**: Prior Obs = **73.06 yrs**, Future Obs = **3.38 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 7 distinct conditions present in historical state
  • Condition (concept_id: 4079749) (concept_id: `4079749`)
  • Condition (concept_id: 200970) (concept_id: `200970`)
  • Condition (concept_id: 4115276) (concept_id: `4115276`)
  • Condition (concept_id: 4129902) (concept_id: `4129902`)
  • Condition (concept_id: 4310703) (concept_id: `4310703`)
  • Condition (concept_id: 4280726) (concept_id: `4280726`)
  • Viral sinusitis (concept_id: `40481087`)
- **Outcome Window Events ($T < date <= T + 365$)**:
  • **Acute bronchitis** (`260139`) $\rightarrow$ 🎯 **POSITIVE INCIDENT LABEL = 1**
  • **Body mass index 30+ - obesity** (`4112343`) $\rightarrow$ 🎯 **POSITIVE INCIDENT LABEL = 1**

------------------------------------------------------------

### Case #4: Patient `54636` — *Multiple Incident Future Diagnoses*
- **Index Encounter**: `2014-08-26` (Emergency Room Visit, ID: `236198`)
- **Observation Status**: Prior Obs = **19.58 yrs**, Future Obs = **4.7 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 10 distinct conditions present in historical state
  • Condition (concept_id: 436096) (concept_id: `436096`)
  • Anemia (concept_id: `439777`)
  • Childhood asthma (concept_id: `4051466`)
  • Fracture of rib (concept_id: `4055754`)
  • Body mass index 30+ - obesity (concept_id: `4112343`)
  • Normal pregnancy (concept_id: `4217975`)
  • Miscarriage (Spontaneous abortion) (concept_id: `4078393`)
  • Condition (concept_id: 40318618) (concept_id: `40318618`)
  • *[... 2 more historical conditions]*
- **Outcome Window Events ($T < date <= T + 365$)**:
  • **Normal pregnancy** (`4217975`) $\rightarrow$ **MASKED / EXCLUDED (Pre-existing in history)**
  • **Viral sinusitis** (`40481087`) $\rightarrow$ **MASKED / EXCLUDED (Pre-existing in history)**

------------------------------------------------------------

### Case #5: Patient `55509` — *Pre-existing Condition Repeated in Future Window*
- **Index Encounter**: `2012-10-06` (Outpatient Visit, ID: `1934289`)
- **Observation Status**: Prior Obs = **44.67 yrs**, Future Obs = **6.4 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 14 distinct conditions present in historical state
  • Anemia (concept_id: `439777`)
  • Type 2 diabetes mellitus (concept_id: `201826`)
  • Hypertensive disorder (concept_id: `316866`)
  • Osteoarthritis of knee (concept_id: `4079750`)
  • Hyperglycemia (concept_id: `4214376`)
  • Acute bronchitis (concept_id: `260139`)
  • Metabolic syndrome X (concept_id: `436940`)
  • Prediabetes (concept_id: `4311629`)
  • *[... 6 more historical conditions]*
- **Outcome Window Events ($T < date <= T + 365$)**:
  • **Acute viral pharyngitis** (`4294548`) $\rightarrow$ 🎯 **POSITIVE INCIDENT LABEL = 1**
  • **Hyperglycemia** (`432867`) $\rightarrow$ 🎯 **POSITIVE INCIDENT LABEL = 1**
  • **Chronic sinusitis** (`257012`) $\rightarrow$ 🎯 **POSITIVE INCIDENT LABEL = 1**

------------------------------------------------------------

### Case #6: Patient `55740` — *Pre-existing Condition Repeated in Future Window*
- **Index Encounter**: `2013-06-29` (Outpatient Visit, ID: `1940331`)
- **Observation Status**: Prior Obs = **49.34 yrs**, Future Obs = **5.5 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 4 distinct conditions present in historical state
  • Condition (concept_id: 4208104) (concept_id: `4208104`)
  • Miscarriage (Spontaneous abortion) (concept_id: `4078393`)
  • Sprain of ankle (concept_id: `81151`)
  • Normal pregnancy (concept_id: `4217975`)
- **Outcome Window Events ($T < date <= T + 365$)**:
  • **Acute bronchitis** (`260139`) $\rightarrow$ 🎯 **POSITIVE INCIDENT LABEL = 1**

------------------------------------------------------------

### Case #7: Patient `56253` — *Pre-existing Condition Repeated in Future Window*
- **Index Encounter**: `2016-02-03` (Outpatient Visit, ID: `1955177`)
- **Observation Status**: Prior Obs = **57.28 yrs**, Future Obs = **3.24 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 17 distinct conditions present in historical state
  • Condition (concept_id: 43530656) (concept_id: `43530656`)
  • Anemia (concept_id: `439777`)
  • Type 2 diabetes mellitus (concept_id: `201826`)
  • Hyperglycemia (concept_id: `4214376`)
  • Condition (concept_id: 4226121) (concept_id: `4226121`)
  • Condition (concept_id: 200970) (concept_id: `200970`)
  • Acute bronchitis (concept_id: `260139`)
  • Metabolic syndrome X (concept_id: `436940`)
  • *[... 9 more historical conditions]*
- **Outcome Window Events ($T < date <= T + 365$)**:
  • **Viral sinusitis** (`40481087`) $\rightarrow$ **MASKED / EXCLUDED (Pre-existing in history)**

------------------------------------------------------------

### Case #8: Patient `56171` — *Pre-existing Condition Repeated in Future Window*
- **Index Encounter**: `2015-04-06` (Outpatient Visit, ID: `1952845`)
- **Observation Status**: Prior Obs = **4.73 yrs**, Future Obs = **3.28 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 2 distinct conditions present in historical state
  • Acute bronchitis (concept_id: `260139`)
  • Normal pregnancy (concept_id: `4217975`)
- **Outcome Window Events ($T < date <= T + 365$)**:
  • **Normal pregnancy** (`4217975`) $\rightarrow$ **MASKED / EXCLUDED (Pre-existing in history)**

------------------------------------------------------------

### Case #9: Patient `70938` — *Zero Future Diagnoses (True Negative under active observation)*
- **Index Encounter**: `2017-05-29` (Inpatient Visit, ID: `125961`)
- **Observation Status**: Prior Obs = **38.9 yrs**, Future Obs = **1.92 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 8 distinct conditions present in historical state
  • Anemia (concept_id: `439777`)
  • Condition (concept_id: 4115276) (concept_id: `4115276`)
  • Prediabetes (concept_id: `4311629`)
  • Condition (concept_id: 4310703) (concept_id: `4310703`)
  • Chronic sinusitis (concept_id: `257012`)
  • Sinusitis (concept_id: `4283893`)
  • Body mass index 30+ - obesity (concept_id: `4112343`)
  • Viral sinusitis (concept_id: `40481087`)
- **Outcome Window Events ($T < date <= T + 365$)**:
  • *No diagnoses recorded during outcome window $\rightarrow$ All target comorbidity labels = 0 (True Negative)*

------------------------------------------------------------

### Case #10: Patient `71928` — *Zero Future Diagnoses (True Negative under active observation)*
- **Index Encounter**: `2015-10-10` (Outpatient Visit, ID: `2405984`)
- **Observation Status**: Prior Obs = **52.91 yrs**, Future Obs = **3.53 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 12 distinct conditions present in historical state
  • Anemia (concept_id: `439777`)
  • Type 2 diabetes mellitus (concept_id: `201826`)
  • Hypertensive disorder (concept_id: `316866`)
  • Condition (concept_id: 37016354) (concept_id: `37016354`)
  • Condition (concept_id: 4152936) (concept_id: `4152936`)
  • Condition (concept_id: 4226121) (concept_id: `4226121`)
  • Metabolic syndrome X (concept_id: `436940`)
  • Prediabetes (concept_id: `4311629`)
  • *[... 4 more historical conditions]*
- **Outcome Window Events ($T < date <= T + 365$)**:
  • *No diagnoses recorded during outcome window $\rightarrow$ All target comorbidity labels = 0 (True Negative)*

------------------------------------------------------------

### Case #11: Patient `71086` — *Zero Future Diagnoses (True Negative under active observation)*
- **Index Encounter**: `2013-11-03` (Outpatient Visit, ID: `2382040`)
- **Observation Status**: Prior Obs = **4.66 yrs**, Future Obs = **5.42 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 12 distinct conditions present in historical state
  • Anemia (concept_id: `439777`)
  • Type 2 diabetes mellitus (concept_id: `201826`)
  • Acute bronchitis (concept_id: `260139`)
  • Metabolic syndrome X (concept_id: `436940`)
  • Congestive heart failure (concept_id: `192279`)
  • Chronic kidney disease stage 1 (concept_id: `443601`)
  • Condition (concept_id: 45769905) (concept_id: `45769905`)
  • Normal pregnancy (concept_id: `4217975`)
  • *[... 4 more historical conditions]*
- **Outcome Window Events ($T < date <= T + 365$)**:
  • *No diagnoses recorded during outcome window $\rightarrow$ All target comorbidity labels = 0 (True Negative)*

------------------------------------------------------------

### Case #12: Patient `72344` — *Zero Future Diagnoses (True Negative under active observation)*
- **Index Encounter**: `2009-07-13` (Outpatient Visit, ID: `2417503`)
- **Observation Status**: Prior Obs = **25.14 yrs**, Future Obs = **9.64 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 5 distinct conditions present in historical state
  • Anemia (concept_id: `439777`)
  • Condition (concept_id: 4116491) (concept_id: `4116491`)
  • Suspected condition (concept_id: `261325`)
  • Prediabetes (concept_id: `4311629`)
  • Chronic sinusitis (concept_id: `257012`)
- **Outcome Window Events ($T < date <= T + 365$)**:
  • *No diagnoses recorded during outcome window $\rightarrow$ All target comorbidity labels = 0 (True Negative)*

------------------------------------------------------------

### Case #13: Patient `73966` — *Censored Observation Window (<365 days future obs)*
- **Index Encounter**: `2003-03-05` (Outpatient Visit, ID: `2465628`)
- **Observation Status**: Prior Obs = **57.2 yrs**, Future Obs = **0.42 yrs** (Completeness Flag: `0`)
- **Pre-Landmark Conditions ($<= T$)**: 19 distinct conditions present in historical state
  • Condition (concept_id: 313217) (concept_id: `313217`)
  • Condition (concept_id: 200970) (concept_id: `200970`)
  • Acute viral pharyngitis (concept_id: `4294548`)
  • Congestive heart failure (concept_id: `192279`)
  • Condition (concept_id: 4059173) (concept_id: `4059173`)
  • Acute bronchitis (concept_id: `260139`)
  • Condition (concept_id: 45769905) (concept_id: `45769905`)
  • Viral sinusitis (concept_id: `40481087`)
  • *[... 11 more historical conditions]*
- **Outcome Window Events ($T < date <= T + 365$)**:
  • *No diagnoses recorded during outcome window $\rightarrow$ All target comorbidity labels = 0 (True Negative)*

------------------------------------------------------------

### Case #14: Patient `75163` — *Censored Observation Window (<365 days future obs)*
- **Index Encounter**: `2018-11-27` (Outpatient Visit, ID: `2501684`)
- **Observation Status**: Prior Obs = **64.13 yrs**, Future Obs = **0.44 yrs** (Completeness Flag: `0`)
- **Pre-Landmark Conditions ($<= T$)**: 16 distinct conditions present in historical state
  • Anemia (concept_id: `439777`)
  • Type 2 diabetes mellitus (concept_id: `201826`)
  • Hypertensive disorder (concept_id: `316866`)
  • Hyperglycemia (concept_id: `4214376`)
  • Acute bronchitis (concept_id: `260139`)
  • Metabolic syndrome X (concept_id: `436940`)
  • Prediabetes (concept_id: `4311629`)
  • Chronic kidney disease stage 1 (concept_id: `443601`)
  • *[... 8 more historical conditions]*
- **Outcome Window Events ($T < date <= T + 365$)**:
  • *No diagnoses recorded during outcome window $\rightarrow$ All target comorbidity labels = 0 (True Negative)*

------------------------------------------------------------

### Case #15: Patient `75163` — *Censored Observation Window (<365 days future obs)*
- **Index Encounter**: `2018-09-04` (Outpatient Visit, ID: `2501656`)
- **Observation Status**: Prior Obs = **63.9 yrs**, Future Obs = **0.67 yrs** (Completeness Flag: `0`)
- **Pre-Landmark Conditions ($<= T$)**: 16 distinct conditions present in historical state
  • Anemia (concept_id: `439777`)
  • Hypertensive disorder (concept_id: `316866`)
  • Type 2 diabetes mellitus (concept_id: `201826`)
  • Hyperglycemia (concept_id: `4214376`)
  • Acute bronchitis (concept_id: `260139`)
  • Metabolic syndrome X (concept_id: `436940`)
  • Prediabetes (concept_id: `4311629`)
  • Congestive heart failure (concept_id: `192279`)
  • *[... 8 more historical conditions]*
- **Outcome Window Events ($T < date <= T + 365$)**:
  • *No diagnoses recorded during outcome window $\rightarrow$ All target comorbidity labels = 0 (True Negative)*

------------------------------------------------------------

### Case #16: Patient `51` — *Repeated Landmark Snapshots for Same Patient*
- **Index Encounter**: `2014-03-12` (Inpatient Visit, ID: `75249`)
- **Observation Status**: Prior Obs = **10.05 yrs**, Future Obs = **4.77 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 2 distinct conditions present in historical state
  • Chronic sinusitis (concept_id: `257012`)
  • Normal pregnancy (concept_id: `4217975`)
- **Outcome Window Events ($T < date <= T + 365$)**:
  • *No diagnoses recorded during outcome window $\rightarrow$ All target comorbidity labels = 0 (True Negative)*

------------------------------------------------------------

### Case #17: Patient `51` — *Repeated Landmark Snapshots for Same Patient*
- **Index Encounter**: `2013-12-24` (Outpatient Visit, ID: `346951`)
- **Observation Status**: Prior Obs = **9.84 yrs**, Future Obs = **4.98 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 2 distinct conditions present in historical state
  • Chronic sinusitis (concept_id: `257012`)
  • Normal pregnancy (concept_id: `4217975`)
- **Outcome Window Events ($T < date <= T + 365$)**:
  • *No diagnoses recorded during outcome window $\rightarrow$ All target comorbidity labels = 0 (True Negative)*

------------------------------------------------------------

### Case #18: Patient `51` — *Repeated Landmark Snapshots for Same Patient*
- **Index Encounter**: `2013-10-01` (Outpatient Visit, ID: `346948`)
- **Observation Status**: Prior Obs = **9.61 yrs**, Future Obs = **5.21 yrs** (Completeness Flag: `1`)
- **Pre-Landmark Conditions ($<= T$)**: 2 distinct conditions present in historical state
  • Chronic sinusitis (concept_id: `257012`)
  • Normal pregnancy (concept_id: `4217975`)
- **Outcome Window Events ($T < date <= T + 365$)**:
  • *No diagnoses recorded during outcome window $\rightarrow$ All target comorbidity labels = 0 (True Negative)*

------------------------------------------------------------
