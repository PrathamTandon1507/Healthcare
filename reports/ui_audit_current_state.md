# UI State Audit & Structural Assessment Report

**Target**: Streamlit User Interface (`streamlit_app/app.py`, `app.py`)  
**Purpose**: Comprehensive audit of the current UI state to establish a baseline before redesigning the clinical decision-support interface.  
**Constraint**: Inspection and documentation only — zero modifications made to application code or UI styles.

---

## 1. Current Page Structure

### Page & View Architecture
- **Single Monolithic View**: Currently, the entire application is implemented as a single, flat Python script ([`streamlit_app/app.py`](file:///c:/Users/Pratham/Documents/Healthcare/streamlit_app/app.py), 424 lines) configured with `st.set_page_config(layout="wide")`.
- **No Multi-Page Navigation**: There is no multi-page routing (`pages/` directory or tabbed sub-views). Every feature (archetype selection, patient demographic intake, chronic condition selection, metric summaries, risk cards, SHAP explanations, base-model weights, and full data tables) is stacked vertically on one page.

### Top-to-Bottom Layout Flow
```
┌────────────────────────────────────────────────────────────────────────┐
│ SIDEBAR: Logo, Engine Title, Threshold Strategy, Top-N, Masking, Info   │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Header & System Subtitle                                            │
│ 2. Blue Informational Callout (Section 1.5 Masking Explanation)        │
│ 3. Horizontal Divider (---)                                            │
│ 4. Archetype Quick-Fill Dropdown (2:1 column split)                    │
│ 5. Patient Intake Form Container (st.form):                            │
│    ├── Demographics: Age, Sex, Race, Ethnicity (4 columns)             │
│    ├── Medical History: 58-option Multi-select Dropdown                │
│    ├── Advanced History: Observation Span Slider (in expander)         │
│    └── Submit Button: "Run Comorbidity Risk Assessment"                │
│ 6. Results Section (rendered after form submission):                   │
│    ├── Summary Metrics (4 KPI tiles: Age/Sex, Diagnoses, Targets, Lat) │
│    ├── Pre-Existing Chronic Diagnoses (in expander, 3 columns)         │
│    ├── Top-N Surfaced Comorbidity Risk Cards (Custom HTML divs)        │
│    │   └── Inside each Card: Deep-Dive Explanation Expander            │
│    │       ├── Left: Base Model Ensemble Weight Dataframe              │
│    │       └── Right: Top Risk-Increasing & Protective Factor Lists    │
│    └── Full 41-Target Risk Table (in expander, raw dataframe)          │
│ 7. Footer Banner                                                       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Visual Design & Component Styling

### Typography & Hierarchy
- **Font Stack**: Default Streamlit browser fonts (Source Sans Pro / Helvetica Neue). No typography scale tailored for clinical EHR interfaces.
- **Header Levels**: `st.title` (H1) $\rightarrow$ `st.subheader` (H3) $\rightarrow$ `st.markdown("##### ...")` (H5). Headings are visually disparate and lack unified section numbering or visual cards.

### Colors & Contrast
- **Generic Bootstrap Palette**: Risk alerts use hardcoded legacy hex codes:
  - High Risk: `#d9534f` (Bootstrap danger red)
  - Moderate Risk: `#f0ad4e` (Bootstrap warning orange)
  - Low Risk: `#5cb85c` (Bootstrap success green)
- **Hardcoded Light Mode Assumption**: The HTML risk cards enforce `#fcfcfc` backgrounds and `#e0e0e0` borders. If the user or browser operates in dark mode, these cards render with jarring white backgrounds and light text contrast issues.

### Component Styling
- **Inconsistent Card Usage**: Only the Top-N results use card containers (via inline HTML strings); the intake form, metrics, and explanations use unstyled Streamlit native containers.
- **Emoji Saturation**: Heavy emoji usage across headers and buttons (`🏥`, `👤`, `🩺`, `⏱️`, `🚀`, `📊`, `📋`, `🎯`, `🚨`, `🔍`, `🤖`, `📈`, `🛡️`, `⚖️`, `📑`, `📦`, `⚙️`). This gives the interface a playful, hackathon/demo feel rather than an enterprise clinical decision support appearance.

---

## 3. Clinical & Professional Feel

### Credibility Assessment
- **Current Impression**: Looks like a **data science model demonstration dashboard** rather than an EHR-integrated clinical decision-support tool.
- **Elements Damaging Clinical Credibility**:
  1. **Direct Exposure of ML Engineering Metrics**: Displaying "Inference Latency: 1.409s", "Meta-Learner Logit Contribution", "Base Model Probability: 0.12%", and "Release Bundle v1.0.0" directly in the primary clinician view.
  2. **Raw Database Column Names**: Feature attribution displays database strings like `has_hist_4115276`, `total_prior_condition_count`, and `bg_viral_sinusitis`.
  3. **OMOP Concept ID Clutter**: Surfacing raw integers (`CID: 201826`, `CID: 316866`) prominently next to disease names.
  4. **Unsorted Multiselect**: The condition input is an unorganized dropdown with 58 text strings that requires active typing to find common conditions.

### High-Value Clinical Elements to Preserve
1. **Section 1.5 Already-Diagnosed Masking**: Clear distinction between existing chronic illnesses and newly candidate incident comorbidities is clinically sound and crucial.
2. **Calibrated Probability vs. Population Multiplier**: Presenting calibrated risk alongside relative risk multipliers (e.g. "$2.4\times$ baseline population risk") is intuitive for clinical risk assessment.
3. **Structured Patient Archetypes**: Fast switching between representative patient profiles (Diabetic/Hypertensive, Heart Failure, Metabolic Syndrome, Asthmatic, Baseline) provides immediate evaluation utility.
4. **Attribution Separation**: Separating model consensus (LR vs RF vs XGB) from patient risk factors (SHAP features) aligns with explainability best practices.

---

## 4. User Experience (UX) & Interaction Flow

### Data Input & Selection
- **Demographics**: 4 input fields placed in `st.columns(4)`. Age input uses `st.number_input` which requires typing or clicking small increment buttons.
- **Diagnoses Selection**: A single large `st.multiselect` containing 58 options. Selecting 5–6 conditions requires opening the dropdown repeatedly, scrolling, or typing exact substrings. There is no category accordion, body system grouping, or quick-toggle chips for high-frequency conditions (e.g., HTN, T2D, Hyperlipidemia).
- **Form Submission**: Users must click the red "Run Comorbidity Risk Assessment" submit button. If an archetype is selected from the top dropdown, the form updates its fields, but the user still has to scroll down and click submit to trigger re-computation.

### Results Inspection & Cognitive Load
- **Heavy Vertical Scrolling**: With 5 surfaced conditions and their explanation expanders open, the user must scroll through over **2,200 pixels** of vertical content.
- **Nested Expanders**: Crucial clinical explanations are hidden inside collapsible `st.expander` elements within custom HTML divs, requiring 5+ clicks to compare why different diseases were surfaced.
- **Scattered Settings**: Decision threshold strategy (`f1_optimal`, `recall_80_threshold`, `prevalence_matched_threshold`) is tucked in the sidebar, far from the actual risk score cards it modifies.

---

## 5. Information Hierarchy & Attention Competition

| Information Tier | Current UI Elements | Clinical Priority | Assessment |
|---|---|---|---|
| **Primary (Clinician-Critical)** | Top Surfaced Diseases, Calibrated Risk %, Risk Flags, Existing Conditions | **Critical** | Diluted by technical metrics and nested inside expanders. |
| **Secondary (Contextual)** | Population baseline comparison, Decision threshold values, Patient Demographics | **High** | Displayed in small gray text inside custom card footers. |
| **Tertiary (Explainability)** | Top risk-increasing factors, Protective factors | **High** | Hidden inside collapsed expanders requiring manual clicks. |
| **Technical / Diagnostics** | Inference latency, Meta-learner weights, Logit contributions, Model release version | **Low (Audit only)** | Prominently displayed alongside clinical risk outputs. |
| **Configuration** | Threshold strategy, Top-N slider, Masking toggle | **Administrative** | Hidden in sidebar, detached from result cards. |

---

## 6. Current Results Presentation (41 Comorbidities)

1. **Top-N Surfaced Cards**: Renders $N$ custom HTML cards. Shows Rank, Disease Name, Category, Concept ID, Risk Tier badge, 1-Year Calibrated Risk %, Decision Threshold %, Risk Status flag, and Population Multiplier.
2. **Clinical Explanation Panels**:
   - Left side: Table of 3 base models with Base Probability %, Meta-Learner Weight ($\alpha$), and Logit Contribution score.
   - Right side: Bullet list of 4 risk-increasing factors and 3 protective factors with attribution values.
   - Bottom: Standardized statistical disclaimer caption.
3. **Pre-Existing Diagnoses Display**: Collapsible card with a 3-column markdown grid showing confirmed pre-existing conditions.
4. **Complete 41-Target Data Table**: A raw pandas dataframe inside a bottom expander containing all 41 candidate diseases sorted by risk.

---

## 7. Technical & Demo Artifacts Identified

- **"Inference Latency: 0.812s"**: A developer performance KPI with no clinical diagnostic utility.
- **"Logit Contribution: 2.140"**: Mathematical log-odds contribution from the meta-learner logistic regression, opaque to medical practitioners.
- **"CID: 75036"**: Raw OMOP standard vocabulary keys displayed as primary labels.
- **"Base Learner: XGBoost (CUDA)"**: Model infrastructure specifications placed in clinician workflow headers.
- **Raw Feature Prefixes**: Database column names like `has_hist_201826` and `bg_normal_bmi` leaking into feature attribution text.

---

## 8. Layout, Responsive, and Component Issues

1. **Fixed Column Grids**: `st.columns(4)` and `st.columns(2)` do not collapse gracefully on tablet or split-screen displays, causing text overlap in metric cards.
2. **Inline CSS Breakage**: Custom HTML strings inside `st.markdown(..., unsafe_allow_html=True)` bypass Streamlit's theme engine and do not adapt to user theme preferences.
3. **Multiselect Badge Overflow**: When multiple conditions are selected, the multiselect widget expands vertically, pushing the rest of the form down and shifting layout anchors.
4. **Expander Nesting Limitations**: Placing Streamlit expanders below custom HTML containers creates visual fragmentation (squared corners below rounded cards).

---

## 9. Current UI Architecture & Flow Map

```
┌─────────────────────────────────────────────────────────────┐
│ [User] Selects Archetype or Enters Demographics + Diagnoses │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ [st.form] Validates PatientInput Dataclass                  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ [src.inference.predict] Single Shared Execution:            │
│  1. Construct 81-dim Feature Vector                         │
│  2. ReleaseBundle.predict_proba() [LR + RF + XGB -> Meta]   │
│  3. Isotonic Calibrator Transformation                      │
│  4. Mask Existing Chronic Conditions (Section 1.5)          │
│  5. Filter & Sort Top-N Risks vs Decision Thresholds        │
│  6. Generate SHAP & Meta-Attribution Explanations           │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ [Streamlit View] Renders:                                   │
│  - 4 Summary Metric Tiles                                   │
│  - Pre-Existing Diagnoses Badge Box                         │
│  - Top-N HTML Risk Cards + Explanation Expanders            │
│  - Complete 41-Target Dataframe Expander                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 10. Suitability Assessment for Multi-Page Professional Redesign

### Is the current codebase structurally ready for a multi-page redesign?
**Yes, structurally ready with strong separation of concerns.**

### Strengths of the Current Backend:
- **Zero Frontend Business Logic**: All feature engineering, model inference, calibration, masking, and SHAP explanations live cleanly inside `src.inference.predict` and `src.packaging.bundle`.
- **Fast Zero-Overhead Caching**: The model release bundle is already managed via `@st.cache_resource`, meaning multi-page Streamlit views can share the loaded bundle in memory with zero re-load overhead.
- **Clean Input/Output Contracts**: `PatientInput` and `PatientPredictionResult` provide strongly typed dataclasses and DataFrame export methods (`to_dataframe()`), making it straightforward to build specialized UI views.

### Architectural Recommendations for the Upcoming Redesign:
1. **Adopt Streamlit Multi-Page Navigation**:
   - **Page 1: Patient Risk Assessment (Clinician View)**: Focus strictly on clinical intake, high-risk comorbidity alert cards, risk factor breakdowns, and clinical recommendations.
   - **Page 2: Comorbidity Disease Atlas**: Interactive exploration of all 41 target conditions, population base rates, and category relationships.
   - **Page 3: Model Explainability & Consensus**: Deep-dive SHAP force plots, base model agreement (LR vs RF vs XGB), and attribution ladders.
   - **Page 4: Model Governance & Performance Audits**: Master benchmark tables, 6-arm ablation comparisons, calibration curves, and Section 5 leakage verification logs.
2. **Clinical Design System**:
   - Replace emoji-heavy headings with clean medical typography and structured card components.
   - Replace raw database column names with clean human-readable clinical concepts.
   - Separate clinical risk scores from technical debugging metrics (latency, logit weights).
