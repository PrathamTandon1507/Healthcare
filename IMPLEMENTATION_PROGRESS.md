# Comorbidity Ensemble ML Implementation Progress

Tracking implementation and validation of the 20-phase ML architecture specified in `COMORBIDITY_ENSEMBLE_ML_PLAN.md`.

---

## Phase Status Summary

- [x] **Phase 1 — Dataset / Schema Inspection**: [COMPLETED & AUDITED]
- [x] **Phase 2 — Patient Timeline Construction**: [COMPLETED & AUDITED]
- [x] **Phase 3 — Landmark & Label Generation**: [COMPLETED & VALIDATED]
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

## Phase 3 Execution & Validation Log

### 1. What was Implemented & Validated
- **Landmark Selection Module (`src/data/landmarks.py`)**:
  - Deterministic landmark identity: `(person_id, visit_occurrence_id, landmark_date)`.
  - Enforced eligibility criteria: $\ge 1$ year prior observation ($T - T_{obs\_start} \ge 365\text{ days}$) and $\ge 1$ prior condition diagnosed on or before $T$.
  - Extracted and characterized two distinct candidate cohorts:
    - **Cohort A (Inpatient / ED: 9201, 9203)**: 325,259 eligible landmarks across 80,467 distinct patients.
    - **Cohort B (General Encounters: all types)**: 3,364,928 eligible landmarks across 115,223 distinct patients.
  - Future observation completeness tracking: explicit `future_observation_complete` boolean flag ($T_{obs\_end} - T \ge 365\text{ days}$).
- **Outcome Label Construction Module (`src/data/labels.py`)**:
  - Evaluated empirical 365-day incidence across all 143 condition concepts in Synthea 100K.
  - Strictly enforced pre-existing disease exclusion: conditions present at or before $T$ are masked to $0$ and never assigned as positive incident comorbidities.
  - Newly diagnosed conditions in $(T, T + 365\text{ days}]$ assigned $\text{target\_<concept\_id>} = 1$.
  - Formatted multi-label binary dataset using high-performance DuckDB vectorized list expressions (`list_contains`).
- **Pipeline Script & Materialization (`scripts/build_prediction_dataset.py`)**:
  - Materialized Parquet datasets with curated comorbidity targets:
    - `data/parquet/prediction_landmarks.parquet` (General cohort, 134.58 MB, 3,364,928 rows $\times$ 41 curated target disease columns).
    - `data/parquet/prediction_landmarks_inpatient_ed.parquet` (Inpatient/ED cohort, 13.38 MB, 325,259 rows $\times$ 41 curated target disease columns).
  - Generated reports:
    - `reports/landmark_cohort_profile.md`
    - `reports/target_incidence.md` (Full 143-condition table + Curated comorbidity table + Excluded conditions table).
    - `reports/target_incidence.json`
    - `reports/phase3_label_validation.md` (18 detailed manual audit cases).

---

### 2. Methodological & Numerical Reconciliations

1. **$144 \rightarrow 143$ Distinct Condition Concepts**:
   - In raw `condition_occurrence`, 144 distinct `condition_concept_id` values exist, including concept `0` (`No matching concept` / unmapped source strings).
   - Concept `0` represents unmapped administrative or free-text diagnoses without clinical definitions. It is excluded from the modeled target space, leaving **143 valid clinical condition concepts**.

2. **$325,359 \rightarrow 325,259$ Cohort A Landmarks ($\Delta = 100$)**:
   - In Phase 2 exploratory profiling, any visit row with $\ge 1$ condition row in history (including concept `0`) was counted as 325,359.
   - Under strict Phase 3 eligibility requiring $\ge 1$ *valid, non-zero* distinct condition concept diagnosed on or before $T$, exactly 100 landmarks whose only historical condition was concept `0` were excluded, yielding **325,259 fully eligible landmarks**.

3. **$3,365,062 \rightarrow 3,364,928$ Cohort B Landmarks ($\Delta = 134$)**:
   - In Cohort B, 134 landmarks had only concept `0` in their pre-landmark history and were excluded under strict eligibility, yielding **3,364,928 eligible landmarks**.

---

### 3. Target Disease Space Curation (Clinical + Statistical Criteria)

Rather than selecting targets purely by frequency or arbitrarily setting $K$, candidate conditions were filtered by **both** empirical statistical counts ($\ge 100$ positive landmarks in Cohort A) and **clinical suitability** for the comorbidity prediction task:
- **Total Condition Concepts Evaluated**: 143
- **Statistically Qualifying Concepts ($\ge 100$ positives)**: 86
- **Curated Chronic Comorbidity Targets**: **41 targets** (Retained for prediction ML models)
- **Excluded Non-Comorbid Conditions**: **45 conditions** (Filtered out)

#### Summary of Excluded Conditions:
1. **Acute / Transient Infections (10 conditions)**: *Viral sinusitis*, *Acute bronchitis*, *Streptococcal sore throat*, *Acute viral pharyngitis*, *Otitis media*, *Acute URI*, *Cystitis*, *Appendicitis*, *Infectious process*, *Acute allergic reaction*.
2. **Acute Mechanical Trauma & Injuries (21 conditions)**: *Rib fracture*, *Ankle sprain*, *Wrist sprain*, *Upper limb fracture*, *Clavicle fracture*, *Wrist closed fracture*, *Ankle fracture*, *Forearm fracture*, *Whiplash neck injury*, *Lacerations (foot, forearm, hand, facial, thigh)*, *Burn injuries (1st, 2nd, 3rd degree)*, *Concussions*, *Patellar tendon rupture*, *Drug overdose / poisonings*.
3. **Obstetric & Pregnancy (8 conditions)**: *Normal pregnancy*, *Miscarriage / Complete miscarriage*, *Tubal pregnancy*, *Pre-eclampsia*, *Eclampsia in pregnancy*, *High risk pregnancy*.
4. **Administrative / Non-Disease Findings (5 conditions)**: *Normal BMI*, *Suspected condition*, *Suspected respiratory finding*, *Postoperative state*.

#### Curated Comorbidity Target Space (K = 41):
- **Cardiometabolic & Endocrine (10)**: *Prediabetes*, *Coronary Arteriosclerosis*, *Hyperlipidemia*, *Essential Hypertension*, *Metabolic Syndrome X*, *Hypertriglyceridemia*, *Hyperglycemia*, *Type 2 Diabetes Mellitus*, *Congestive Heart Failure*, *Cardiac Arrest*.
- **Diabetic Complications (2)**: *Diabetic Neuropathy*, *Diabetic Retinopathy*.
- **Renal (2)**: *Chronic Kidney Disease*, *CKD Stage 1*.
- **Neurological & Mental Health (6)**: *Alzheimer's Disease*, *Stroke (CVA)*, *Familial Alzheimer's*, *Epilepsy / Seizure Disorder*, *Seizure Disorder*, *Childhood ADHD*.
- **Chronic Respiratory & Allergic (4)**: *Chronic Sinusitis*, *Sinusitis*, *Chronic Obstructive Bronchitis (COPD)*, *Childhood Asthma*.
- **Musculoskeletal & Degenerative (6)**: *Chronic Intractable Migraine*, *Chronic Pain*, *Osteoporosis*, *Osteoarthritis of Knee*, *Localized Osteoarthritis of Hand*, *Osteoarthritis of Hip*.
- **Oncology & Pre-Malignant Neoplasms (10)**: *Polyp of Colon*, *Recurrent Rectal Polyp*, *Non-Small Cell Lung Cancer*, *NSCLC Stage 1*, *Small Cell Lung Cancer*, *SCLC Stage 1*, *Neoplasm of Prostate*, *Carcinoma in situ of Prostate*, *Malignant Neoplasm of Colon*, *Primary Malignant Neoplasm of Colon*.
- **Hematology (1)**: *Anemia*.

---

### 4. Automated Test Results
- Ran `pytest -v tests/test_landmarks.py tests/test_timeline.py`
- **16/16 tests PASSED**:
  1. `test_landmark_integrity_and_uniqueness`: Passed (unique landmark IDs, 1-to-1 visit mapping).
  2. `test_temporal_observation_bounds`: Passed (landmark date within observation bounds).
  3. `test_censoring_flag_accuracy`: Passed (incomplete future observation accurately flagged).
  4. `test_existing_disease_masking_rule`: Passed (pre-existing conditions strictly masked to 0).
  5. `test_incident_disease_positive_label_rule`: Passed (new diagnoses in window receive label = 1).
  6. `test_outside_window_diagnoses_not_labeled`: Passed (diagnoses after $T + 365$ receive label = 0).
  7. `test_target_dataset_reproducibility`: Passed (deterministic Parquet rows and sums).
  8. `test_patient_integrity`: Passed.
  9. `test_chronological_ordering`: Passed.
  10. `test_no_cross_patient_joins`: Passed.
  11. `test_date_validity`: Passed.
  12. `test_pipeline_reproducibility`: Passed.
  13. `test_source_consistency`: Passed.
  14. `test_demographics_count_consistency`: Passed.
  15. `test_no_join_multiplication_in_landmarks`: Passed.
  16. `test_temporal_non_leakage_and_label_masking`: Passed.

---

### 5. Git Commits & Push Log
- Code, scripts, reports, and tests staged and committed.
- Pushed to `https://github.com/PrathamTandon1507/Healthcare.git` (`origin/main`).
