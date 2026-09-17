# Synthea OMOP 100K Dataset Profile & Schema Inspection Report

*Generated At:* 2026-09-18T01:36:26.675729  
*Source Directory:* `synthea100k`  
*DuckDB Version:* `1.5.5`  

---

## 1. Executive Summary & Table Inventory

| Table Name | Raw Rows | Distinct Records | Columns | Role / Content |
|---|---|---|---|---|
| `person` | 235,222 | 117,611 | 18 | Primary OMOP CDM table (`person_id`) |
| `observation_period` | 235,222 | 117,611 | 5 | Primary OMOP CDM table (`observation_period_id`) |
| `condition_occurrence` | 2,644,530 | 1,763,020 | 16 | Primary OMOP CDM table (`condition_occurrence_id`) |
| `visit_occurrence` | 11,030,274 | 3,676,758 | 17 | Primary OMOP CDM table (`visit_occurrence_id`) |


## 2. Patient Demographics (`person`)

- **Total Unique Patients (`person_id`):** 117,611
- **Birth Year Range:** 1908 to 2019 (Median: 1973, IQR: 1954–1995)

### Sex / Gender Breakdown
| Concept ID | Description | Source Value | Count | Percentage |
|---|---|---|---|---|
| `8507` | MALE | `M` | 59,127 | 50.27% |
| `8532` | FEMALE | `F` | 58,484 | 49.73% |

### Race Breakdown
| Concept ID | Description | Source Value | Count | Percentage |
|---|---|---|---|---|
| `8527` | White | `white` | 89,692 | 76.26% |
| `0` | Unknown / Unspecified | `hispanic` | 11,485 | 9.77% |
| `8516` | Black or African American | `black` | 8,696 | 7.39% |
| `8515` | Asian | `asian` | 7,105 | 6.04% |
| `0` | Unknown / Unspecified | `native` | 517 | 0.44% |
| `0` | Unknown / Unspecified | `other` | 116 | 0.1% |

## 3. Observation Period (`observation_period`)

- **Total Distinct Observation Spans:** 117,611 across 117,611 patients (100% cohort coverage)
- **Dataset Time Horizon:** `1908-07-02` to `2019-05-21`
- **Patient Observation Length:** Median = **24.3 years** (8,877.0 days), Mean = **28.59 years**
- **Min / Max Observation:** 0 days to 40,357 days

## 4. Visits Profile (`visit_occurrence`)

- **Total Distinct Visit Records:** 3,676,758
- **Patients with >= 1 Visit:** 117,611 (100.0% of cohort)
- **Date Range:** `1908-07-02` to `2019-05-21`
- **Visits Per Patient:** Median = 22.0, Mean = 31.26, IQR = 15.0–37.0, Max = 1479.0

### Visit Types Breakdown
| Visit Concept ID | Description | Total Encounters | Unique Patients | Encounter % | Cohort Prev % |
|---|---|---|---|---|---|
| `9202` | **Outpatient Visit** | 3,331,255 | 117,611 | 90.6% | 100.0% |
| `9203` | **Emergency Room Visit** | 205,486 | 82,260 | 5.59% | 69.94% |
| `9201` | **Inpatient Visit** | 140,017 | 27,421 | 3.81% | 23.31% |

## 5. Conditions Profile (`condition_occurrence`)

- **Total Distinct Condition Records:** 2,644,529
- **Unique Patients with >= 1 Diagnosis:** 115,681 (98.4% of cohort)
- **Distinct Condition Concepts:** 144
- **Conditions Per Patient:** Median = 21.0, Mean = 22.86, Distinct Concepts/Patient = 6.0

### Top Conditions by Patient Prevalence
| Concept ID | Condition / Disease Name | Source Code | Total Events | Patient Count | Cohort Prevalence |
|---|---|---|---|---|---|
| `40481087` | **444814009** | `444814009` | 74,879 | 74,879 | **63.67%** |
| `0` | **Unknown / Unspecified** | `162864005` | 86,003 | 61,152 | **52.0%** |
| `4112343` | **Body mass index 30+ - obesity** | `195662009` | 52,544 | 52,544 | **44.68%** |
| `260139` | **10509002** | `10509002` | 45,760 | 45,760 | **38.91%** |
| `4311629` | **15777000** | `15777000` | 35,191 | 35,191 | **29.92%** |
| `439777` | **Anemia** | `271737000` | 35,018 | 35,018 | **29.77%** |
| `316866` | **Hypertensive disorder** | `38341003` | 30,285 | 30,285 | **25.75%** |
| `257012` | **40055000** | `40055000` | 24,699 | 24,699 | **21.0%** |
| `4217975` | **72892002** | `72892002` | 20,452 | 20,452 | **17.39%** |
| `4078393` | **19169002** | `19169002` | 19,976 | 19,976 | **16.98%** |
| `28060` | **Normal pregnancy** | `43878008` | 15,526 | 15,526 | **13.2%** |
| `372328` | **65363002** | `65363002` | 13,415 | 13,415 | **11.41%** |
| `432867` | **Hyperglycemia** | `55822004` | 13,281 | 13,281 | **11.29%** |
| `81151` | **44465007** | `44465007` | 11,749 | 11,749 | **9.99%** |
| `4285898` | **68496003** | `68496003` | 8,530 | 8,530 | **7.25%** |
| `201826` | **Type 2 diabetes mellitus** | `44054006` | 8,150 | 8,150 | **6.93%** |
| `4120314` | **302870006** | `302870006` | 7,823 | 7,823 | **6.65%** |
| `436940` | **237602007** | `237602007` | 7,694 | 7,694 | **6.54%** |
| `317576` | **Coronary arteriosclerosis** | `53741008` | 7,426 | 7,426 | **6.31%** |
| `378001` | **62106007** | `62106007` | 6,769 | 6,769 | **5.76%** |
| `4294548` | **75498004** | `75498004` | 6,642 | 6,642 | **5.65%** |
| `381316` | **230690007** | `230690007` | 6,620 | 6,620 | **5.63%** |
| `4283893` | **36971009** | `36971009` | 6,548 | 6,548 | **5.57%** |
| `4214376` | **80394007** | `80394007` | 6,261 | 6,261 | **5.32%** |
| `4079750` | **239873007** | `239873007` | 6,158 | 6,158 | **5.24%** |

## 6. Visit Cadence & ML Landmark Feasibility

- **Median Days Between Successive Visits:** 60.0 days (Mean: 345.08 days)
- **Consecutive Visit Pairs within 180 Days (H=180):** 67.73%
- **Consecutive Visit Pairs within 365 Days (H=365):** 82.72%

### Landmark Eligibility Pool (Under Section 1.2 Criteria)
- **Total Candidate Encounters:** 3,676,758
- **Eligible Landmarks (≥ 1 yr prior obs + ≥ 1 prior condition):** **3,365,062**
- **Eligible Landmarks with ≥ 365d Future Observation (`H=365`):** **2,906,281**
- **Eligible Landmarks with ≥ 180d Future Observation (`H=180`):** **3,067,203**
- **Inpatient Index Encounters (`visit_concept_id = 9201`):** 133,674
- **Inpatient or Emergency Encounters (`visit_concept_id IN (9201, 9203)`):** 325,359

## 7. Complete Table Schemas & Completeness

### Table: `person` (Raw: 235,222 rows, Distinct: 117,611)
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

### Table: `observation_period` (Raw: 235,222 rows, Distinct: 117,611)
| Column Name | Data Type | Null Count | Null % | Completeness |
|---|---|---|---|---|
| `observation_period_id` | `BIGINT` | 0 | 0.0% | 100% |
| `person_id` | `BIGINT` | 0 | 0.0% | 100% |
| `observation_period_start_date` | `DATE` | 0 | 0.0% | 100% |
| `observation_period_end_date` | `DATE` | 0 | 0.0% | 100% |
| `period_type_concept_id` | `BIGINT` | 0 | 0.0% | 100% |

### Table: `condition_occurrence` (Raw: 2,644,530 rows, Distinct: 1,763,020)
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

### Table: `visit_occurrence` (Raw: 11,030,274 rows, Distinct: 3,676,758)
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