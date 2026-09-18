# Prompt for Antigravity: Comorbidity Prediction Tool — Clinical UI Redesign

Copy everything below this line into Antigravity as one prompt.

---

## 0. Role and mandate

You are redesigning the frontend of an existing, working medical decision-support application. The ML backend is complete, tested, and must not be rewritten or duplicated. Your job is an **information-architecture and UI redesign**, not a CSS reskin of the current page.

Before writing any code:

1. Inspect the existing Streamlit application end to end — every page, every component, every helper function currently used to render the UI.
2. Inspect `src/inference/predict.py` and everything it depends on — the `PatientInput` model, the feature construction step, the masking logic, the calibration step, the thresholding logic, and the explainability outputs it returns. Treat its public interface as fixed.
3. Inspect `models/release_v1` to understand what artifacts exist and what metadata (version, thresholds, feature manifest) is available to display.
4. Identify every piece of functionality currently implemented anywhere in the UI — including things buried in expanders or shown only in technical/debug sections — and produce an inventory before deleting or moving anything. Nothing in this list gets dropped; it gets relocated to the right page under this new architecture:
   - Patient input (demographics, existing conditions, background conditions, observation history)
   - Archetype/example-patient loading
   - The 41-target prediction run
   - Already-diagnosed condition masking
   - Calibrated probabilities and decision thresholds
   - Top-N control
   - Per-condition explanations (feature attributions, model contributions)
   - Batch prediction capability, if it exists
   - Full 41-target result view (not just the top-N)
   - Model package/version loading and metadata
5. Only after steps 1–4 are complete, design the new information architecture, the design system, and the reusable components — then implement pages.

Do not add CSS to the current monolithic `app.py`. Restructure it.

---

## 1. What is fundamentally wrong with the current UI (baseline audit)

The current UI is a single Streamlit page that works but reads as an ML dashboard rather than a clinical tool:

- Everything lives on one page, causing excessive vertical scrolling.
- Emoji-heavy section headers and generic Streamlit default styling.
- Too many competing cards with no clear hierarchy.
- Raw OMOP concept IDs and raw feature names (e.g. `has_hist_4115276`) are shown to the user.
- Internal model-engineering detail — inference latency, meta-learner logit contributions, CUDA/runtime details — is shown prominently, mixed into the clinical output instead of separated from it.
- Explanations are buried in deeply nested expanders instead of being a first-class part of the results.
- Diagnosis selection is one large multiselect with no structure, search, or grouping.
- Technical and clinical information are interleaved throughout, so nothing has priority.

The net effect: the tool looks like a model demonstration, not a piece of clinical software a clinician or researcher would trust. Every decision below is aimed at fixing that, specifically.

---

## 2. UX philosophy

Design toward: **professional, calm, trustworthy, light-themed, spacious, restrained, highly readable, information-dense without feeling cluttered.**

Design away from: AI-startup landing pages, generic SaaS dashboards, cybersecurity-style dashboards, glassmorphism, neon/gradient "futuristic AI" aesthetics, decorative illustrations, emoji as iconography, oversized rounded hero cards, or marketing language like "AI-powered health insights."

Draw on the underlying principles behind mature healthcare products (NHS digital services, Epic/MyChart, Mayo Clinic) rather than copying their branding or layouts specifically:

- Clear, single-purpose information hierarchy per screen.
- Plain-language explanation alongside precise medical terminology — never instead of it.
- Strong, deliberate whitespace instead of visual density achieved through boxes and gradients.
- Accessible, restrained color — color reinforces meaning, it does not decorate.
- Predictable, shallow navigation the user can form a mental model of immediately.
- Progressive disclosure: show the clinically relevant conclusion first, let the user opt into the mechanism behind it.
- Forms that read like a structured clinical intake, not a generic web form.
- Alerts and risk indicators that are clinically meaningful, not decorative severity theater.

Every visual element must justify its presence. If a card, icon, badge, or color has no functional purpose, remove it.

---

## 3. Information architecture — final navigation and reasoning

Do not invent a different structure than the one below without strong justification documented in your implementation notes. The reasoning follows the actual clinical workflow a user goes through, in order: orient → provide patient information → get a result → understand the result → explore reference material → (later) explore relationships. Model governance is explicitly *not* part of that workflow, so it does not sit in the primary navigation.

**Primary navigation (top-level, always visible):**

1. **Overview** — orientation and entry point.
2. **Patient Assessment** — the structured intake form; where a prediction is actually run.
3. **Risk Results** — the primary clinical deliverable: ranked, calibrated, explained predictions for the current patient/session.
4. **Explainability** — a deeper, per-condition and model-consensus view, reached primarily *from* Risk Results, but also directly navigable; if no assessment has been run yet, show an empty state directing the user back to Patient Assessment rather than a broken or empty page.
5. **Disease Explorer** — a reference browser for the 41 supported comorbidities, independent of any active session. Useful before, during, or after running an assessment.
6. **Comorbidity Network** — reserved navigation slot for the future graph/network feature. Present now as a clearly-labeled, disabled-or-placeholder entry (see Section 9), never as fake or simulated network output.

**Secondary/footer navigation (visually and structurally separated from the clinical workflow):**

7. **Model & Research** — benchmark results, calibration curves, ablation results, explainability methodology, model version, reproducibility notes, leakage-audit summary. This exists for research/demo credibility, not for a clinician working through a patient. Style it so it's obviously a different *kind* of page (e.g., a distinct sidebar section titled "Research" or a footer link), not a seventh peer of the clinical workflow.

**Why "Explainability" is its own page and not just an expander on Results:** the deck's explainability requirement (existing-condition evidence + model-level evidence + eventually network evidence) has enough content — per-condition attribution, LR/RF/XGBoost consensus, patient-specific factors — that cramming it into the Results page either bloats that page or forces it back into nested expanders, which is exactly the current failure mode. Keeping it a distinct page reached by a clear "View explanation" action per risk card gives it room to be genuinely readable, while Results stays focused on "what, how likely, new-or-not."

**Why Disease Explorer is decoupled from an active session:** browsing what the model can predict, and what each condition means, is useful independent of any specific patient — e.g., before starting an assessment, or for someone evaluating the tool. Coupling it to session state would force an unnecessary dependency.

**Why Network gets a reserved slot now, not later:** adding a sixth nav item later would restructure navigation the user has already learned. Reserving the slot with an honest "not yet available" state costs nothing now and avoids that churn later.

---

## 4. Session/state model

Use `st.session_state` to hold:

- The current `PatientInput` (or `None` if no assessment has been started).
- The current prediction result object returned by `src/inference/predict.py` (or `None`).
- Whatever minimal metadata (timestamp, archetype name if loaded from one) is useful for the Overview page's "current session" summary.

Risk Results, Explainability, and the Overview page's session summary all read from this shared state rather than re-running inference or maintaining their own copies. If no assessment exists yet, Risk Results and Explainability must show a clear, non-technical empty state with a direct call-to-action back to Patient Assessment — never a blank page or a stack trace.

---

## 5. Page-by-page specification

### 5.1 Overview

Purpose: orient a new user, and give a returning user a fast path back into their current work.

Contents:
- A short, plain-language description of what the tool does and does not do (predicts *likely future comorbidities* from current patient information; it is a decision-support aid, not a diagnosis).
- A single clear primary call-to-action: **Start a patient assessment**.
- If a session already exists: a compact summary card (patient age/sex, number of existing conditions entered, number of predicted elevated-risk conditions) with a link straight into Risk Results, so a returning user doesn't have to re-navigate through the whole flow.
- No statistics, no marketing copy, no decorative hero section.

### 5.2 Patient Assessment (the form)

This is one of the most important surfaces in the redesign. See Section 6 for the full form specification. This page ends in a single clear primary action (**Run assessment**), which calls `src/inference/predict.py` and stores the result in session state, then navigates to Risk Results.

### 5.3 Risk Results

Purpose: the primary clinical deliverable. Prioritize, in this order, matching how a clinician actually reads a result:

1. What conditions are predicted.
2. How likely (calibrated 1-year risk, risk category).
3. Which are newly at-risk vs. which the patient already has (masking is visible and explained, not silently applied).
4. A short "why this was surfaced" summary per condition.
5. How the risk compares to a population baseline.

Layout: a ranked list of risk cards (Section 7), Top-N control preserved, with a visible, unobtrusive way to expand to the full 41-target view (this must not be deleted — see Section 5.7). Anything not on the five-point list above — inference latency, release version, raw probabilities, meta-learner logits, raw feature identifiers — must not appear on this page. Route it to Explainability's "Model details" disclosure (Section 5.4) or to Model & Research (Section 5.7).

### 5.4 Explainability

Purpose: answer "why" in more depth than the Results page's short summary, for a specific condition or for the assessment as a whole.

Structure, using progressive disclosure:
- **Plain-language layer (default, always visible):** risk-increasing factors and protective/lower-risk factors, expressed as human-readable clinical concepts (e.g., "History of hypertension," "Older age," "No recorded history of chronic kidney disease") — never as raw feature identifiers.
- **Model details (opt-in disclosure, collapsed by default):** LR / Random Forest / XGBoost individual contributions, ensemble/meta-learner weighting, and — only here — raw technical feature identifiers, for a technical or research audience that explicitly wants them.
- Reached from a "View explanation" action on each Risk Results card, scoped to that condition, and also directly navigable for a broader per-assessment view.
- If no assessment exists yet, show the same kind of empty state as Risk Results.

### 5.5 Disease Explorer

Purpose: browse and understand the 41 supported comorbidities independent of any specific patient.

Contents:
- Search and filter by clinical category (do not rely on one long unfiltered list).
- Each entry: medical term (precise, not dumbed down) + short plain-language explanation, using the reusable medical-term component from Section 6.5.
- Where genuinely supported by the model/data (not invented), show model-relevant context such as how the condition is modeled (target vs. background condition) — do not surface fabricated prevalence statistics.

### 5.6 Comorbidity Network (placeholder)

Purpose now: reserve the architectural and navigational slot; make it obvious the ML-only workflow is already complete and usable without it.

- A single, honest placeholder state: this feature is planned, will show patient conditions and predicted conditions as nodes with relationship evidence between them, and is not yet available — no simulated graph, no fabricated relationships, no fake data standing in for it.
- Design the page container/route now so that when the real network component is integrated, it drops into this slot without further navigation changes.

### 5.7 Model & Research (secondary nav)

Purpose: house everything that is legitimate and valuable for a research/demo audience but has no place in a clinical workflow.

Contents (relocated from the current monolithic page, not deleted):
- Model version / release bundle metadata (`models/release_v1`).
- Benchmark results (baseline vs. base learners vs. stacked ensemble).
- Calibration curves / Brier scores.
- Ablation results.
- Explainability methodology write-up (how SHAP/coefficients/meta-weights are used).
- Leakage-audit and reproducibility summary.
- The full, un-thresholded 41-target result table for the current session, if one exists (this preserves the "full 41-target results" capability without cluttering Risk Results, which defaults to Top-N).
- Inference latency, CUDA/runtime details, and any other implementation-level diagnostics belong here, if shown at all — never in the clinical workflow pages.

---

## 6. Patient Assessment form — detailed UX specification

The form must feel like a structured clinical intake a clinician could actually work through, not a generic web form or one giant multiselect.

### 6.1 Section structure

Group fields by clinical meaning, in this order, each a clearly separated, collapsible-if-needed section rather than one continuous scroll of unrelated fields:

1. **Patient demographics** — age, biological sex, race, ethnicity (mark clearly which are required vs. optional, consistent with what `PatientInput` actually requires).
2. **Existing chronic conditions** — the conditions driving the 41-target prediction and masking logic.
3. **Background/relevant history** — the (currently: 17) background conditions that inform prediction without being prediction targets themselves; explain in one short line what distinguishes this section from section 2, so the distinction is not left implicit.
4. **Observation history** — whatever observation-span/history-length input the current pipeline requires, with a short explanation of why it matters (history length affects how much can be inferred).

Improve this grouping if inspection of the actual `PatientInput` fields reveals a clearer split, but preserve the underlying principle: group by clinical meaning, not by data type or form-widget convenience.

### 6.2 Condition selection UX (replacing the giant multiselect)

Replace the single large multiselect with:
- A **search box** to find a condition by name.
- Conditions grouped by clinical category, browsable without searching.
- A short list of **common-condition shortcuts** (one-click add for the most frequently entered conditions) above or beside the search/browse UI.
- Selected conditions shown as **removable chips**, so the current selection is always visible without opening the picker again.
- Each condition option shows the plain-language explanation pattern (Section 6.5) inline or on hover/expand, so a user unfamiliar with a specific term isn't blocked.

### 6.3 Field-level UX

- Clear, unambiguous labels; helper text under any field whose meaning isn't self-evident.
- Sensible field widths (a two-character sex selector should not be full-width; a condition search box should be).
- Explicit required-vs-optional marking, consistent with actual backend validation in `PatientInput`.
- Inline validation with plain-language error messages (not raw exceptions).
- A clear, singular primary call-to-action (**Run assessment**) — no competing secondary buttons of equal visual weight.
- Good empty states for the condition pickers before anything is selected ("No conditions added yet — search or browse above").
- Preserve archetype/example-patient loading as a distinct, clearly optional entry point (e.g., "Load an example patient") that pre-fills the form rather than bypassing it.

### 6.4 What this section must not do

Do not flatten this into a single scroll of unrelated inputs, and do not split it into pages so granular that running an assessment requires excessive back-and-forth. The target is: one page, clearly sectioned, with the condition-selection UX doing the heavy lifting of managing complexity within section 2/3, not the page structure doing it via fragmentation.

### 6.5 Reusable medical-term + plain-language component

Design and use this pattern everywhere a medical term appears anywhere in the app (form, Results cards, Explainability, Disease Explorer):

```
[Medical term, precise and un-simplified]
[One short sentence of plain-language explanation]
[Optional: "Learn more" → expands to further detail, if available]
```

Constraints:
- The medical term itself is never simplified or renamed — precision is preserved.
- The plain-language line is one short sentence, not a paragraph.
- Do not invent unsupported medical facts to populate this component. Instead, build a **structured disease/condition metadata layer** (e.g., a lookup keyed by condition/concept identifier, with fields for canonical term, plain-language explanation, category, and optional extended detail) that can be populated and clinically reviewed over time. Where a description does not yet exist in this metadata layer, show the term alone with an honest "Description not yet available" state rather than a fabricated explanation.
- This component and its backing metadata layer should be a single reusable module, not re-implemented per page.

---

## 7. Risk card component — detailed specification

Design one reusable risk-card component used throughout Risk Results (and referenced, in a denser form, from Explainability). Structure (content and hierarchy shown below; do not treat the exact copy or numbers as literal content to hardcode):

```
01

Chronic Kidney Disease, Stage 1
[plain-language explanation, one sentence — via the Section 6.5 component]

1-year predicted risk        Risk level         Compared with population
        8.4%                  Elevated              2.4× baseline

Why this was surfaced
- Hypertension
- Type 2 diabetes
- Age-related risk

[View explanation →]
```

Requirements:
- Rank/number, condition name + plain-language line, the three risk metrics (probability, categorical risk level, population comparison), a short bulleted "why surfaced" list (2–4 items, plain-language, not raw feature names), and a single subtle action into the Explainability page for that condition.
- Risk level must not rely on color alone — pair a semantic risk color with a text label ("Elevated," "Moderate," "Low") for accessibility.
- Avoid large colorful dashboard-style cards, drop shadows, gradients, or decorative icons. This is a quiet, information-dense card, not a hero element.
- The already-diagnosed masking behavior must be visible and explained where relevant — e.g., a clearly separated note or section indicating which conditions were excluded because the patient already has them, rather than silently dropping them with no trace.

---

## 8. Explainability UX — detailed specification

Two layers, strictly separated, in this order:

**Layer 1 — plain-language (default view):**
- **Risk-increasing factors** — a short list of human-readable clinical concepts (e.g., "History of hypertension," "Older age," "Previous metabolic disease").
- **Protective / lower-risk factors** — same format, e.g., "No recorded history of chronic kidney disease."
- These must be translated from the underlying feature attributions — never show a raw feature identifier or a raw contribution score in this layer.

**Layer 2 — "Model details" (progressive disclosure, collapsed by default):**
- Per-base-learner contribution (Logistic Regression, Random Forest, XGBoost).
- Ensemble/meta-learner weighting for this prediction.
- Raw technical feature identifiers, if shown at all, only here.

This mirrors the existing backend's explainability output structure — the change is entirely in what is surfaced by default versus behind an explicit, clearly-labeled disclosure, not in what the backend computes.

---

## 9. Design system

Specify and implement as a single, coherent system — do not style components individually and ad hoc.

- **Typography**: a restrained, highly legible sans-serif system stack or a single web-safe/professional font (avoid decorative or "techy" fonts); define a small type scale (e.g., page title, section heading, body, caption/helper text) and use it consistently — no ad hoc font sizes.
- **Layout**: a sensible max content width (avoid full-bleed edge-to-edge text on wide monitors); consistent page padding; a spacing scale (e.g., a 4/8px-based scale) used for all margins/gaps instead of arbitrary values.
- **Color**:
  - Light theme only. Neutral background and surface colors (whites/very light grays), not stark pure white if it reduces glare/contrast comfort.
  - One restrained primary color for navigation/primary actions, used sparingly.
  - A small set of **semantic risk colors** (e.g., low/moderate/elevated/high) chosen for accessible contrast, always paired with a text label, never color-only.
  - No neon, no gradients, no glassmorphism, no glow effects.
- **Borders and radius**: subtle, consistent border radius (small, not pill-shaped everywhere); thin, low-contrast borders rather than heavy drop shadows to separate surfaces.
- **Components to define once and reuse**: buttons (primary/secondary, not more than needed), form inputs, cards (including the risk card from Section 7 and the medical-term component from Section 6.5), badges/labels (for risk level, category, "new" vs. "existing" condition), tabs/navigation, alerts (used only for genuinely important, clinically meaningful messages — not decoration), tables (for the full 41-target view and Model & Research), empty states, and loading states.
- **Icons**: if used at all, a single consistent icon set, used sparingly and only where it aids scanning (e.g., a small indicator next to risk level) — never emoji, never decorative.

---

## 10. Accessibility requirements

- Meet WCAG-level contrast expectations for all text and semantic risk colors against their backgrounds.
- Risk status must never be communicated by color alone — always pair with a text label.
- Full keyboard navigability and visible, clear focus states across the form, navigation, and any interactive card elements.
- Use real semantic heading levels (page title, section headings, subheadings) so the document structure is meaningful, not just visually styled text.
- Every form field has a real, associated label (not placeholder-text-only labeling) and helper text where the field's meaning isn't self-evident.
- Maintain a logical reading and tab order through each page, especially the form and the risk-card list.
- Choose body text sizing for comfortable reading, not compressed to fit more on screen.

---

## 11. Responsiveness

- Target desktop and laptop widths as the primary use case (this is a clinical/research tool, not a mobile-first consumer product), but the layout must not visually break at narrower browser widths.
- Avoid fixed multi-column grids (e.g., a rigid 4-column layout) that collapse awkwardly; prefer flexible layouts with sensible max widths and wrapping behavior.
- Test the form, risk-card list, and Disease Explorer at a few representative widths (e.g., a narrow laptop window) as part of implementation QA.

---

## 12. Streamlit implementation architecture

The implementation stays in Streamlit. Do not propose a React/Next.js rewrite.

- Use Streamlit's multipage app structure (a `pages/`-based or `st.navigation`/`st.Page`-based architecture, whichever is best supported by the current Streamlit version in use) to implement the navigation from Section 3 as real, separate pages — not tabs or expanders simulating pages on one script.
- Organize the app directory so components are genuinely reusable, roughly:

```text
streamlit_app/
├── navigation/         # page registration / nav structure
├── pages/              # Overview, Assessment, Results, Explainability,
│                       # Disease Explorer, Network (placeholder), Model & Research
├── components/         # risk_card, medical_term, condition_picker, empty_state, etc.
├── styles/             # design-system tokens (colors, spacing, typography), theme CSS
├── disease_metadata/   # the structured term/description lookup from Section 6.5
├── state/              # session-state helpers (current PatientInput, current result)
└── app.py              # thin entry point wiring navigation together
```

- `src/inference/predict.py` remains the single source of truth for prediction. The Patient Assessment page calls it directly; no page reimplements feature construction, masking, calibration, or thresholding logic itself.
- Do not duplicate any model logic, feature-encoding logic, or masking logic inside the UI layer. If the UI needs derived display values (e.g., a human-readable risk category label from a numeric probability), that mapping lives in a small, explicit UI-layer utility — it does not reimplement anything `src/inference` already computes.
- Adjust the exact structure above if inspection of the current codebase suggests a better fit, but preserve the underlying separation: navigation, pages, reusable components, design-system tokens, disease metadata, and session-state handling are distinct concerns, not folded into one file.

---

## 13. What must NOT change in the backend

- `src/inference/predict.py` and its public interface (`PatientInput`, the prediction/result objects it returns) are fixed. Do not modify their behavior to suit the UI; if the UI needs something the current interface doesn't expose, surface that as a note rather than silently changing backend behavior.
- `models/release_v1` and its packaged models/calibrators are not touched.
- The 41 target comorbidities, the background-condition set, already-diagnosed masking, calibrated probabilities, and decision-threshold logic are not altered — only how they are displayed changes.
- The network/graph component is not implemented, simulated, or faked as part of this task.

---

## 14. Testing requirements

- The full existing suite must continue to pass: `pytest -v tests/`. Do not break inference functionality while restructuring the UI layer.
- Add UI-specific tests where practical for:
  - Navigation between all pages.
  - Patient form submission (including archetype loading) correctly populating `PatientInput` and invoking `src/inference/predict.py`.
  - Already-diagnosed masking being correctly reflected in what Risk Results displays.
  - Result rendering for both the Top-N view and the full 41-target view.
  - Explainability rendering for both the plain-language layer and the "Model details" disclosure.
  - Disease Explorer search/filter behavior.
  - The Comorbidity Network placeholder rendering without error and without fabricating data.
  - Basic responsive behavior at a narrower viewport width, as far as Streamlit's testing tools permit.
- Document any test that cannot be automated (e.g., fine-grained visual/responsive QA) as a manual verification step instead of skipping it silently.

---

## 15. Definition of done

- The application is a genuine multipage Streamlit app matching the navigation and page responsibilities in Section 3, not a single page with tabs or expanders standing in for pages.
- No raw feature identifiers, OMOP concept IDs, inference latency, meta-learner logits, or other implementation-level detail appear anywhere in Overview, Patient Assessment, Risk Results, Disease Explorer, or the plain-language layer of Explainability. That information is fully relocated to Model & Research or to the explicit "Model details" disclosure in Explainability — not deleted.
- Every currently-working piece of functionality listed in Section 0's inventory still works, on its new page.
- A reusable design system (Section 9), a reusable risk-card component (Section 7), and a reusable medical-term component with a backing metadata layer (Section 6.5) exist and are used consistently, rather than each page styling its own version.
- `pytest -v tests/` passes in full, plus the new UI-specific tests from Section 14.
- The Comorbidity Network page exists as an honest, non-fake placeholder, and the rest of the application is fully usable without it.
- The result, evaluated by someone unfamiliar with the project, reads as a credible clinical decision-support tool — not a machine-learning demo.
