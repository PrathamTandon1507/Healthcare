# Comorbidity Ensemble ML Implementation Progress

Tracking implementation and validation of the 20-phase ML architecture specified in `COMORBIDITY_ENSEMBLE_ML_PLAN.md`.

---

## Phase Status Summary

- [x] **Phase 1 — Dataset / Schema Inspection**: [COMPLETED & AUDITED]
- [x] **Phase 2 — Patient Timeline Construction**: [COMPLETED & AUDITED]
- [ ] **Phase 3 — Landmark & Label Generation**: [NOT STARTED]
- [ ] **Phase 4 — Feature Engineering**: [NOT STARTED]
- [ ] **Phase 5 — Train / Validation / Test Splitting**: [NOT STARTED]
- [ ] **Phase 6 — Baseline Models**: [NOT STARTED]
- [ ] **Phase 7 — Logistic Regression Base Model**: [NOT STARTED]
- [ ] **Phase 8 — Random Forest Base Model**: [NOT STARTED]
- [ ] **Phase 9 — XGBoost Base Model**: [NOT STARTED]
- [ ] **Phase 10 — Proper Stacked Ensemble (OOF)**: [NOT STARTED]
- [ ] **Phase 11 — Hyperparameter Tuning Finalization**: [NOT STARTED]
- [ ] **Phase 12 — Calibration**: [NOT STARTED]
- [ ] **Phase 13 — Explainability**: [NOT STARTED]
- [ ] **Phase 14 — Evaluation**: [NOT STARTED]
- [ ] **Phase 15 — Ablation Experiments**: [NOT STARTED]
- [ ] **Phase 16 — Model Packaging**: [NOT STARTED]
- [ ] **Phase 17 — Inference Pipeline**: [NOT STARTED]
- [ ] **Phase 18 — Streamlit Integration**: [NOT STARTED]
- [ ] **Phase 19 — Testing & Leakage Audits**: [NOT STARTED]
- [ ] **Phase 20 — Final Experiment & Reproducibility Pass**: [NOT STARTED]

---

## Phase 1 & 2 Focused Validation Audit Log

### 1. Inconsistencies Investigated & Resolved

#### A. Patient Demographic Counts
- **Issue**: Walkthrough text previously listed Male: 8,507 and Female: 8,532 (which was a copy-paste error copying the concept IDs `8507` and `8532` rather than patient counts).
- **Resolution**: Audited against `person` table. Total unique patients = **117,611**.
  - **Male** (`gender_concept_id = 8507`, source `'M'`): **59,127 patients (50.27%)**
  - **Female** (`gender_concept_id = 8532`, source `'F'`): **58,484 patients (49.73%)**
  - **Total**: $59,127 + 58,484 = 117,611$ (100.0%, 0 missing).
  - Race breakdown: White = 89,692 (76.26%), Hispanic = 11,485 (9.77%), Black = 8,696 (7.39%), Asian = 7,105 (6.04%), Native = 517 (0.44%), Other = 116 (0.10%).

#### B. Visit Counts vs. Landmark Count
- **Issue**: Report previously stated 3,676,758 distinct visits vs 20.1M candidate encounters due to raw file block duplications in un-deduplicated queries ($11\text{M visits} \times 2\text{ observation records} = 22\text{M rows}$).
- **Resolution**: Deduplicated entities by primary keys (`visit_occurrence_id`, `observation_period_id`, `person_id`).
  - **Total distinct visits**: **3,676,758** across all 117,611 patients.
  - **Visits with $\ge 1$ year prior observation**: **3,429,235** (93.27%).
  - **Total eligible landmarks ($\ge 1$ yr prior obs + $\ge 1$ prior condition)**: **3,365,062** (91.52% of visits).
  - **Eligible landmarks with $\ge 365$d future observation ($H=365$)**: **2,906,281**.
  - **Eligible landmarks with $\ge 180$d future observation ($H=180$)**: **3,067,203**.
  - **Eligible Inpatient index encounters (`visit_concept_id = 9201`)**: **133,674**.
  - **Eligible Inpatient or Emergency index encounters (`visit_concept_id IN (9201, 9203)`)**: **325,359**.

#### C. Observation Period Semantics & Inter-Visit Cadence
- **Issue**: Describing the 24.3-year span as "continuous history" was imprecise.
- **Resolution**: Clarified that 24.3 years represents the **median observation-period span** (enrollment/coverage window). Quantified actual discrete encounter cadence:
  - Total inter-visit intervals: 3,559,147.
  - **Median gap between consecutive visits**: **60.0 days** (IQR: 21–286 days, Mean: 345.1 days).
  - 82.72% of all consecutive visits occur within 365 days of each other.

#### D. Human-Readable Condition Vocabulary
- **Issue**: Condition concepts in sample timelines and reports were partially displayed as numeric codes.
- **Resolution**: Built a comprehensive SNOMED CT and OMOP concept dictionary covering all 159 distinct condition concepts/source codes present in Synthea 100K. All reports now format conditions as:
  `Condition Name (concept_id: XXXXX, source_code: XXXXX)`.

#### E. Temporal Landmark & Pre-existing Masking Audit
- **Implemented**: `scripts/generate_validation_audit.py` and `reports/phase2_validation_audit.md`.
- **Verified**:
  - For each landmark at time $T$, feature history strictly contains records with `timestamp <= T`.
  - Zero future records leak into pre-landmark features.
  - Candidate comorbidity labels strictly belong to $(T, T + 365\text{ days}]$.
  - Pre-existing conditions diagnosed on or before $T$ are masked/excluded from future incident comorbidity labels.
  - Repeated occurrences of an incident condition within $(T, T + 365]$ are binarized to 1.

---

## 2. Automated Test Results

Executed `pytest -v tests/test_timeline.py`:
- `test_patient_integrity` [PASSED]
- `test_chronological_ordering` [PASSED]
- `test_no_cross_patient_joins` [PASSED]
- `test_date_validity` [PASSED]
- `test_pipeline_reproducibility` [PASSED]
- `test_source_consistency` [PASSED]
- `test_demographics_count_consistency` [PASSED]
- `test_no_join_multiplication_in_landmarks` [PASSED]
- `test_temporal_non_leakage_and_label_masking` [PASSED]

**All 9 automated validation tests PASSED.**

---

## 3. Deliverables & Reports

1. `reports/data_profile.json`: Machine-readable dataset profile.
2. `reports/data_profile.md`: Formatted schema profile and cohort statistics.
3. `reports/sample_patient_timelines.md`: Formatted patient trajectories for 15 diverse patients.
4. `reports/phase2_validation_audit.md`: Detailed temporal and landmark validation audit across 10 sample patients.
5. `src/data/lzo_util.py`: LZO decompressor & Parquet converter.
6. `src/data/loader.py`: Centralized DuckDB query interface.
7. `src/data/timeline.py`: Deduplicated chronological patient timeline builder.
8. `tests/test_timeline.py`: Automated 9-suite validation test battery.
