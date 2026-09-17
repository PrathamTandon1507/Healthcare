# Landmark Cohort Characterization Report

*Generated At:* 2026-09-18T02:15:27.520535  
*Specification:* `COMORBIDITY_ENSEMBLE_ML_PLAN.md` (Sections 1.2, 1.3, 1.5)  

---

## 1. Executive Cohort Comparison

| Metric | Cohort A: Inpatient / ED (`9201, 9203`) | Cohort B: General Encounters (All Types) | Interpretation / Design Role |
|---|---|---|---|
| **Eligible Index Landmarks** | **325,259** | **3,364,928** | Total candidate prediction points |
| **Distinct Patients** | **80,467** | **115,223** | Patient cohort size passing eligibility |
| **Fully Observed Landmarks ($H=365$d)** | **259,889** (79.9%) | **2,906,150** (86.4%) | Primary complete-window prediction pool |
| **Censored Landmarks ($< 365$d future obs)** | **65,370** (20.1%) | **458,778** (13.6%) | Incomplete future observation window |
| **Patient Age at Landmark** | Median: **51.0y** (Mean: 49.87y) | Median: **47.0y** (Mean: 45.91y) | Age distribution at index encounter |
| **Prior Observation History** | Median: **31.84 yrs** (Mean: 34.22y) | Median: **27.41 yrs** (Mean: 30.85y) | Pre-landmark history length |
| **Pre-existing Diagnoses at $T$** | Median: **7.0** (Mean: 8.23) | Median: **5.0** (Mean: 6.68) | Chronic comorbidity load at index |
| **Landmark Multiplicity per Patient** | Median: **2.0** (Mean: 4.04) | Median: **19.0** (Mean: 29.2) | Repeated snapshots per patient |
| **Calendar Window** | `1910-02-08` to `2019-05-17` | `1909-09-09` to `2019-05-21` | Full dataset longitudinal span |

---

## 2. Landmark Multiplicity & Patient-Level Distribution

Because a single patient may contribute multiple index encounters across their lifetime, the table below documents the distribution of landmarks per patient:

| Statistic | Cohort A (Inpatient/ED) | Cohort B (General) |
|---|---|---|
| Patients with exactly 1 landmark | 31,608 (39.3%) | 360 (0.3%) |
| Patients with > 1 landmarks | 48,859 (60.7%) | 114,863 (99.7%) |
| 25th Percentile | 1.0 | 12.0 |
| Median (50th Percentile) | **2.0** | **19.0** |
| 75th Percentile | 3.0 | 35.0 |
| 90th Percentile | 6.0 | 58.0 |
| Maximum landmarks for 1 patient | 364 | 1478 |

> [!NOTE]
> This multiplicity distribution confirms that **patient-level splitting** (rather than row-level splitting) is strictly required in Phase 5 to prevent cross-split data leakage.
