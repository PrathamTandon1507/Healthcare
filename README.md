# Clinical Comorbidity Risk Engine & Decision Support System

A clinical decision support platform designed to estimate a patient's **1-year prospective risk of developing new chronic conditions**. 

By analyzing documented patient history, demographic factors, and longitudinal EHR patterns, the system screens across **41 comorbidity targets** to flag elevated future health risks and provide interpretable clinical explanations.

---

## What the System Does

1. **Patient Risk Profiling**:
   - Takes a patient's age, biological sex, and current documented medical history.
   - Automatically excludes conditions the patient already has to prevent duplicate warnings.
   - Computes calibrated 1-year risk estimates across 41 potential chronic conditions (cardiovascular, metabolic, renal, respiratory, oncology, etc.).

2. **Actionable Clinical Alerts**:
   - Compares predicted risk against baseline population incidence to highlight clinically elevated conditions (e.g. *5.1× above baseline*).
   - Classifies findings into clinical risk tiers (*High Risk*, *Moderate Risk*, *Baseline / Low Risk*).

3. **Interpretable Risk Drivers (Explainability)**:
   - Breaks down **why** a condition was flagged.
   - Highlights key risk-increasing factors (e.g., advanced age, synergistic disease interactions like *Diabetes × Hypertension*) and protective factors.
   - Shows model consensus across diverse algorithmic perspectives.

4. **Directed Comorbidity Network**:
   - Models how diseases trigger one another longitudinally over time.
   - Evaluates statistical disease pathways (e.g., *Pre-existing Type 2 Diabetes → Incident Hypertriglyceridemia*).
   - Overlays active patient pathways directly onto the disease network to visualize disease cascade risks.

---

## Clinical Use Cases

- **Preventive Care & Early Screening**: Identify high-risk comorbidities months before clinical symptoms trigger emergency or late-stage diagnosis.
- **Multimorbidity Management**: Assess compounding risks in patients with complex chronic histories (e.g., metabolic syndrome, cardiovascular disease).
- **Clinical Decision Support**: Provide clinicians with data-driven probability estimates and documented disease trajectories to inform preventive follow-up schedules.

---

## Application Walkthrough

The platform features a multi-page interactive web interface:

- **Overview**: Clinical orientation, scope, and snapshot of the active patient session.
- **Patient Assessment**: Intake form for patient demographics, active conditions, and longitudinal history. Includes pre-loaded demonstration profiles.
- **Risk Results**: Ranked risk cards showing 1-year calibrated probability, risk tiers, relative risk multipliers, and excluded existing conditions.
- **Explainability**: In-depth inspection of clinical risk drivers, contributing factors, and model consensus for any selected condition.
- **Comorbidity Network**: Interactive exploration of disease progression pathways, comorbidity hubs, and patient-specific pathway overlays.
- **Disease Explorer**: Searchable clinical dictionary with plain-language medical definitions and OMOP / ICD-10 cross-references.
- **Model & Research**: Technical documentation on prediction horizons, calibration methods, and governance.

---

## Quickstart

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/PrathamTandon1507/Healthcare.git
cd Healthcare

# Set up virtual environment
python -m venv .venv

# Activate environment
# On Windows:
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Application

Launch the web application:
```bash
streamlit run app.py
```

Then open your browser to `http://localhost:8501`.

---

## Running Automated Tests

To run the automated verification test suite:

```bash
pytest
```

---

## Clinical Disclaimer

> **Notice**: This tool is designed strictly for research, educational, and clinical decision-support purposes. It does not provide formal medical diagnoses or replace independent clinical judgment by qualified healthcare professionals.

---

## License

This project is licensed under the MIT License.
