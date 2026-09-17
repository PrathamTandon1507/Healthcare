# Synthea OMOP 100K Dataset Profile & Schema Inspection Report

*Generated At:* 2026-09-18T01:46:31.676767  
*Source Directory:* `synthea100k`  
*DuckDB Version:* `1.5.5`  

---

## 1. Executive Summary & Table Inventory

| Table Name | Raw Rows in Export | Distinct Primary Key Records | Primary Entity Key | Role / Description |
|---|---|---|---|---|
| `person` | 235,222 | 117,611 | `person_id` | Primary OMOP CDM table |
| `observation_period` | 235,222 | 117,611 | `observation_period_id` | Primary OMOP CDM table |
| `condition_occurrence` | 2,644,530 | 1,763,020 | `condition_occurrence_id` | Primary OMOP CDM table |
| `visit_occurrence` | 11,030,274 | 3,676,758 | `visit_occurrence_id` | Primary OMOP CDM table |


## 2. Patient Demographics (`person`)

- **Total Unique Patients (`person_id`):** **117,611**
- **Birth Year Range:** 1908 to 2019 (Median: 1973, IQR: 1954–1995)

### Sex / Gender Breakdown
| Concept ID | Demographic Category | Source Value | Unique Patient Count | Cohort Percentage |
|---|---|---|---|---|
| `8507` | **Male** | `M` | **59,127** | **50.27%** |
| `8532` | **Female** | `F` | **58,484** | **49.73%** |

### Race Breakdown
| Concept ID | Demographic Category | Source Value | Unique Patient Count | Cohort Percentage |
|---|---|---|---|---|
| `8527` | **White** | `white` | 89,692 | 76.26% |
| `0` | **Hispanic** | `hispanic` | 11,485 | 9.77% |
| `8516` | **Black** | `black` | 8,696 | 7.39% |
| `8515` | **Asian** | `asian` | 7,105 | 6.04% |
| `0` | **Native** | `native` | 517 | 0.44% |
| `0` | **Other** | `other` | 116 | 0.1% |

## 3. Observation Period Span (`observation_period`)

- **Total Patients with Observation Coverage:** 117,611 (100% cohort coverage)
- **Dataset Calendar Window:** `1908-07-02` to `2019-05-21`
- **Median Observation-Period Span:** **24.3 years** (8,877.0 days)
- **Mean Observation-Period Span:** **28.59 years** (10,443.7 days)
- **Min / Max Observation Span:** 0 days to 110.5 years

## 4. Visits Profile (`visit_occurrence`)

- **Total Distinct Clinical Visits:** **3,676,758**
- **Patients with >= 1 Visit:** 117,611 (100.0% of cohort)
- **Date Range:** `1908-07-02` to `2019-05-21`
- **Visits Per Patient:** Median = **22.0**, Mean = **31.26**, IQR = **15.0–37.0**, Max = 1479.0

### Visit Types Breakdown
| Visit Concept ID | Description | Total Encounters | Unique Patients | Encounter % | Cohort Prev % |
|---|---|---|---|---|---|
| `9202` | **Outpatient Visit** | 3,331,255 | 117,611 | 90.6% | 100.0% |
| `9203` | **Emergency Room Visit** | 205,486 | 82,260 | 5.59% | 69.94% |
| `9201` | **Inpatient Visit** | 140,017 | 27,421 | 3.81% | 23.31% |

## 5. Conditions Profile (`condition_occurrence`)

- **Total Distinct Condition Records:** **2,644,523**
- **Unique Patients with >= 1 Diagnosis:** 115,681 (98.4% of cohort)
- **Distinct Condition Concepts:** 144
- **Conditions Per Patient:** Median = 21.0, Mean = 22.86, Distinct Concepts/Patient = 6.0

### Top Conditions by Patient Prevalence
| Concept ID | Condition / Disease Name | Source Code | Total Events | Patient Count | Cohort Prevalence |
|---|---|---|---|---|---|
| `40481087` | **Viral sinusitis** | `444814009` | 368,769 | 74,879 | **63.67%** |
| `0` | **Body mass index 30+ - obesity** | `408512008` | 258,009 | 61,152 | **52.0%** |
| `4112343` | **Normal body mass index** | `195662009` | 210,259 | 52,544 | **44.68%** |
| `260139` | **Acute bronchitis** | `10509002` | 169,617 | 45,760 | **38.91%** |
| `4311629` | **Prediabetes** | `15777000` | 105,573 | 35,191 | **29.92%** |
| `439777` | **Anemia** | `271737000` | 105,052 | 35,018 | **29.77%** |
| `316866` | **Hypertensive disorder** | `38341003` | 90,855 | 30,285 | **25.75%** |
| `257012` | **Chronic sinusitis** | `40055000` | 75,117 | 24,699 | **21.0%** |
| `4217975` | **Normal pregnancy** | `72892002` | 150,024 | 20,452 | **17.39%** |
| `4078393` | **Miscarriage** | `19169002` | 59,928 | 19,976 | **16.98%** |
| `28060` | **Streptococcal sore throat** | `43878008` | 51,105 | 15,526 | **13.2%** |
| `372328` | **Otitis media** | `65363002` | 54,705 | 13,415 | **11.41%** |
| `432867` | **Hyperlipidemia** | `55822004` | 39,843 | 13,281 | **11.29%** |
| `81151` | **Sprain of ankle** | `44465007` | 37,197 | 11,749 | **9.99%** |
| `4285898` | **Polyp of colon** | `68496003` | 28,347 | 8,530 | **7.25%** |
| `201826` | **Type 2 diabetes mellitus** | `44054006` | 24,450 | 8,150 | **6.93%** |
| `4120314` | **Hypertriglyceridemia** | `302870006` | 23,469 | 7,823 | **6.65%** |
| `436940` | **Metabolic syndrome X** | `237602007` | 23,082 | 7,694 | **6.54%** |
| `317576` | **Coronary arteriosclerosis** | `53741008` | 22,276 | 7,426 | **6.31%** |
| `378001` | **Concussion injury** | `62106007` | 20,946 | 6,769 | **5.76%** |
| `4294548` | **Acute viral pharyngitis** | `75498004` | 20,577 | 6,642 | **5.65%** |
| `381316` | **Stroke (Cerebrovascular accident)** | `230690007` | 19,860 | 6,620 | **5.63%** |
| `4283893` | **Sinusitis** | `36971009` | 20,328 | 6,548 | **5.57%** |
| `4214376` | **Hyperglycemia** | `80394007` | 18,783 | 6,261 | **5.32%** |
| `4079750` | **Osteoarthritis of knee** | `239873007` | 18,474 | 6,158 | **5.24%** |

## 6. Inter-Visit Cadence & Landmark Eligibility

- **Total Consecutive Visit Intervals:** 3,559,147.0
- **Median Inter-Visit Gap:** **60.0 days** (IQR: 21.0–286.0 days, Mean: 345.08 days)
- **Inter-Visit Gap Distribution:** Same-day: 1.15%, 1–180 days: 66.59%, 181–365 days: 14.99%, >365 days: 17.28%
- **Visits with Follow-up within 365 Days (`H=365`):** **82.73%**

### Landmark Eligibility Pool (Under Section 1.2 Criteria)
- **Total Distinct Candidate Visits:** 3,676,758
- **Visits with ≥ 1 Year Prior Observation:** 3,429,235 (93.3% of visits)
- **Eligible Landmarks (≥ 1 yr prior obs + ≥ 1 prior diagnosis):** **3,365,062** (91.5% of visits)
- **Eligible Landmarks with ≥ 365d Future Observation (`H=365`):** **2,906,281**
- **Eligible Landmarks with ≥ 180d Future Observation (`H=180`):** **3,067,203**
- **Inpatient Index Landmarks (`visit_concept_id = 9201`):** **133,674**
- **Inpatient or Emergency Index Landmarks (`visit_concept_id IN (9201, 9203)`):** **325,359**

## 7. Complete Table Schemas & Completeness

### Table: `person` (Raw rows: 235,222, Distinct: 117,611)
| Column Name | Data Type | Null Count | Null % | Completeness |
|---|---|---|---|---|
| `person_id` | `BIGINT` | 0 | 0.0% | 100% |
| `gender_concept_id` | `BIGINT` | 0 | 0.0% | 100% |
| `year_of_birth` | `BIGINT` | 0 | 0.0% | 100% |
| `month_of_birth` | `BIGINT` | 0 | 0.0% | 100% |
| `day_of_birth` | `BIGINT` | 0 | 0.0% | 100% |
| `birth_datetime` | `DATE` | 0 | 0.0% | 100% |
| `race_concept_id` | `BIGINT` | 0 | 0.0% | 100% |
| `ethnicity_concept_id` | `BIGINT` | 0 | 0.0% | 100% |
| `location_id` | `VARCHAR` | 235,222 | 100.0% | 0.0% |
| `provider_id` | `VARCHAR` | 235,222 | 100.0% | 0.0% |
| `care_site_id` | `VARCHAR` | 235,222 | 100.0% | 0.0% |
| `person_source_value` | `VARCHAR` | 0 | 0.0% | 100% |
| `gender_source_value` | `VARCHAR` | 0 | 0.0% | 100% |
| `gender_source_concept_id` | `BIGINT` | 0 | 0.0% | 100% |
| `race_source_value` | `VARCHAR` | 0 | 0.0% | 100% |
| `race_source_concept_id` | `BIGINT` | 0 | 0.0% | 100% |
| `ethnicity_source_value` | `VARCHAR` | 0 | 0.0% | 100% |
| `ethnicity_source_concept_id` | `BIGINT` | 0 | 0.0% | 100% |

### Table: `observation_period` (Raw rows: 235,222, Distinct: 117,611)
| Column Name | Data Type | Null Count | Null % | Completeness |
|---|---|---|---|---|
| `observation_period_id` | `BIGINT` | 0 | 0.0% | 100% |
| `person_id` | `BIGINT` | 0 | 0.0% | 100% |
| `observation_period_start_date` | `DATE` | 0 | 0.0% | 100% |
| `observation_period_end_date` | `DATE` | 0 | 0.0% | 100% |
| `period_type_concept_id` | `BIGINT` | 0 | 0.0% | 100% |

### Table: `condition_occurrence` (Raw rows: 2,644,530, Distinct: 1,763,020)
| Column Name | Data Type | Null Count | Null % | Completeness |
|---|---|---|---|---|
| `condition_occurrence_id` | `BIGINT` | 0 | 0.0% | 100% |
| `person_id` | `BIGINT` | 0 | 0.0% | 100% |
| `condition_concept_id` | `BIGINT` | 0 | 0.0% | 100% |
| `condition_start_date` | `DATE` | 0 | 0.0% | 100% |
| `condition_start_datetime` | `DATE` | 0 | 0.0% | 100% |
| `condition_end_date` | `DATE` | 1,271,463 | 48.08% | 51.9% |
| `condition_end_datetime` | `DATE` | 1,271,463 | 48.08% | 51.9% |
| `condition_type_concept_id` | `BIGINT` | 0 | 0.0% | 100% |
| `stop_reason` | `VARCHAR` | 2,644,530 | 100.0% | 0.0% |
| `provider_id` | `VARCHAR` | 2,644,530 | 100.0% | 0.0% |
| `visit_occurrence_id` | `BIGINT` | 3,045 | 0.12% | 99.9% |
| `visit_detail_id` | `BIGINT` | 0 | 0.0% | 100% |
| `condition_source_value` | `BIGINT` | 0 | 0.0% | 100% |
| `condition_source_concept_id` | `BIGINT` | 0 | 0.0% | 100% |
| `condition_status_source_value` | `VARCHAR` | 2,644,530 | 100.0% | 0.0% |
| `condition_status_concept_id` | `BIGINT` | 0 | 0.0% | 100% |

### Table: `visit_occurrence` (Raw rows: 11,030,274, Distinct: 3,676,758)
| Column Name | Data Type | Null Count | Null % | Completeness |
|---|---|---|---|---|
| `visit_occurrence_id` | `BIGINT` | 0 | 0.0% | 100% |
| `person_id` | `BIGINT` | 0 | 0.0% | 100% |
| `visit_concept_id` | `BIGINT` | 0 | 0.0% | 100% |
| `visit_start_date` | `DATE` | 0 | 0.0% | 100% |
| `visit_start_datetime` | `DATE` | 0 | 0.0% | 100% |
| `visit_end_date` | `DATE` | 0 | 0.0% | 100% |
| `visit_end_datetime` | `DATE` | 0 | 0.0% | 100% |
| `visit_type_concept_id` | `BIGINT` | 0 | 0.0% | 100% |
| `provider_id` | `VARCHAR` | 11,030,274 | 100.0% | 0.0% |
| `care_site_id` | `VARCHAR` | 11,030,274 | 100.0% | 0.0% |
| `visit_source_value` | `VARCHAR` | 0 | 0.0% | 100% |
| `visit_source_concept_id` | `BIGINT` | 0 | 0.0% | 100% |
| `admitting_source_concept_id` | `BIGINT` | 0 | 0.0% | 100% |
| `admitting_source_value` | `VARCHAR` | 11,030,274 | 100.0% | 0.0% |
| `discharge_to_concept_id` | `BIGINT` | 0 | 0.0% | 100% |
| `discharge_to_source_value` | `VARCHAR` | 11,030,274 | 100.0% | 0.0% |
| `preceding_visit_occurrence_id` | `BIGINT` | 235,222 | 2.13% | 97.9% |