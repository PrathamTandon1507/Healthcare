# Comorbidity Network + Prediction Tool
## ML / Ensemble Component — Implementation Blueprint

**Scope of this document:** the network-augmented stacked ensemble that predicts diseases likely to appear in a patient's subsequent admission. The disease-network/graph construction pipeline is treated as an external module with a defined interface, not implemented here. The deep-learning baseline and RR-only network baseline are also out of scope; they are named where relevant so the ML pipeline stays compatible with the eventual full benchmark.

**Dataset:** Synthea OMOP 23M (synthetic, OMOP CDM schema), not MIMIC-IV. Every design decision below is re-derived for Synthea/OMOP rather than carried over from the original MIMIC-IV framing in the presentation — the two datasets differ enough (ICU stays vs. lifetime longitudinal care, real vs. synthetic, no ground-truth clinical ambiguity) that assumptions must be re-justified.

---

## 0. Reading the source presentation into ML requirements

From the attached deck, three commitments constrain this plan and are treated as fixed requirements, not optional design choices:

1. **Ensemble identity**: stacked ensemble of XGBoost + Random Forest + Logistic Regression base learners, Logistic Regression meta-learner. The plan is free to *justify or amend* this, but any deviation must be argued for explicitly (Section 4).
2. **Explainability contract**: a prediction must be explainable as "disease X predicted because of network-derived relationship with existing conditions A, B, plus model-level feature importance" — i.e., the explanation must separate the *network-relationship* contribution from the *general feature* contribution. This shapes the explainability design in Section 13.
3. **Eventual benchmarking**: network-only (RR) scoring, conventional ML, deep learning, and an ablation study isolating network-feature value. Not built now, but the ML pipeline's baselines (Section 11) and ablation groups (Section 12) are designed to slot into that comparison later without rework.

---

## 1. Defining the prediction task

### 1.1 Why the MIMIC-IV framing doesn't transfer directly

The original framing ("predict diseases likely to appear in a patient's subsequent admission") was built around MIMIC-IV, where "admission" means a discrete ICU/hospital stay and patients typically have a small number of admissions over a short critical-care window. Synthea/OMOP patients instead have **lifelong longitudinal records** — a mix of outpatient wellness visits, ED visits, inpatient stays, and specialist visits, often years apart. Two consequences:

- "The next admission" is not a well-defined, densely-populated event for most Synthea patients the way it is in an ICU cohort. Many patients have zero or one inpatient encounter their entire synthetic lifetime.
- Synthea encounter timing is generated from disease modules on population-health schedules, not real clinical urgency — so treating "next visit" as a tight, information-rich prediction target (as in ICU 30-day-readmission style tasks) overstates what the data actually encodes.

**Resolution:** keep the clinical intent ("what will this patient be newly diagnosed with going forward") but operationalize it as a **fixed-horizon future-diagnosis prediction**, anchored at a **landmark point** in each patient's timeline, rather than strictly "the next single visit record." This is both more robust to Synthea's irregular visit cadence and more faithful to what the Streamlit tool actually needs to do (a user enters a *snapshot* of a patient — not a specific next-visit date — and wants "what should I watch for going forward").

### 1.2 Prediction point (landmark) definition

- For each patient, one or more **landmark dates** are chosen from their `visit_occurrence` timeline. A landmark is defined as **the end date of an eligible index encounter** (inpatient or ED preferred, since these are the visits most analogous to "an admission"; fallback to any visit type if a patient has no inpatient/ED visits at all, flagged as a distinct cohort stratum).
- Eligibility filters for an index encounter:
  - Patient must have **≥ 1 year of prior observation** (`observation_period`) before the landmark, so "current diagnoses" is a meaningful, non-truncated history rather than an artifact of just having joined the dataset.
  - Patient must have **≥ 1 condition_occurrence** recorded before the landmark (a patient with zero history has nothing for the model, or the network module, to work with — these go into a documented "cold start" exclusion, not silently dropped).
- **Multiple landmarks per patient** are allowed (e.g., one per inpatient/ED encounter in a patient's record) to increase sample size — Synthea has far fewer distinct patients than raw rows, so single-landmark-per-patient would waste most of the signal. This directly motivates the patient-level (not sample-level) splitting strategy in Section 7.

### 1.3 "Subsequent admission" and the prediction horizon

- Define the **outcome window** as **[landmark, landmark + H]** for a horizon `H`. Recommended default: **H = 365 days**, with **H = 180 days** run as a sensitivity check during development.
  - Rationale for a fixed horizon over "next visit, whenever it occurs": an unbounded "next visit" target lets the label depend on how soon a patient happens to return, which is itself informative of severity and would let the model implicitly learn "this patient returns quickly" rather than "this patient will develop this disease" — a subtle form of target leakage through visit-timing artifacts. A fixed calendar horizon decouples the label from arbitrary future visit spacing.
- Within the outcome window, the **"subsequent admission"** is operationalized as **any encounter** in the window (inpatient, ED, or outpatient) in which a qualifying diagnosis is recorded — not restricted to only inpatient encounters, because Synthea often records new-onset chronic disease first at an outpatient or ED visit rather than an inpatient stay. Restricting to inpatient-only would bias the label toward acute/severe conditions and undercount the exact kind of chronic comorbidity progression (e.g., diabetes → CKD) the project cares about.
- Patients with **no encounters at all** in the outcome window are **not** automatically treated as negative for every disease — they are excluded from that landmark's label computation (label = missing, not 0) if they also lack sufficient continued observation (`observation_period` coverage) through the window, since "no visit" and "no continued enrollment" are indistinguishable from "definitely didn't get sick" in a way that would poison negatives. If the patient has continued observation coverage through the window but no diagnosis, it is a legitimate negative.

### 1.4 Target disease definition

- **Target label space** = a curated set of **K clinically meaningful condition groups**, not raw OMOP `condition_concept_id`s (there are tens of thousands of these, at every granularity from "essential hypertension" to ultra-specific ICD-10 leaf codes). Concepts are rolled up to a coarser, clinically interpretable grouping — either OMOP's standard condition hierarchy (ancestor concepts / SNOMED "clinical finding" groupings via `concept_ancestor`) or a manually curated chronic-disease list matching the project's own narrative examples (diabetes, hypertension, CKD, COPD, stroke, etc.), consistent with the "disease X predicted from disease Y/Z" explanation style shown in the deck.
- `K` is chosen empirically after schema inspection and prevalence analysis (Phase 1), not assumed up front — but the design targets **on the order of 30–75 target diseases**: high enough to be clinically useful and to give the network module something structurally interesting to connect, low enough that per-disease stacked ensembles (Section 4) remain computationally and interpretably tractable. Diseases below a minimum positive-case threshold in the training split are dropped from the label space rather than modeled with too few positives (Section 9).

### 1.5 Handling diseases the patient already has

- **A disease already present in the patient's pre-landmark history is excluded from that landmark's candidate label set** (both as a feature-space output and as something the model is scored on). Predicting "will this chronic, already-diagnosed disease appear" is trivially true and clinically uninteresting, and would flood the model with easy, leakage-adjacent positives.
- Exception, explicitly modeled as a **separate, secondary framing**, not the primary target: **recurrence/exacerbation** of an already-present condition (relevant for a small set of relapsing/remitting conditions) is out of scope for the primary deliverable and only revisited if time allows after the primary incident-comorbidity task is working end-to-end.
- Practical effect: the model's target vector for a given landmark has support only over the subset of the K target diseases the patient **does not already have**, and its predicted-risk output for a disease the patient already has is simply not surfaced in the Streamlit UI for that patient (masked at inference, not before — the masking is a display-time and evaluation-time operation, not a training-time filter, so the same trained model works for every patient regardless of which subset of diseases they already carry).

### 1.6 Handling repeated diagnoses within the outcome window

- The label is **binarized per target disease per landmark**: 1 if the disease is newly recorded (first-ever occurrence for that patient) at least once inside the outcome window, 0 otherwise. Multiple occurrences of the same new diagnosis within the window (e.g., recorded at both an ED visit and a follow-up) do not create multiple positive labels — this is a single incident-comorbidity event, and modeling visit-count as the outcome would conflate "got the disease" with "how many times it was billed/recorded," which is a coding/administrative artifact, not a clinical outcome worth predicting.

### 1.7 Multi-label vs. one-vs-rest — decision and justification

- **Decision: one-vs-rest binary formulation, one independent stacked ensemble per target disease**, sharing the same upstream feature pipeline.
- Why not a single joint multi-label/multi-output model:
  - The explainability contract (Section 0.2) requires per-disease explanations that name *which existing diagnoses and which network relationships* drove *that specific disease's* score. A shared multi-output model (e.g., one XGBoost with 30 output heads) makes this harder to attribute cleanly, and SHAP-based per-label attribution effectively degenerates back to per-label analysis anyway.
  - Class imbalance and prevalence vary hugely across target diseases (Section 9); independent models let per-disease decisions (base rate handling, threshold, calibration) be tuned per label instead of forcing one global compromise.
  - The requested architecture (LR meta-learner over XGBoost/RF/LR base learners) is a **binary-classification stacking recipe**; forcing it into a single multi-label head loses the clean OOF-stacking procedure in Section 5, or requires a much more complex multi-label stacking scheme that isn't what was specified.
- Cost, acknowledged directly: training/maintaining `K` independent 4-model stacks (3 base + 1 meta) is `4K` models, plus `K` calibrators. This is deliberately kept feasible by capping `K` (Section 1.4) and by sharing all feature engineering, encoders, and cross-validation folds across every per-disease model (Section 18) — only the label vector changes per disease, not the pipeline.
- The K independent probabilities are then **assembled into one ranked list per patient** ("top-N most likely new diagnoses"), which is what the Streamlit tool actually needs to display — so one-vs-rest is not just easier to implement, it's a more natural match to the product requirement than a joint multi-label score would be.

---

## 2. Feature design (what the Streamlit form can actually provide)

This is the section the plan is most insistent on: **no feature may be used in training that cannot be reconstructed from a plausible Streamlit form input at inference time.** Every OMOP-derivable feature is explicitly bucketed below.

### 2.1 User-input features (entered directly on the form)

| Feature | OMOP source | Notes |
|---|---|---|
| Age at landmark | `person.birth_datetime` vs. landmark date | Computed from a birth year/date the user enters, or a direct age field |
| Sex | `person.gender_concept_id` | Standard concept, form dropdown |
| Race / ethnicity *(optional, flagged for ablation)* | `person.race_concept_id`, `ethnicity_concept_id` | Included only if schema inspection shows non-trivial, non-degenerate coverage in Synthea; evaluated for fairness implications before use, not assumed benign |
| Current diagnoses (multi-select list) | `condition_occurrence` before landmark, rolled up to the same K-disease grouping (plus an "other/none of these" bucket) | This is the single most important feature group — see 2.2 |
| Current medications *(optional, stretch)* | `drug_exposure` before landmark, rolled up to major drug classes | Only included if it survives the leakage and usefulness check in 2.2; a "skip" option is fine on the form |

### 2.2 Derived features (computed from the user's inputs, not entered directly)

- **Multi-hot diagnosis vector** over the K target diseases *plus a broader "background comorbidity" set* (patients often have relevant conditions — e.g., obesity, hyperlipidemia — that aren't themselves prediction targets but are informative predictors). The background set is chosen from prevalence analysis in Phase 1, not the same K used for targets.
- **Comorbidity count** (total number of distinct chronic conditions currently recorded) — a simple, well-known predictor of future morbidity, cheap to derive, easy for the user to have implicitly provided by ticking boxes.
- **Age bucket** (e.g., decade bins) as a categorical companion to raw age, useful for both LR and tree models and for network features that may be age-stratified.
- **Pairwise/interaction indicators** for clinically standard comorbidity combinations (e.g., diabetes AND hypertension both present) — cheap, interpretable, and directly supports the "CKD predicted partly because of existing diabetes and hypertension" style explanation even before network features are wired in.
- **Time-since-diagnosis features are explicitly NOT used**, even though they exist in the raw data (`condition_start_date`), because a realistic Streamlit form asks "does the patient currently have condition X" as a checkbox, not "on what date was X first diagnosed." Requiring exact diagnosis dates from a form user is unrealistic and would make the trained model unusable at inference. If a coarse recency band (e.g., "diagnosed within the last year" vs. "longstanding") is judged useful and easy enough for a user to answer, it can be added as an **optional** field with its own ablation — but the core model must work without it.

### 2.3 Future / unavailable features — explicitly excluded from training

These exist in Synthea/OMOP and would inflate offline metrics if used, but are **unavailable at real inference time** and must never enter the feature matrix:

- Anything with a timestamp **after** the landmark date: subsequent `condition_occurrence`, `drug_exposure`, `measurement`, `observation`, `procedure_occurrence`, `visit_occurrence` rows.
- Outcome-adjacent administrative fields that indirectly encode future utilization (e.g., total future visit count, discharge disposition of the *outcome-window* encounter).
- Any lab/measurement value that would only be ordered *because* the clinician already suspects the outcome disease (a common and easy-to-miss leakage path — e.g., an elevated creatinine test ordered in the outcome window because CKD is already being worked up counts as "future," not "current," data).
- Mortality / death table fields relative to the landmark, unless explicitly modeling a mortality-censoring adjustment (see Section 6).

### 2.4 Network-derived features — interface only (not computed here)

The graph/network module is being built separately, but the ML pipeline is designed against a **fixed contract** so the two can be integrated without reworking the ensemble later.

**Conceptual pipeline placement:**

```
[ Patient demographics + current diagnosis set S ]
                     │
                     ├──────────────► [ Direct / derived features, Section 2.1–2.2 ]
                     │
                     └──────────────► [ Network module: S, target disease T  →  network feature vector ]
                                                        │
                                                        ▼
                             [ Concatenated feature vector → ML ensemble, Section 4 ]
```

**Interface contract** (the network module must implement a function conceptually shaped like `get_network_features(existing_diagnoses: set[disease_id], target_disease: disease_id, cohort_filter: {age_band, sex}) -> dict[str, float]`), returning a fixed-length, fixed-name feature vector for every `(patient snapshot, candidate target disease)` pair. Candidate feature fields for that vector, to be finalized by the network team but scoped here so the ML side can build against a stable schema:

| Candidate network feature | Intuition |
|---|---|
| `max_relative_risk(S, T)` | Strongest single existing-diagnosis → target-disease association |
| `mean_relative_risk(S, T)` | Aggregate association strength across all existing diagnoses |
| `n_significant_edges(S, T)` | Count of existing diagnoses with an FDR-significant edge to T |
| `shortest_path_length(S, T)` | Network-distance proxy; smaller = more directly linked |
| `personalized_pagerank(S, T)` | Diffusion-based relevance of T given the whole existing-diagnosis set, not just the single best edge |
| `target_degree_centrality(T)` | Is T a network hub in general (independent of this patient) |
| `target_community_overlap(S, T)` | Whether T shares a detected cluster/community with any existing diagnosis |
| `strongest_source_disease(S, T)` | *Categorical, for explanation only* — which existing diagnosis drove `max_relative_risk`; not fed into the model as a number, but plumbed straight through to the explanation layer (Section 13) |

- **Stub/mock policy for this phase:** until the network module exists, this interface returns a **documented placeholder** (e.g., all-zero or population-mean-imputed vector, with a `network_features_available: bool` flag feature) so the ensemble, stacking, and evaluation code can be built, tested, and even partially benchmarked (the "demographics + diagnoses only" ablation arm, Section 12) without blocking on the graph team. Swapping the stub for the real module later should require touching **only** the network-feature-computation call site, not the model or training code — enforced by keeping this function behind one clearly named module (`src/features/network_interface.py`).
- **Leakage constraint the network module must honor** (stated here so it's not lost between the two workstreams): the network itself must be fit on a **training-period-only, patient-disjoint** slice of data relative to whatever split the ML pipeline uses (Section 6, "network-feature leakage"). This plan does not implement that guarantee, but the interface signature above assumes a network object that has already been fit under that constraint before `get_network_features` is called.

---

## 3. Ensemble architecture recommendation (evaluated, not assumed)

### 3.1 Base learners — why each, and what it complements

- **Logistic Regression**: a well-calibrated, low-variance linear baseline; strong on the multi-hot diagnosis/demographic feature space, which is largely linear-additive in effect (each existing condition nudges risk somewhat independently). Also the most directly interpretable base learner (raw coefficients), useful as a sanity check against the tree models' SHAP output.
- **Random Forest**: captures non-linear interactions and threshold effects (e.g., "diabetes AND hypertension AND age > 60" behaving differently than the linear sum of parts) without needing explicit interaction terms; robust to the mix of binary, categorical, and continuous (network-score) features without heavy scaling requirements; naturally handles the sparse multi-hot diagnosis space reasonably well and is less prone to the aggressive overfitting a single deep tree would show on a modest-N, high-imbalance dataset.
- **XGBoost**: typically the strongest raw discriminator on structured/tabular clinical feature sets of this kind, handles missing values (relevant since network features may be unavailable for some diseases/cohorts) and non-linear interactions natively, and its `scale_pos_weight` and early-stopping machinery map directly onto the class-imbalance and overfitting controls needed here (Sections 8–9).
- Together: LR gives a stable, interpretable linear anchor; RF and XGBoost each model non-linearities with different bias/variance trade-offs (bagging vs. boosting), which is exactly the kind of *diverse-error* base-learner set that makes stacking worth doing rather than just picking the single best base model.

### 3.2 Meta-learner

- **Logistic Regression**, confirmed as the right choice: it takes a small number of well-behaved (0,1)-bounded probability inputs (the base learners' outputs) and learns how much to trust each — a linear-combination problem LR is well suited to, without the risk of a more complex meta-learner (e.g., a second-level GBM) overfitting to the base models' quirks on a modest-sized meta-training set.
- **Meta-learner input**: base-learner **calibrated-scale probabilities** (`predict_proba`), not raw logits or margins — probabilities are already on a comparable [0,1] scale across three structurally different models, which logits/margins are not (XGBoost margins and RF vote fractions aren't on the same scale without extra normalization). Recommendation, to be validated empirically: additionally include a **small, curated passthrough set** of the strongest raw features (e.g., comorbidity count, top 1–2 network-relationship scores) alongside the three base probabilities as meta-features — a standard "restacking" variant that often modestly improves over probability-only stacking, tested against probability-only stacking as an ablation rather than assumed.
- **Output**: the meta-learner produces the model's raw probability for that disease; this raw probability then goes through calibration (Section 14) before being shown to a user as "risk."

### 3.3 Multi-label handling at the ensemble level

- As established in Section 1.7: **one full 4-model stack (XGBoost, RF, LR, meta-LR) per target disease**, all K stacks sharing the same upstream feature matrix and the same cross-validation fold assignment (critical for the stacking procedure in Section 5 to stay leakage-free and reproducible across labels).
- **Ranking/thresholding**: two output modes are supported and both are useful for different parts of the product:
  - **Ranked list mode** (primary, for the Streamlit "top predicted comorbidities" view): sort the K calibrated probabilities for a given patient and show the top-N, using Precision@K / MAP@K as the governing metrics (Section 10) — no hard threshold needed.
  - **Flagged/binary mode** (secondary, for a "should this specific disease be flagged as elevated risk" toggle): a **per-disease decision threshold**, chosen on the validation split to hit a clinically reasonable operating point (e.g., maximize F1, or fix recall at a chosen floor) — not a single global 0.5 threshold, since base rates differ by an order of magnitude across the K diseases.

---

## 4. Stacking procedure — correct out-of-fold construction

This is treated as a hard correctness requirement, not a tuning nicety. Naively fitting base learners on the full training set and then training the meta-learner on those same in-sample predictions lets the meta-learner see base-model predictions that are contaminated by having already memorized the labels it's trying to predict — the meta-learner would learn to over-trust whichever base model overfits hardest, and reported performance would not replicate at inference.

**Per target disease, per outer split (train/val/test already fixed at the patient level, Section 6):**

1. Take the **training set** for this disease (patient-landmark rows with a known 0/1 label after Section 1.5 masking).
2. Partition the training set into **`M` folds at the patient level** (e.g., `M = 5`) — if a patient contributes multiple landmark rows, all of that patient's rows go into the same fold, so no patient's information leaks across the OOF split.
3. For each fold `m` (1..M):
   - Train each base learner (XGBoost, RF, LR) on the other `M − 1` folds.
   - Predict probabilities for the **held-out fold `m`** with each base learner. These are genuinely out-of-fold predictions — the model producing them never saw fold `m`'s labels.
4. Concatenating the per-fold OOF predictions across all `M` folds reconstructs one OOF probability per base learner for **every** training row, with no row scored by a model that was trained on it.
5. These OOF probability columns (plus the optional passthrough features, Section 3.2) become the **meta-training set**; fit the meta-learner (LR) on this.
6. **Refit each base learner on the full training set** (all `M` folds combined) — this is the version of each base learner that will actually be shipped/used at inference, since it's the one trained on the most data. The OOF-trained fold models from step 3 are discarded after step 4; they exist only to generate leakage-free meta-features, never to be used for real predictions.
7. At **validation-set and test-set time**, generate base-learner predictions using the step-6 full-training-set models (never the fold models), then feed those into the already-fit meta-learner from step 5. Validation and test data are never touched during steps 1–5.

**Hyperparameter tuning discipline:** all hyperparameter search (Section 8) happens using **only** the training-set cross-validation described above (i.e., nested inside step 3's fold structure, or on a further inner split of the training folds) — the validation set is reserved purely for calibration fitting, decision-threshold selection, and early-stopping rounds, and the test set is touched exactly once, at the very end, per disease, per architecture variant (base vs. ensemble vs. ablation arm) being compared.

**Final-model retraining after model selection:** once hyperparameters are chosen via the validation set, the *reported* final model for each disease is refit using train+validation combined (with the same OOF procedure applied over that combined set) before the single final test-set evaluation — so the test set sees the best-available model, but still never influenced which model that was.

---

## 5. Leakage prevention — consolidated checklist

| Leakage type | Control |
|---|---|
| **Future diagnoses / subsequent-admission info** | Feature computation strictly filters `condition_start_date ≤ landmark_date`; label computation strictly filters to `(landmark_date, landmark_date + H]` (Sections 1.3, 2.3) |
| **Post-index medications** | `drug_exposure` features (if used) filtered to `drug_exposure_start_date ≤ landmark_date` |
| **Future measurements** | Never used as features at all in the primary design (Section 2.3); if added later as a stretch feature, same pre-landmark filter applies |
| **Patient overlap across splits** | Splitting is patient-level, not row-level (Section 6); a given `person_id` appears in exactly one of train/val/test, across all of its landmark rows |
| **Repeated visits inflating labels** | Labels are binarized per disease per landmark, not counted (Section 1.6) |
| **Preprocessing leakage** | Scalers/encoders (Section 15) are fit on the training set only, then applied (not refit) to validation/test |
| **Feature-selection leakage** | Any filter-based feature selection (e.g., variance thresholding, correlation pruning) is fit on training folds only, inside the same CV loop as hyperparameter tuning — never on the full dataset before splitting |
| **Target leakage via proxy features** | Explicit exclusion list (Section 2.3); additionally, a **leakage audit step** in Phase 4 checks the top-importance features of a quick baseline model for suspiciously perfect predictors (a classic tell that something post-landmark slipped through) |
| **Network-feature leakage** | Network module must be fit on a training-period/patient-disjoint slice matching the ML split (Section 2.4); the ML side asserts this as a hard precondition on the interface, and adds a scheduled integration test once the real module exists |
| **Stacking leakage** | Full OOF procedure, Section 4 |
| **Death/censoring leakage** | Patients who die within the outcome window before it closes are handled as a **censored observation** (label = missing beyond time of death for diseases that couldn't have been newly diagnosed post-mortem), not silently coded as negative |

---

## 6. Train / validation / test strategy

- **Unit of splitting: patient (`person_id`)**, not row/visit/condition — every landmark row for a given patient goes to the same split, per Section 4's fold rule extended to the outer split too. Splitting individual visit rows randomly would let a model implicitly learn "I've seen this exact patient's other visits" and dramatically overstate generalization.
- **Recommended split composition**: a **hybrid patient-level + temporal** strategy —
  1. First, order patients by their earliest landmark date.
  2. Reserve the **most recent slice of calendar time** (e.g., the last ~15–20% of the dataset's date range) as a **temporal holdout** for the final test set, using only patients whose landmarks fall entirely in that window — this tests generalization to "the future" relative to training, which is the realistic deployment condition (the model will always be asked about a patient's *current* snapshot, later than its training data).
  3. Within the remaining, earlier-dated patients, do a **random patient-level split** into train (~70% of remaining patients) and validation (~30% of remaining patients) for hyperparameter tuning and calibration.
- **Multiple snapshots per patient**: since one patient can contribute several landmark rows (Section 1.2), and a temporal boundary is being used, a patient whose landmarks span across the temporal cutoff is assigned **entirely** to whichever side contains the *majority* of their observation history to avoid a patient effectively appearing (in slightly different snapshots) on both sides of the boundary; the minority-side rows for that patient are dropped rather than reassigned individually.
- **Reporting**: results are reported both on the random validation split (used for tuning) and the held-out temporal test split (used for final numbers), and the gap between them is treated as a first-class diagnostic (Section 8) — a large drop on the temporal split indicates the model is leaning on patterns that don't hold up prospectively, which is exactly the failure mode a purely random split would hide.

---

## 7. Overfitting / underfitting controls, mapped to pipeline stage

| Stage | Overfitting control | Underfitting control |
|---|---|---|
| Feature selection | Drop near-constant / near-duplicate features (fit on train folds only) | Ensure the background comorbidity set (Section 2.2) is wide enough that LR isn't starved of signal |
| Logistic Regression | L2 (default) or L1 (for sparsity/interpretability trade-off, tested as an ablation) penalty, tuned `C` via inner CV | Check that heavily regularized LR isn't collapsing to the population base rate — compare against a null/majority-class baseline (Section 11) |
| Random Forest | `max_depth`, `min_samples_leaf`, `max_features` tuned via inner CV; out-of-bag error tracked as a free extra diagnostic | If OOB error and validation error are both high, increase `n_estimators` / depth before assuming the ceiling has been reached |
| XGBoost | `max_depth`, `min_child_weight`, `subsample`, `colsample_bytree`, `reg_lambda`/`reg_alpha` tuned via inner CV; **early stopping** on a held-out inner-validation fold using the primary metric (AUPRC, Section 10) as the early-stopping criterion | Confirm training-set AUPRC isn't suspiciously close to the validation AUPRC in a way that suggests the model stopped too early or is under-parameterized for the feature space |
| Meta-learner | Kept deliberately simple (LR, few inputs) — this is itself an overfitting control, since a complex meta-learner on a small meta-training set is a well-known stacking failure mode | If the meta-learner ends up assigning near-zero weight to two of the three base learners, that's a signal worth investigating (possibly those base learners are miscalibrated, not necessarily useless) rather than automatically pruning them |
| Hyperparameter tuning | Nested inside the Section 4 CV loop; tuning search itself uses a **separate inner split** from the OOF-generation folds where feasible, to avoid the search itself creeping into meta-feature quality | Wide-enough search space (don't over-constrain grids to values near defaults without checking) |
| Cross-cutting diagnostics | **Learning curves** (train vs. validation AUPRC as a function of training-set size) run per disease-tier (high/medium/low prevalence) to check whether more data would help; **train-vs-validation-vs-test metric table** reported for every model in every experiment, not just the final headline number | Same learning curves catch underfitting (flat, low curves) as well as overfitting (diverging curves) |
| Temporal generalization | Section 6's temporal test split is itself the main overfitting check against "the model learned this specific data era" | — |

---

## 8. Class imbalance strategy

- **Expectation going in**: most of the K target diseases will have training-set positive rates well under 5–10%, and some considerably rarer — standard for incident-diagnosis prediction.
- **Chosen approach, and why the alternatives are rejected for this task:**
  - **Class weighting** (`class_weight='balanced'` for LR/RF, `scale_pos_weight` for XGBoost) is the primary imbalance control — it changes the loss landscape without fabricating data, keeps calibration more tractable than oversampling does, and is trivial to apply consistently across the three heterogeneous base learners.
  - **SMOTE / synthetic oversampling is explicitly rejected as the default**, not just left out by omission: the feature space here is a mix of binary multi-hot diagnosis indicators, small-integer counts, and continuous network scores — SMOTE's linear interpolation between neighbors produces synthetic patients with fractional/nonsensical diagnosis indicators (e.g., "0.4 diabetic") and can manufacture unrealistic combinations, which is a worse failure mode for a clinically-facing tool than simply living with imbalance via weighting. If a specific disease's performance under class weighting alone is judged inadequate, a **targeted, disease-specific undersampling of the majority (negative) class** (not synthetic oversampling of the minority) is the first thing to try instead, since it doesn't fabricate patient data.
  - **Minimum-prevalence threshold**: target diseases with fewer than a set minimum number of positive training landmarks (e.g., ~50–100, to be finalized once real prevalence is measured in Phase 1) are **excluded from the modeled label space** rather than forced through the pipeline with too few examples to support a stable stacked ensemble — reported explicitly as a limitation, not silently dropped.
  - **Per-class thresholds** (Section 3.3) rather than one global threshold, since a single 0.5 cutoff applied uniformly across diseases with wildly different base rates would make rare-but-important diseases essentially never fire.
  - **Ranking-first evaluation** (Section 9): because the product surface is a ranked list, not independent yes/no calls, the primary metrics are chosen to be robust to imbalance by construction (AUPRC, Precision@K) rather than leaning on accuracy or a single threshold at all.

---

## 9. Evaluation metrics

- **Primary metric: AUPRC (per disease), averaged into a macro-AUPRC across the K modeled diseases.** AUPRC is preferred over AUROC as the headline number precisely because of the imbalance discussed above — AUROC can look deceptively strong on rare-positive problems by being dominated by the (easy) true-negative majority, while AUPRC directly reflects precision at realistic operating points.
- **Primary product-facing metric: Precision@K and Recall@K** (K = top-3/5/10 predicted diseases per patient) plus **MAP@K**, since the Streamlit tool's actual behavior is "show the top-N most likely new diagnoses for this patient" — these ranking metrics evaluate exactly that behavior, across all K modeled diseases simultaneously per patient, rather than one disease in isolation.
- **Secondary metrics**:
  - **AUROC** — retained as a standard, widely-understood reference number for comparison against literature and the baselines in Section 10, even though it isn't the primary decision metric here.
  - **Per-disease F1 at the tuned operating threshold** (Section 3.3) — useful for the "flagged/binary" product mode.
  - **Brier score** and **calibration curves (reliability diagrams)** — directly needed for the calibration work in Section 14, since a wrong-but-confident probability is a distinct failure mode from a merely low-ranking one.
- **NDCG@K** is noted as a reasonable secondary ranking metric if graded relevance (e.g., weighting more severe/actionable diseases higher) is ever introduced, but is not part of the primary metric set now since all diseases are currently treated as equally relevant.
- **Reporting discipline**: every metric is reported per disease **and** macro-averaged across diseases, plus split out by the high/medium/low prevalence tiers used elsewhere in this plan (Section 8) — a single macro-average can hide the fact that performance is being carried entirely by the two or three most common diseases.

---

## 10. Baselines

For the ML component specifically, in increasing order of complexity, all evaluated on the identical patient-level splits, feature pipeline, and metric set so comparisons are apples-to-apples:

1. **Prevalence/majority baseline**: rank candidate diseases purely by their population base rate in the training set, ignoring the patient's own features entirely. This is the floor — any modeled approach that doesn't clearly beat it is not adding value.
2. **Logistic Regression alone** (no stacking).
3. **Random Forest alone**.
4. **XGBoost alone**.
5. **Stacked ensemble** (the full Section 3–4 pipeline).

The explicit research question this baseline ladder answers for the ML component: **does stacking actually improve over the best single base model**, not just over the weakest one — so the comparison between (5) and the *best* of (2)/(3)/(4) per disease (not just their average) is reported as its own explicit result, not buried in an aggregate table. If stacking does not clearly beat the best single base learner once this is measured honestly, that is reported as a finding, not hidden.

*(Out of scope for this document, but the pipeline is built so these slot in later without rework: RR/network-only scoring baseline, and a deep-learning baseline such as an MLP or the CURENet-style architecture referenced in the literature review, both evaluated against the exact same splits and metrics defined above.)*

---

## 11. Ablation study design

**Governing research question** (as specified): *does adding network-derived information improve future-comorbidity prediction beyond conventional patient features?* The graph module itself is out of scope, but the ablation harness is built now, against the Section 2.4 stub interface, so that swapping in real network features later is a one-line config change, not a re-implementation.

Feature-group configurations, each run through the **identical** stacked-ensemble pipeline (same splits, same tuning budget, same metrics):

| Ablation arm | Feature groups included |
|---|---|
| A — Demographics only | Age, sex (+ race/ethnicity if retained, Section 2.1) |
| B — Diagnoses only | Multi-hot current-diagnosis vector, no demographics |
| C — Demographics + diagnoses | A + B (this is the realistic "conventional ML" baseline a network-free version of this tool would ship) |
| D — C + derived features | C + comorbidity count, interaction indicators (Section 2.2) |
| E — Network features only | Network-interface output only (Section 2.4), demographics/diagnoses excluded — isolates how much signal the network relationships carry on their own, mirroring the eventual RR-only baseline in spirit |
| F — All features | D + network features — the full intended system |

The **D vs. F** comparison is the headline ablation result once the real network module exists; **A/B/C/E** individually contextualize *why* (e.g., if E alone already rivals D, that says something different about the network's contribution than if E is weak but F still beats D). Every arm is run for every modeled target disease, not just averaged, since network-feature value plausibly varies a lot by disease (a disease with few well-established comorbid relationships in the literature should show smaller lift than one like CKD with strong, well-documented RR links to diabetes/hypertension).

---

## 12. Explainability design

Per the deck's explicit example ("CKD predicted because of relative risk with existing diabetes and hypertension, alongside model-level feature importance"), the explanation output must **name two distinct sources of evidence**, not blend them into one opaque score:

1. **Network-relationship evidence**: surfaced directly from the network-interface fields (Section 2.4) — specifically `strongest_source_disease`, `max_relative_risk`, and `n_significant_edges` are earmarked as *explanation-only* passthrough fields even where they aren't the most useful *modeling* features, precisely so the natural-language layer can say "linked to your existing diagnoses of X and Y" without having to reverse-engineer that from a SHAP value.
2. **Model-level feature evidence**: standard per-model attribution —
   - **Logistic Regression**: standardized coefficients, straightforward and exact.
   - **Random Forest / XGBoost**: **SHAP (TreeExplainer)** values per prediction, preferred over plain impurity-based `feature_importances_` because SHAP gives *per-patient, per-prediction* attribution (which is what an explanation needs — "why did *this* patient get *this* score," not "which features matter on average").
   - **Stacked ensemble**: the meta-learner's coefficients directly show how much weight each base learner's opinion received for this disease; combined with each base learner's own SHAP breakdown, this supports a two-level explanation ("the score leaned heavily on the XGBoost model's opinion, which was driven mainly by your diagnosis of diabetes and a strong network link to CKD").
- **Assembling the natural-language explanation**: a lightweight template-based generator (not a free-text LLM call, to keep it deterministic, auditable, and cheap enough to run per-prediction in a Streamlit app) fills a sentence template from the top-ranked SHAP contributors plus the top network-relationship fields, e.g.: *"`{disease}` is flagged as elevated risk primarily due to existing `{top_diagnosis_1}` and `{top_diagnosis_2}`, which show a strong historical association with `{disease}` in the comorbidity network, along with `{top_model_feature}`."*
- **No causal language**: the template vocabulary is restricted to association/risk-factor phrasing ("associated with," "linked to," "elevated risk given") and explicitly avoids "causes," "leads to," "will develop" — enforced as a fixed, reviewed template rather than free text, so this constraint can't be silently violated by a later change.

---

## 13. Calibration

- **Why calibration matters here specifically**: raw base-learner or meta-learner probabilities from tree ensembles (and to a lesser extent LR under class weighting) are known to be poorly calibrated — a "70% predicted risk" from an uncalibrated model does not mean 70% of such patients actually develop the disease. Since the product intends to *display a risk-like number* to a user, this gap is not cosmetic.
- **Procedure**: fit a calibrator (Platt/sigmoid scaling as the default, isotonic regression as an alternative if enough validation-set positives exist per disease to support the more flexible non-parametric fit) **per target disease**, on the **validation split only**, using the meta-learner's raw output as input — never on training data (the meta-learner has already fit that) and never on test data (reserved for final unbiased evaluation).
- **Reported separately, deliberately not conflated**:
  - **Model probability**: the meta-learner's raw output — useful internally for debugging and for AUPRC/AUROC computation (rank-based metrics are calibration-invariant, so raw probabilities are fine for those).
  - **Calibrated risk**: the post-calibration probability — this is what gets displayed to the Streamlit user as "risk," accompanied by a Brier score / reliability-diagram check that the calibration actually held on the test split (calibration fit on validation can still drift on test, especially given the temporal split in Section 6 — this is checked, not assumed).
  - **Ranking score**: for the "top-N" list view, the **raw** (or calibrated, they'll produce the same order — calibration is monotonic) probability is used purely for *sorting*; the point of keeping this conceptually distinct from "calibrated risk" is that ranking correctness (did we surface the right diseases) and calibration correctness (is the displayed percentage trustworthy) are evaluated and can fail independently, and the plan treats them as two different acceptance criteria rather than one.

---

## 14. Website (Streamlit) inference-pipeline compatibility

**End-to-end inference flow**, matching the training-time pipeline field-for-field:

```
User form input (age, sex, current diagnoses[, meds])
        │
        ▼
Input validation + encoding
  (map free-text/checkbox diagnosis selections → same disease-group
   vocabulary used in training; reject/flag unrecognized entries)
        │
        ▼
Derived-feature construction
  (multi-hot vector, comorbidity count, interaction indicators, age bucket —
   using the exact encoder/vocabulary objects saved from training, Section 15)
        │
        ▼
Network-feature interface call
  (per candidate target disease T: get_network_features(current_diagnoses, T);
   stub-safe — falls back to the documented placeholder if the network
   module/service is unavailable, rather than failing the whole request)
        │
        ▼
Per-disease base-model inference (XGBoost, RF, LR)  ×  K diseases
        │
        ▼
Per-disease meta-learner inference (LR)
        │
        ▼
Per-disease calibration
        │
        ▼
Assemble ranked list (top-N) + apply "already has this disease" mask (Section 1.5)
        │
        ▼
Explanation generation (Section 13) for each surfaced disease
        │
        ▼
Streamlit display: ranked, calibrated risk list + explanations
  (+ optional supporting network visualization, owned by the graph module)
```

- **Hard invariant**: training-time and inference-time preprocessing code must be **the same code path**, not reimplemented twice (once for batch training, once for the live app) — the preprocessing/feature-construction module is written once, imported by both the training pipeline and the Streamlit app, so encoder/vocabulary drift between "how the model was trained" and "how the app builds features" is structurally impossible rather than something to remember to keep in sync.
- **Artifact persistence** — everything needed to reproduce a prediction exactly is versioned together in a single model-registry directory per trained release:
  - Base-learner weights: XGBoost's native booster format; RF and LR via `joblib`.
  - Meta-learner weights: `joblib`.
  - Per-disease calibrators: `joblib`.
  - Feature manifest (`feature_manifest.json`): ordered feature-name list, dtype per feature, diagnosis-vocabulary mapping (concept-group → index), scaler parameters (means/scales for any standardized continuous features), the K target-disease list, and the minimum-prevalence cutoffs actually applied.
  - Per-disease decision thresholds (for the flagged/binary mode, Section 3.3).
  - A top-level `manifest.json` recording: training-data version/hash, horizon `H` used, split boundary dates, code/git commit hash, and library versions — so a given Streamlit deployment can be tied back to an exact, reproducible training run.

---

## 15. Synthea 23M scalability plan

- **Query layer**: use **DuckDB** directly over the OMOP Parquet/CSV tables for all heavy joins, filters, and aggregations (landmark selection, pre-landmark history extraction, outcome-window label computation) rather than pulling raw tables into pandas — DuckDB's columnar, out-of-core execution comfortably handles a 23M-scale OMOP export on a single machine, and SQL is a natural fit for the interval-based logic in Sections 1.2–1.3 (`condition_start_date BETWEEN ...`, `visit_occurrence` joins).
- **Materialization strategy**: the **raw OMOP tables are large; the resulting patient-landmark feature matrix is not** — after landmark selection and feature aggregation, the working dataset shrinks to (number of patients × average landmarks per patient) rows by (a few hundred feature columns), which is expected to fit comfortably in memory as a **Parquet-cached intermediate dataset**. Heavy computation happens once in DuckDB/SQL; everything downstream (splitting, CV, model training, SHAP) operates on this compact cached matrix, not the raw tables.
- **Sparse representation**: the multi-hot diagnosis/background-comorbidity vectors are stored and fed to LR/RF/XGBoost as **`scipy.sparse`** matrices where the library supports it (all three do), since the vast majority of a given patient's multi-hot vector is zero.
- **Dev vs. final dataset, explicitly separated**:
  - **Development/testing dataset**: a fixed, reproducible **person-level random sample** (e.g., 1–5% of patients, sampled by hashing `person_id` so the same patients are always included — never a fresh random sample each run, which would make dev-cycle results incomparable across iterations) used for all pipeline-correctness work, debugging the OOF-stacking logic, and fast iteration on feature engineering.
  - **Final training/evaluation dataset**: the full cohort passing the Section 1.2 eligibility filters, run through the exact same (already-debugged) pipeline for the reported results.
  - The dev sample is drawn **before** any splitting logic (Section 6) so it exercises the same patient-level/temporal splitting code the final run uses, rather than a simplified stand-in that could hide split-logic bugs.
- **GPU note**: XGBoost's `gpu_hist`/CUDA-accelerated training is a viable, optional speed-up on the K-times-model-count training workload described in Section 3.3 if local GPU hardware is available; it is a runtime optimization, not a modeling-decision dependency, so the plan works identically (just slower) on CPU-only training.

---

## 16. Project structure

```text
comorbidity-ml/
├── src/
│   ├── data/                 # DuckDB queries against raw OMOP tables; dev-sample extraction
│   ├── preprocessing/        # Shared encoders/vocab builders — imported by BOTH training and inference
│   ├── labels/                # Landmark selection, outcome-window label construction, disease grouping
│   ├── features/
│   │   ├── demographic.py
│   │   ├── diagnosis.py
│   │   ├── derived.py
│   │   └── network_interface.py   # Stub now; single integration point for the future graph module
│   ├── models/
│   │   ├── base_learners.py       # XGBoost / RF / LR training + inference wrappers
│   │   └── meta_learner.py
│   ├── stacking/               # OOF fold logic (Section 4) — the one place stacking correctness lives
│   ├── calibration/
│   ├── explainability/         # SHAP wrappers + explanation-template assembly
│   ├── evaluation/             # Metrics (Section 9), baseline runners (Section 10), ablation harness (Section 11)
│   └── inference/               # The single pipeline module also imported by the Streamlit app (Section 15)
├── configs/                    # Per-experiment YAML: horizon H, K, split dates, hyperparameter grids
├── models/                     # Versioned model-registry output (Section 15's artifact bundle)
├── experiments/                 # Ablation/baseline run outputs, one directory per experiment id
├── reports/                     # Generated metric tables, learning curves, calibration plots
├── tests/                       # Leakage-audit tests, OOF-correctness unit tests, encoder round-trip tests
└── streamlit_app/                # Thin UI layer; imports src/inference, no duplicated preprocessing logic
```

---

## 17. Implementation phases

**Phase 1 — Dataset & schema inspection**
- *Objective*: understand the actual Synthea OMOP 23M schema and cohort characteristics before any modeling assumption is finalized.
- *Tasks*: inventory table row counts and column completeness for `person`, `condition_occurrence`, `visit_occurrence`, `observation_period`, `drug_exposure`; measure real disease prevalence to finalize K (Section 1.4) and the minimum-prevalence cutoff (Section 8); check typical visit cadence per patient to validate the horizon `H` choice (Section 1.3).
- *Outputs*: a data-profiling report; a finalized K-disease list with prevalence numbers.
- *Validation checks*: no assumed column is actually missing/renamed in this Synthea export; prevalence numbers are sane against known Synthea disease-module rates.
- *Completion criteria*: K and H are locked in with documented justification from real numbers, not just the defaults proposed in this plan.

**Phase 2 — Patient timeline construction**
- *Objective*: build the per-patient chronological event timeline needed for landmark selection.
- *Tasks*: DuckDB views joining `person` + `visit_occurrence` + `condition_occurrence` ordered by date; compute `observation_period` coverage per patient.
- *Outputs*: a queryable, cached "patient timeline" table.
- *Validation checks*: spot-check a handful of patients' timelines manually against raw tables.
- *Completion criteria*: timeline table reproducible from raw tables via a single script/query set.

**Phase 3 — Landmark & label generation**
- *Objective*: implement Sections 1.2–1.6.
- *Tasks*: eligibility filtering; landmark extraction; outcome-window label computation per target disease; already-has-disease masking; censoring handling.
- *Outputs*: the labeled patient-landmark table (one row per landmark, one column per target disease label).
- *Validation checks*: label prevalence matches Phase 1 expectations; spot-check that no label depends on post-landmark data (manual trace on sample rows).
- *Completion criteria*: label table passes an automated leakage-audit test that fails the build if any label column correlates suspiciously with a known-future field.

**Phase 4 — Feature engineering**
- *Objective*: implement Section 2 (excluding the network module itself).
- *Tasks*: demographic/diagnosis/derived feature builders; network-interface stub; feature manifest generation.
- *Outputs*: the full pre-network feature matrix, cached as Parquet.
- *Validation checks*: run the Section 2.3 exclusion list as an automated check (fail the build if any excluded column name appears in the feature matrix); confirm feature matrix row count matches label table row count exactly.
- *Completion criteria*: feature matrix + manifest reproducible end-to-end from raw tables via the pipeline scripts, no manual steps.

**Phase 5 — Train/validation/test splitting**
- *Objective*: implement Section 6.
- *Tasks*: temporal boundary selection; patient-level assignment; multi-landmark patient handling.
- *Outputs*: a split-assignment table (`person_id → {train, val, test}`).
- *Validation checks*: assert zero patient overlap across splits; report class balance per split per disease (flag if wildly different, which would suggest a split artifact).
- *Completion criteria*: split assignment is deterministic and versioned (same split every re-run given the same config).

**Phase 6 — Baseline models**
- *Objective*: implement Section 10's simple/majority baseline and confirm the evaluation harness works before investing in the full ensemble.
- *Tasks*: prevalence-baseline scorer; metric computation harness (Section 9).
- *Outputs*: baseline metric report.
- *Validation checks*: baseline numbers are sane (e.g., AUPRC ≈ prevalence for the majority baseline, as expected).
- *Completion criteria*: the metrics/evaluation code is trusted enough to be reused unchanged for every later model.

**Phase 7 — Logistic Regression base model**
- *Objective*: standalone LR per disease.
- *Tasks*: pipeline wiring (encoders → LR), class weighting, hyperparameter search for `C`/penalty.
- *Outputs*: per-disease LR models + metrics.
- *Validation checks*: coefficients reviewed for clinical plausibility (e.g., diabetes should positively predict CKD) as a sanity check, not just a metric number.
- *Completion criteria*: LR results beat the Phase 6 baseline on macro-AUPRC.

**Phase 8 — Random Forest base model**
- *Objective*: standalone RF per disease.
- *Tasks*: hyperparameter search; OOB diagnostics.
- *Outputs*: per-disease RF models + metrics.
- *Validation checks*: train-vs-OOB-vs-validation gap reviewed per Section 8.
- *Completion criteria*: RF results recorded alongside LR for the Section 11 baseline table.

**Phase 9 — XGBoost base model**
- *Objective*: standalone XGBoost per disease.
- *Tasks*: hyperparameter search; early stopping wired to an inner validation fold; `scale_pos_weight` tuning.
- *Outputs*: per-disease XGBoost models + metrics.
- *Validation checks*: learning curves confirm early stopping is triggering sensibly (not at round 1, not never).
- *Completion criteria*: XGBoost results recorded for the baseline table.

**Phase 10 — Proper stacked ensemble**
- *Objective*: implement Section 4's OOF stacking exactly.
- *Tasks*: fold-level OOF generation for all three base learners; meta-feature assembly; meta-learner training; full-data base-learner refit.
- *Outputs*: per-disease 4-model stack.
- *Validation checks*: a dedicated **unit test** that deliberately checks no base-learner OOF prediction was generated by a model trained on that same row (assert via row-id bookkeeping, not just visual inspection).
- *Completion criteria*: stacked ensemble metrics computed and compared against Phase 7–9 per Section 10's "beats the best single base model" test.

**Phase 11 — Hyperparameter tuning finalization**
- *Objective*: consolidate and finalize tuning across all four model types, respecting the nested-CV discipline (Section 4/8).
- *Tasks*: final grid/search-space selection; document chosen hyperparameters per disease.
- *Outputs*: finalized hyperparameter config files.
- *Validation checks*: confirm no tuning step ever touched the test split.
- *Completion criteria*: config is frozen and version-controlled before touching the test set for the first time.

**Phase 12 — Calibration**
- *Objective*: implement Section 14.
- *Tasks*: per-disease calibrator fitting on validation; Brier score and reliability-diagram generation.
- *Outputs*: per-disease calibrator artifacts + calibration report.
- *Validation checks*: calibration curve checked on the held-out test split, not just validation, to catch drift.
- *Completion criteria*: calibrated Brier score improves over uncalibrated for the majority of modeled diseases (documented exceptions are fine, silent regressions are not).

**Phase 13 — Explainability**
- *Objective*: implement Section 13.
- *Tasks*: SHAP wrappers for RF/XGBoost; LR coefficient extraction; meta-learner weight extraction; explanation-template assembly.
- *Outputs*: an `explain(patient, disease) → structured explanation` function.
- *Validation checks*: manual review of a sample of generated explanations for the "no causal language" constraint and for basic clinical plausibility.
- *Completion criteria*: explanation output matches the deck's target style (names existing diagnoses + network relationship + model evidence) on a demo patient.

**Phase 14 — Evaluation**
- *Objective*: full metric suite (Section 9) run across all models and splits.
- *Tasks*: per-disease and macro-averaged metric tables; prevalence-tier breakdowns; train/val/test gap reporting.
- *Outputs*: the primary results report.
- *Validation checks*: numbers cross-checked against Phase 6–10's incremental results for consistency.
- *Completion criteria*: a single reproducible script regenerates every reported number from the cached feature matrix.

**Phase 15 — Ablation experiments**
- *Objective*: implement Section 11's six-arm ablation.
- *Tasks*: run each feature-group configuration through the identical pipeline; compare.
- *Outputs*: ablation results table, per disease and macro.
- *Validation checks*: confirm each arm's feature set exactly matches its definition (automated column-set assertion, not manual).
- *Completion criteria*: a clear, honestly-reported answer to "does the (stubbed, then later real) network signal add value beyond conventional features."

**Phase 16 — Model packaging**
- *Objective*: implement Section 15's artifact bundle.
- *Tasks*: serialize all models/calibrators/manifests into a versioned registry directory.
- *Outputs*: a self-contained, loadable model release.
- *Validation checks*: load the packaged bundle in a **fresh process** and reproduce Phase 14's test-set metrics exactly, catching any artifact/version mismatch.
- *Completion criteria*: a documented, one-command "load release X and score patient Y" path works.

**Phase 17 — Inference pipeline**
- *Objective*: implement Section 15's shared inference module.
- *Tasks*: input validation/encoding; feature construction reusing Phase 4's exact code; stub-safe network-interface call; ranked-list assembly + already-has masking; explanation call.
- *Outputs*: `src/inference/predict(patient_input) → ranked, explained predictions`.
- *Validation checks*: unit tests feeding hand-constructed patient inputs and checking output shape/ranges/masking behavior.
- *Completion criteria*: identical outputs whether called from a test script or from the Streamlit app (proves the "one code path" invariant).

**Phase 18 — Streamlit integration**
- *Objective*: wire the inference pipeline into the actual form-based UI.
- *Tasks*: form design matching exactly the "user-input features" list from Section 2.1; call `src/inference/predict`; render ranked list + explanations.
- *Outputs*: working Streamlit page (ML side only — network visualization is the other module's responsibility).
- *Validation checks*: manual click-through with several representative synthetic patient profiles.
- *Completion criteria*: a user can submit a plausible patient profile and get a sensible, explained, ranked output with no backend errors.

**Phase 19 — Testing**
- *Objective*: consolidate the validation checks scattered through Phases 1–18 into a real, runnable test suite.
- *Tasks*: leakage-audit tests (Section 5 checklist, each as an assertion where feasible); OOF-correctness test (Phase 10); encoder round-trip tests (train-time vs. inference-time feature construction produce identical vectors for the same patient); split-integrity tests (no patient overlap).
- *Outputs*: `tests/` suite, runnable in CI or locally.
- *Validation checks*: the suite itself is reviewed for coverage against the Section 5 leakage checklist, item by item.
- *Completion criteria*: all tests pass on a clean checkout; the leakage checklist has at least one corresponding automated test per row.

**Phase 20 — Final experiment & reproducibility pass**
- *Objective*: lock a single, fully reproducible end-to-end run for the report/write-up.
- *Tasks*: freeze configs, random seeds, data version; regenerate every table/figure from scratch on the full (non-dev-sample) dataset; write up honest limitations (Synthea-specific caveats, stubbed network features, dropped low-prevalence diseases, temporal-split performance gaps if any).
- *Outputs*: final results report + a documented, one-command reproduction path.
- *Validation checks*: a clean re-run from raw OMOP tables reproduces the reported headline numbers within expected floating-point/nondeterminism tolerance.
- *Completion criteria*: everything in Sections 9–11 of this plan has a corresponding number in the final report, and every number can be traced back to the pipeline code that produced it.

---

## 18. Recommended final architecture

```
                         ┌───────────────────────────────┐
                         │   Synthea OMOP 23M (DuckDB)    │
                         └───────────────┬────────────────┘
                                         │
                     Patient timelines, landmarks, outcome-window labels
                                         │
                                         ▼
                ┌──────────────────────────────────────────────┐
                │        Patient-landmark feature matrix         │
                │  demographics · diagnoses · derived features   │
                └───────────────────────┬────────────────────────┘
                                         │            ┌───────────────────────────┐
                                         ├───────────►│  Network module (separate,│
                                         │            │  external, interface only)│
                                         │            └─────────────┬─────────────┘
                                         │                          │
                                         └────────────┬─────────────┘
                                                      ▼
                                     Full feature vector per (patient, target disease)
                                                      │
                     ┌────────────────────────────────┼────────────────────────────────┐
                     ▼                                ▼                                ▼
              XGBoost (per disease)          Random Forest (per disease)      Logistic Regression (per disease)
                     │                                │                                │
                     └────────────────────┬───────────┴────────────────┬───────────────┘
                                          ▼                            ▼
                                Out-of-fold probabilities (train)   Full-data-fit probabilities (val/test/inference)
                                          │
                                          ▼
                             Logistic Regression meta-learner (per disease)
                                          │
                                          ▼
                                Per-disease calibration (Platt/isotonic)
                                          │
                                          ▼
                     Ranked, calibrated risk list across K diseases (per patient)
                                          │
                          ┌───────────────┴───────────────┐
                          ▼                                ▼
             SHAP / coefficient / meta-weight        Network-relationship
                  attribution                          evidence (passthrough)
                          └───────────────┬───────────────┘
                                          ▼
                          Template-based natural-language explanation
                                          │
                                          ▼
                                 Streamlit application
```

**Data/model flow, summarized**: Synthea OMOP tables → patient timelines → landmark selection & outcome-window labels → feature matrix (demographics + diagnoses + derived, joined with network-interface output) → per-disease base learners → per-disease OOF stacking into a meta-learner → per-disease calibration → ranked, masked, explained predictions → Streamlit form-to-output loop, using the exact same feature-construction code at inference as at training.

---

## 19. Final implementation checklist

**Task & data definition**
- [ ] Schema-inspect Synthea OMOP tables; finalize K target diseases and prevalence-based inclusion cutoff
- [ ] Finalize horizon `H` (default 365 days) after checking real visit-cadence statistics
- [ ] Build patient timelines and `observation_period` coverage checks
- [ ] Implement landmark eligibility filtering (history length, min. prior diagnosis count)
- [ ] Implement outcome-window label generation, including already-has-disease masking, repeated-diagnosis binarization, and death/censoring handling
- [ ] Automated leakage-audit test on the label table

**Features**
- [ ] Implement user-input feature encoders (age, sex, current diagnoses[, meds])
- [ ] Implement derived features (multi-hot vector, comorbidity count, interaction indicators, age bucket)
- [ ] Enforce and test the future/unavailable-feature exclusion list
- [ ] Build the `network_interface` stub module with the fixed feature schema (Section 2.4) and a documented placeholder policy
- [ ] Generate and version the feature manifest

**Splitting**
- [ ] Implement patient-level + temporal hybrid split
- [ ] Assert zero patient overlap across train/val/test
- [ ] Handle multi-landmark patients straddling the temporal boundary

**Modeling**
- [ ] Train & tune standalone LR, RF, XGBoost per disease; record baseline metrics
- [ ] Implement fold-level OOF prediction generation (patient-level folds)
- [ ] Implement meta-feature assembly (base probabilities [+ passthrough features])
- [ ] Train per-disease LR meta-learner on OOF meta-features
- [ ] Refit base learners on full training data for deployment
- [ ] Unit test proving no base-learner prediction leaks into its own training fold

**Calibration & explainability**
- [ ] Fit per-disease calibrators on the validation split only
- [ ] Generate Brier scores / reliability diagrams on validation and test
- [ ] Implement SHAP-based attribution for RF/XGBoost
- [ ] Implement LR coefficient and meta-learner weight extraction
- [ ] Implement the causal-language-free explanation template, combining network-relationship and model-level evidence

**Evaluation**
- [ ] Implement AUPRC, AUROC, Precision@K/Recall@K, MAP@K, F1-at-threshold, Brier score
- [ ] Report per-disease and macro-averaged metrics, split by prevalence tier
- [ ] Run and report the majority-baseline through full-stacked-ensemble comparison ladder
- [ ] Explicitly compare stacked ensemble vs. best single base learner (not just average)
- [ ] Run all six ablation arms; report per-disease and macro results

**Packaging & deployment**
- [ ] Serialize models, calibrators, manifest, thresholds into a versioned registry bundle
- [ ] Build the shared inference module used by both training-time evaluation and the Streamlit app
- [ ] Fresh-process load test reproducing exact test-set metrics from the packaged bundle
- [ ] Build the Streamlit form matching the user-input feature list exactly
- [ ] Wire ranked-list display, already-has-disease masking, and explanation rendering

**Quality & reproducibility**
- [ ] Consolidate all leakage/correctness checks into a runnable test suite
- [ ] Freeze configs/seeds/data version for the final reported run
- [ ] Full reproduction run from raw OMOP tables to final report, on the complete (non-dev-sample) cohort
- [ ] Written limitations section (Synthea synthetic-data caveats, stubbed network features, dropped rare diseases, temporal-generalization gap if observed)
