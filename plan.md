# Comorbidity Network Integration — Implementation Plan

**Audience:** an implementing coding agent (Antigravity) with real access to the project repository.
**Status of this document:** written from project context only. It contains no claims about actual repository file contents, exact schemas, or exact paths — every file/path reference below is a **proposal to verify and adapt**, not a fact. The implementing agent must inspect the actual repository before writing code; this plan tells it *what* to build and *why*, not what already exists on disk.

---

## 1. What is being built, and why

The project already has a working, evaluated conventional ML system that predicts which of 41 curated chronic comorbidities a patient will newly develop in the 365 days following a landmark date, using 81 clinical features and a per-disease stacked ensemble (LR + RF + XGBoost → OOF stacking → meta-LR → calibration). That system's results are final and must not change.

The next stage adds the second major research component named in the project title: an **interpretable disease-comorbidity network**, used to derive patient-specific network features, integrated into the existing prediction pipeline as a **new, separate experimental arm/version** — not a replacement of the existing one. The point of this stage is to answer one clean research question: *does network-derived information about disease-disease relationships improve future-comorbidity prediction beyond the existing clinical features?* A negative result (network features add nothing) is an acceptable, reportable outcome — this is a hypothesis test, not a mandate to make the network "win."

---

## 2. How the components interact

```
Longitudinal EHR (existing, unchanged)
        │
        ├──────────────► Existing 81-feature clinical pipeline (UNCHANGED, this is the baseline)
        │
        └──────────────► Disease graph construction (NEW)
                                 │
                                 ▼
                       Frozen disease graph artifact
                                 │
                                 ▼
                  Patient-specific network features (NEW, per landmark)
                                 │
                                 ▼
         Concatenated with existing 81 clinical features (per target disease)
                                 │
                                 ▼
        Per-disease stacked ensemble, same architecture as today, retrained
        on the expanded feature set → new release version (NOT overwriting v1)
                                 │
                                 ▼
        Calibration → masking → ranked predictions → explanations (SAME
        mechanics as today, extended to label which evidence is clinical
        vs. network-derived)
                                 │
                                 ▼
              Streamlit: real Comorbidity Network page replaces the
              current placeholder; Risk Results/Explainability/Disease
              Explorer gain small, additive network-aware elements
```

The graph is built **once**, from a fixed data slice, and frozen (Section 4). Patient-specific network features are then computed **from that frozen graph**, not recomputed per experiment or per inference call in a way that touches raw EHR history again.

---

## 3. Graph design

### 3.1 Nodes

- Primary node set: the **41 curated chronic comorbidity targets** already defined and used as prediction targets in the existing pipeline. Use this as the default node space, per the project's own instruction, unless the implementing agent finds a concrete architectural reason to also include the background/history conditions already used as clinical features — if so, document that decision and why, rather than silently expanding scope.
- Each node stores: a stable disease/condition identifier consistent with whatever identifier the existing target definitions already use (verify against the repo rather than inventing a new ID scheme), the underlying OMOP concept ID(s) where applicable, a human-readable name, and a category field for visualization/filtering (reuse the existing target category grouping — cardiovascular, metabolic/endocrine, renal, etc. — already established for the 41 targets).
- Concept 0 / unmapped conditions are excluded, consistent with how the existing target space already excludes them.

### 3.2 Edges — primary definition

- **Primary edge measure: directed, temporal relative risk**, matching the project's own stated preference and directly supporting the research question "given history of A, what is the association with future B":

  For an ordered pair (A → B), using the **same landmark/horizon definition already used to generate the existing 81-feature training labels** (reuse that logic; do not reimplement it separately):

  - `exposed` = landmarks where disease A is present in the patient's history at/before the landmark.
  - `unexposed` = landmarks where disease A is not present at/before the landmark.
  - `RR(A→B) = P(B newly diagnosed within the 365-day horizon | exposed) / P(B newly diagnosed within the 365-day horizon | unexposed)`

- This is deliberately the same landmark/horizon machinery already built and leakage-audited for the ML labels — reusing it (rather than a separate ad hoc co-occurrence calculation) is both simpler to implement and inherently more consistent with the prediction task the graph is meant to support.
- Only compute this for pairs where B is one of the 41 targets (B must have a valid incident-label definition); A can be any of the 41 targets or, if the node-set decision in 3.1 includes background conditions, any of those too. This keeps the pairwise computation small (on the order of a few thousand candidate pairs, not a dense N×N matrix over the full OMOP vocabulary).
- The graph is used and visualized as **directed**. If a simpler undirected view is wanted for the visualization page only, derive it at render time from the same directed edge data (e.g., take the stronger of RR(A→B)/RR(B→A)) rather than computing and maintaining a second graph artifact.

### 3.3 Edge thresholding / significance

To avoid a dense graph of statistically meaningless edges, apply all of the following together, not any single one alone:

1. **Minimum support**: require a minimum number of exposed landmarks (e.g., on the order of tens to low hundreds — the implementing agent should tune this against the actual cohort sizes in Section 4.1) so RR isn't computed from a handful of patients.
2. **Minimum outcome count**: require a minimum number of positive (A-exposed, B-incident) events, for the same reason.
3. **Statistical test**: a standard 2×2 contingency-table test (Fisher's exact test is preferred over chi-square given some cells will have small counts) on each candidate pair, with a **multiple-testing correction** (Benjamini-Hochberg FDR) applied across all tested pairs, since a few thousand pairwise tests will otherwise produce false positives by chance.
4. **Effect-size floor**: require RR above a minimal threshold (e.g., RR ≥ 1.0, i.e., no protective/neutral pairs) so a "significant but trivial" edge doesn't count.

Store the full contingency-table statistics (RR, p-value, counts) for every tested pair, plus a boolean `is_significant` flag from the combined threshold above — this lets downstream features (like `net_n_significant_edges`) simply filter on the flag rather than re-deriving significance.

### 3.4 Data period used to build the graph (leakage boundary)

This is the most important constraint in the whole plan, so it is stated as a hard rule:

- **The graph is built using training-split landmarks only.** Using the cohort sizes already established for the existing split — Train: 44,661 patients / 174,660 landmarks; Validation: 19,106 patients / 73,862 landmarks; Test: 16,700 patients / 33,304 landmarks (test period ≈ 2016-01-01 to 2019-05-17) — **only the training-split rows** may contribute to the contingency-table counts behind any edge.
- Validation and test patients/landmarks are **never** used to construct the graph, full stop. This guarantees the "Clinical + Network" experimental arm can be evaluated on the existing, unmodified test set without any risk that graph-derived information was informed by test-period outcomes.
- The graph is then **frozen** — built once, saved as a versioned artifact, and reused unchanged for feature generation across train, validation, and test landmarks. No hot recomputation, no per-fold graphs.
- A patient-specific network feature computed for a **training-split** patient still only looks up that patient's own pre-landmark diagnosis set against the frozen graph — the graph's aggregate statistics were built from many patients' data, not that single patient's outcome being predicted, so this does not reintroduce label leakage into that patient's own row. The implementing agent should still write an explicit test for this (Section 8) rather than take it on faith.
- The graph is a **single static graph** for this stage (not a time-windowed/temporal series of graphs). This is a deliberate simplification, documented as a stated limitation, not an oversight.

---

## 4. Patient-specific network features

For a patient at landmark T, let `S` = the set of the patient's diseases present at/before T (reuse the existing pre-landmark diagnosis extraction already used for the 81-feature pipeline — do not reimplement this independently).

For a candidate target disease `Tgt` (one of the 41):

| Feature | Definition | Target-specific? | Notes |
|---|---|---|---|
| `net_max_relative_risk` | `max` over `s ∈ S` of `RR(s → Tgt)`, using a neutral value (e.g., 1.0) if `S` is empty or has no edge to `Tgt` | Yes | Strongest single existing-condition association with the target |
| `net_mean_relative_risk` | mean over **all** `s ∈ S` of `RR(s → Tgt)`, treating any `s` with no computed/significant edge to `Tgt` as neutral (1.0) rather than excluding it | Yes | Averaging over the full diagnosis set (not just existing edges) avoids one strong edge dominating a patient with many conditions |
| `net_n_significant_edges` | count of `s ∈ S` where `(s → Tgt)` exists and passes the Section 3.3 significance flag | Yes | Integer |
| `net_shortest_path_length` | minimum unweighted hop count, over `s ∈ S`, from `s` to `Tgt` in the frozen graph; a fixed sentinel value if no path exists or `S` is empty | Yes | Start with unweighted hops for interpretability; only add edge-weighted shortest paths later if unweighted proves too coarse |
| `net_personalized_pagerank` | personalized PageRank on the frozen graph with a uniform restart distribution over `S`, read off at node `Tgt` | Yes | Can be computed **once per patient** (one PageRank vector per unique diagnosis set `S`) and looked up per target — do not rerun PageRank separately for each of the 41 targets |
| `net_target_degree_centrality` | degree centrality of node `Tgt` in the frozen graph | Yes, but **patient-independent** — a per-target constant | Precompute once per graph build; this is a property of the target, not the patient |
| `net_target_community_overlap` | fraction of `S` that shares a detected community (e.g., via Louvain, computed once at graph-build time) with `Tgt` | Yes | Continuous fraction, not a rigid 0/1, for smoother signal |
| `network_features_available` | boolean; false when the patient's diagnosis set doesn't map to any graph node at all (e.g., true cold-start patient) | No — one flag per patient | Metadata/diagnostic; confirm with the actual existing interface code whether it is meant to be a numeric model input or purely a UI/debug flag before wiring it either way |

### 4.1 Dimensionality — resolving the "41 × N" question

Six of the eight fields above are target-specific, giving 41 × 6 = 246 possible feature values in principle, plus one global availability flag. This does **not** need to become a 246+-column input to any single model: because the existing pipeline already trains **one independent stacked ensemble per target disease**, each per-disease model only ever needs the **7 network feature values scoped to its own target**. Concretely, the CHF model's feature vector becomes 81 clinical features + 7 CHF-specific network features = 88 columns — not 81 + 246. This is the natural, low-complexity integration path given the existing one-vs-rest architecture, and the plan below assumes it; if the implementing agent finds the current architecture is not actually one-model-per-disease, this dimensionality decision must be revisited and flagged.

---

## 5. Model integration

### 5.1 Integration approach

- **Append the 7 target-specific network features to the existing 81-feature vector** for each per-disease stack (Option A: direct concatenation), rather than building a separate network sub-model whose output is fused afterward (Option B). Concatenation reuses 100% of the existing base-learner, OOF-stacking, calibration, and explainability code paths unchanged — only the input feature matrix grows. A separate fusion architecture (Option B) is a reasonable escalation only if concatenation is shown to dilute the network signal (e.g., tree/LR importance on the new columns stays near zero) — it is not the starting design.
- **Versioning**: the existing release (81 features, all current results) is preserved completely unmodified as the reproducible conventional baseline. The network-integrated system is packaged as a **new release version** (e.g., the next version number after whatever the existing release is tagged, to be confirmed from the actual repo rather than assumed) with its own feature manifest (81 + 7 = 88 features, or 7 alone for the network-only arm), its own per-disease models/calibrators, and its own checksums/metadata. Nothing about the existing release's files, results, or manifest is edited in place.

### 5.2 Efficient experimental sequence (avoid wasted compute)

Run the arms in this order, stopping early if a step shows the network signal isn't worth pursuing further:

1. **Arm A — Existing clinical baseline.** Already trained and evaluated; no new work, just the existing numbers as the comparison point (Macro-AUPRC 0.0816, Macro-AUROC 0.8824, P@3 27.61%, R@3 68.51%, MAP@3 0.5869 for XGBoost/stacked ensemble as already reported).
2. **Arm B — Network-only, simple model first.** Train a single, cheap per-disease model (e.g., Logistic Regression, not the full stack) on the 7 network features alone, for all 41 diseases, on the existing split. This is a fast way to sanity-check whether the network features carry any signal at all before investing in a full retrain.
3. **Arm C — Clinical + network, single strong model.** Train XGBoost alone (not yet the full stack) on the 88-feature vector, per disease, and compare against the existing XGBoost-alone numbers. This isolates the incremental value of the network features from any effect of the stacking machinery itself.
4. **Decision point.** Only if Arm C shows a meaningful, consistent improvement over the equivalent clinical-only XGBoost result should the full per-disease stacked ensemble (LR + RF + XGBoost + OOF stacking + meta-LR + calibration) be retrained on the 88-feature vector for all 41 diseases as the final "Clinical + Network" release candidate. If Arm C shows no meaningful lift, that is reported as the finding — do not retrain the full 41-disease stack "just in case."
5. **Optional ablations** (time-permitting, not required for the core comparison): D — clinical + only the relative-risk-derived features (`net_max_relative_risk`, `net_mean_relative_risk`, `net_n_significant_edges`); E — clinical + only the structural features (`net_shortest_path_length`, `net_personalized_pagerank`, `net_target_degree_centrality`, `net_target_community_overlap`). This narrows down *which* kind of network signal, if any, is doing the work.

### 5.3 What all arms must hold constant

- The exact existing patient-level temporal split (same train/validation/test patient sets, same cohort sizes and test period given in Section 3.4).
- The same 41 target diseases and the same incident-label/masking definitions.
- The same primary and secondary metrics (Section 6).
- The same general modeling methodology (same base learners, same calibration approach) wherever a like-for-like comparison is being made — only the feature set changes between arms A/B/C.

---

## 6. Metrics and reporting

- **Primary**: Macro-AUPRC.
- **Secondary**: Macro-AUROC, Precision@3, Recall@3, MAP@3, Brier score (where a calibrated probability is available for the arm in question).
- Report per-disease AUPRC in addition to the macro average, and break results out by prevalence tier (high/medium/low), so a macro-average improvement isn't silently driven by only the most common diseases.
- Report the **delta versus the existing clinical baseline** explicitly for every arm and every metric — the headline deliverable of this stage is that delta table, not a new standalone number.
- Every reported number must be traceable to a specific experiment run/config; do not hand-average or eyeball comparisons.

---

## 7. Explainability integration

- Extend the existing explanation output (which already separates model-level contributions per base learner) to additionally separate **clinical signal from network signal**, without introducing a new causal framing:
  - **Clinical factors** (unchanged from today): age, disease history, disease burden, interaction features, etc.
  - **Network factors** (new): the strongest existing-condition association driving `net_max_relative_risk`, the count from `net_n_significant_edges`, and a qualitative proximity phrase derived from `net_shortest_path_length` (e.g., directly connected vs. not directly connected). Reserve raw numeric values (pagerank score, centrality, exact p-values) for the existing technical/"model details" disclosure layer, not the plain-language explanation.
- Language constraints, matching the project's existing non-causal convention: describe network evidence using terms like "association," "observed relationship," "network proximity," "predictive signal" — never "causes," "will develop," or "the network proves."

---

## 8. Streamlit integration

- **Comorbidity Network page**: replace the existing placeholder with a real, interactive rendering of the frozen graph — nodes, weighted/directed edges, a legend explaining what a node and an edge represent, search/select for a disease, filtering out weak edges, and (per the demo-patient example already described for the project) an optional overlay highlighting a selected patient's existing conditions and the network's proximity to their candidate future diseases.
- The visualization library is an implementation-time decision for the agent building this — evaluate what's already available/installed in the repository and prefer a lightweight, Streamlit-compatible option (e.g., a `pyvis`-style embedded HTML network or a Streamlit-native graph component) over introducing a heavy new frontend dependency; do not decide this in advance of inspecting the environment.
- **Disease Explorer**: extend to show, per disease, its graph degree, strongest connected diseases, and edge strengths — using the **same frozen graph artifact** as the Network page, not a separately generated one, so the two pages can never disagree with each other.
- **Risk Results**: at most a small, subtle additive indicator per prediction (e.g., noting when a prediction has meaningful network support) — this must not become a second, competing risk score next to the existing calibrated probability.
- **Explainability page**: add the "Network factors" section from Section 7 alongside the existing "Clinical factors" section.
- **Model & Research**: add the network methodology description and the Section 5–6 experiment/ablation results table.
- **Patient Assessment**: no change required — network features are derived entirely from the patient's already-collected diagnosis inputs; the form itself does not need new fields.
- Do not restructure pages or navigation beyond what's needed to add these elements — the existing page architecture stays as-is.

---

## 9. Likely files/modules affected (proposed — verify and adapt to the real repository)

```
data/graph/                      # frozen graph artifact: nodes, edges, metadata, version tag
src/graph/                       # graph construction: RR calculation, thresholding, freezing
src/features/network_interface.py   # existing interface/placeholder — replace stub with real
                                     # computation; confirm exact current location/contents first
src/models/                      # per-disease training code — extend to accept 88-feature input
                                  # for the new release version; do not modify how it trains
                                  # the existing 81-feature release
models/<new_release_version>/    # new, separate release bundle — models, calibrators, manifest,
                                  # checksums — parallel to and independent of the existing release
reports/network/                 # experiment results (Arms A–E), comparison tables, methodology writeup
streamlit_app/pages/comorbidity_network.py  # replace placeholder with real page
streamlit_app/pages/disease_explorer.py     # extend with graph-degree/connections view
streamlit_app/pages/explainability.py       # add network-factors section
tests/                           # new tests per Section 10
```

The implementing agent must confirm the actual current locations of the network interface, the release bundle, and the Streamlit pages before creating or editing any of the above — these paths are proposals based on conventional structure, not confirmed facts about this repository.

---

## 10. Required tests

At minimum, implement automated tests for:

1. Graph node correctness (expected node count/identifiers match the 41-target definition).
2. Edge calculation correctness (RR formula verified against a hand-computed example).
3. Edge-thresholding correctness (support/significance/effect-size filters behave as specified).
4. Deterministic graph generation (same input + same code + same seed → identical artifact/checksum).
5. Temporal cutoff enforcement (no landmark or label outside the intended horizon contributes to an edge).
6. No future-diagnosis leakage (a patient's post-landmark diagnoses never enter the `S` set used to query the graph for that landmark).
7. Graph-construction split enforcement (assert zero validation/test patient contribution to edge statistics).
8. Patient-level network feature correctness (hand-verified example patient, matching Section 8's demo-patient case).
9. Target-specific feature correctness and dimensionality (each per-disease model receives exactly its own 7 network features, not all 41×7).
10. Missing/unmapped disease handling (a diagnosis not in the node set doesn't crash feature generation, and is handled per the `network_features_available` definition).
11. Network-only inference path (Arm B model loads and predicts correctly).
12. Clinical+network inference path (Arm C/final model loads and predicts correctly).
13. Existing baseline still reproduces its already-reported numbers exactly (regression test against the existing release).
14. Existing release bundle remains loadable and unmodified (file-level check, not just behavioral).
15. Streamlit Comorbidity Network page renders without error and reflects the frozen graph artifact.
16. End-to-end reproducibility: rebuilding the graph and regenerating network features from the same training-split data produces the same artifact and the same downstream feature values.

Extend the existing leakage-audit framework with items 5–9 above rather than building a separate, parallel testing system.

---

## 11. Computational approach

- Build the graph via SQL aggregation (DuckDB over the existing Parquet-based landmark/label tables) — the pairwise contingency-table counts behind each edge are small aggregations over a bounded set of candidate disease pairs, not a dense patient × disease × disease matrix.
- The graph itself (a few dozen nodes, at most a few thousand candidate edges before thresholding) is trivially small to hold in memory and to run NetworkX operations (shortest path, PageRank, community detection) against — no need for distributed or approximate graph algorithms at this scale.
- Precompute per-target, patient-independent quantities (degree centrality, community assignment) once at graph-build time.
- Precompute, per unique patient diagnosis set, the personalized PageRank vector once, and look up per-target values from it, rather than rerunning PageRank per target.
- Cache the frozen graph and any precomputed per-target constants as versioned artifacts; patient-specific feature generation at training or inference time reads from these cached artifacts, it does not rebuild or requery the graph.

---

## 12. What must NOT change

- The existing 81-feature clinical release, its models, calibrators, manifest, and reported results.
- The existing patient-level temporal train/validation/test split (cohort sizes and test period given in Section 3.4).
- The existing 41 target-disease definitions and incident-label/masking logic.
- The existing non-causal explanation language convention.
- The existing Streamlit page architecture/navigation, beyond the specific additive changes in Section 8.
- No existing report, checksum, or manifest is edited in place; new results live in new, separate artifacts.

---

## 13. Definition of done

- A frozen, versioned disease graph artifact exists, built strictly from training-split data, with documented node/edge definitions and thresholding parameters.
- All 8 planned network features are implemented against real graph data (no remaining stub/placeholder values in the production feature path) and pass the correctness tests in Section 10.
- Arms A (existing), B (network-only), and C (clinical + network) have all been run on the identical existing split, and a comparison report exists showing the delta on every metric in Section 6, including per-disease and prevalence-tier breakdowns.
- A decision has been made and documented on whether the full per-disease stacked ensemble was retrained with network features, based on the Arm C result — not retrained reflexively regardless of outcome.
- If a network-integrated release was produced, it exists as a new, independently versioned release bundle, and the existing baseline release still loads and reproduces its original results unchanged.
- The Comorbidity Network Streamlit page shows the real graph (no placeholder remains), Disease Explorer and Explainability reflect the same graph artifact and network-factor evidence, and the rest of the application's existing workflow is unaffected.
- All required tests (Section 10) pass, including the regression test proving the existing baseline is unchanged.
- A short written summary states plainly whether the network features provided incremental predictive value — a "no" is an acceptable, complete answer.

---

## 14. Implementation order (summary)

1. Graph construction (nodes, edges, RR + thresholding, train-split-only, freeze artifact).
2. Network feature implementation against the frozen graph, replacing the existing stub interface.
3. Validation/leakage-audit tests for the graph and the features (Section 10, items 1–10), run before any model touches these features.
4. Model integration: Arm B (network-only, simple model) → Arm C (clinical+network, single strong model) → decision point → full stack retrain only if justified, packaged as a new release version.
5. Experiment/ablation run and comparison report (Arms A–E as applicable), against the unchanged existing split.
6. Explainability integration (clinical-vs-network factor separation).
7. Streamlit integration (real Network page, Disease Explorer/Explainability extensions).
8. Final reproducibility pass: regenerate the graph, features, and any new release from scratch, confirm the existing baseline is untouched, and confirm all tests pass.
