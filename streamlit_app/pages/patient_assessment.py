"""
Module: streamlit_app.pages.patient_assessment
Page 2: Patient Assessment — Structured Clinical Intake & Inference Trigger.
"""

from typing import List, Dict, Any
import streamlit as st

from src.inference.predict import (
    PatientInput,
    predict_patient_comorbidity_risk,
    ReleaseBundle,
    load_release_bundle,
)
from streamlit_app.components.page_header import render_page_header
from streamlit_app.components.condition_picker import render_condition_picker
from streamlit_app.state.session import set_patient, set_result, get_patient


# Predefined Clinical Patient Profiles
CLINICAL_ARCHETYPES: Dict[str, Dict[str, Any]] = {
    "Select an example patient profile (optional)...": None,
    "Elderly Diabetic & Hypertensive (High CVD / CKD Risk)": {
        "age": 68,
        "gender": "Male",
        "race": "white",
        "ethnicity": "non_hispanic",
        "conditions": [201826, 316866, 432867],  # Type 2 Diabetes, HTN, Hyperlipidemia
        "bg_conditions": [4311629],               # Prediabetes history
        "prior_obs_years": 6.5
    },
    "Cardiovascular & Heart Failure Patient": {
        "age": 74,
        "gender": "Male",
        "race": "black",
        "ethnicity": "non_hispanic",
        "conditions": [192279, 317576, 316866, 4120314],  # CHF, CAD, HTN, Hypertriglyceridemia
        "bg_conditions": [],
        "prior_obs_years": 8.0
    },
    "Metabolic Syndrome & Prediabetes (Middle-Aged Female)": {
        "age": 52,
        "gender": "Female",
        "race": "white",
        "ethnicity": "non_hispanic",
        "conditions": [4311629, 316866, 436940],  # Prediabetes, HTN, Metabolic Syndrome
        "bg_conditions": [],
        "prior_obs_years": 4.0
    },
    "Young Adult with Chronic Respiratory History": {
        "age": 29,
        "gender": "Female",
        "race": "asian",
        "ethnicity": "non_hispanic",
        "conditions": [4051466, 257012, 133834],  # Asthma, Chronic Sinusitis, Eczema
        "bg_conditions": [],
        "prior_obs_years": 5.0
    },
    "Young Healthy Adult (Baseline Floor)": {
        "age": 24,
        "gender": "Male",
        "race": "white",
        "ethnicity": "non_hispanic",
        "conditions": [],
        "bg_conditions": [4112343],  # Normal BMI
        "prior_obs_years": 2.0
    }
}


@st.cache_resource(show_spinner=False)
def get_cached_release_bundle() -> ReleaseBundle:
    """Loads and caches the release bundle."""
    bundle = load_release_bundle()
    if not bundle.is_loaded:
        bundle.load()
    return bundle


def render():
    render_page_header(
        title="Patient Assessment",
        subtitle="Enter the patient's demographic and documented clinical history to estimate the risk of developing new comorbidities over the next year."
    )

    st.markdown(
        '<p class="clinical-disclaimer" style="margin-top: -1rem; margin-bottom: 1.25rem;">'
        'This tool provides model-based decision support and does not constitute a diagnosis.'
        '</p>',
        unsafe_allow_html=True
    )

    # Example Patient Loader (Secondary)
    with st.expander("Try an example patient (optional demonstration profiles)", expanded=False):
        st.markdown(
            '<p style="color: #64748B; font-size: 0.88rem; margin-bottom: 0.5rem;">'
            'Use a predefined clinical profile to explore the assessment workflow.'
            '</p>',
            unsafe_allow_html=True
        )
        col_arch, col_arch_btn = st.columns([0.75, 0.25])
        with col_arch:
            arch_choice = st.selectbox(
                "Select profile",
                options=list(CLINICAL_ARCHETYPES.keys()),
                label_visibility="collapsed",
                key="archetype_select"
            )
        with col_arch_btn:
            if st.button("Load Profile", use_container_width=True, disabled=(arch_choice == "Select an example patient profile (optional)...")):
                arch_data = CLINICAL_ARCHETYPES[arch_choice]
                if arch_data:
                    st.session_state["form_age"] = arch_data["age"]
                    st.session_state["form_gender"] = arch_data["gender"]
                    st.session_state["form_race"] = arch_data["race"]
                    st.session_state["form_ethnicity"] = arch_data["ethnicity"]
                    st.session_state["form_obs_years"] = arch_data["prior_obs_years"]
                    st.session_state["intake_chronic_selected_cids"] = list(arch_data["conditions"])
                    st.session_state["intake_bg_selected_cids"] = list(arch_data["bg_conditions"])
                    st.session_state["current_archetype_name"] = arch_choice
                    st.rerun()

    st.markdown("<hr />", unsafe_allow_html=True)

    # 1. Patient Demographics (Controlled 2-column grid)
    st.markdown("### Patient Demographics")
    st.markdown(
        '<p class="page-subtitle">Basic demographic information used by the risk calibration model.</p>',
        unsafe_allow_html=True
    )

    # Row 1: Age & Sex
    c_age, c_sex = st.columns(2)
    with c_age:
        age_val = st.number_input(
            "Age (Years)",
            min_value=0,
            max_value=120,
            value=st.session_state.get("form_age", 58),
            step=1,
            help="Patient age in completed years.",
            key="form_age"
        )
    with c_sex:
        gender_val = st.selectbox(
            "Biological Sex",
            options=["Male", "Female"],
            index=0 if st.session_state.get("form_gender", "Male") == "Male" else 1,
            help="Biological sex at birth.",
            key="form_gender"
        )

    # Row 2: Race & Ethnicity
    c_race, c_eth = st.columns(2)
    with c_race:
        race_options = ["white", "black", "asian", "other"]
        cur_race = st.session_state.get("form_race", "white").lower()
        race_val = st.selectbox(
            "Race",
            options=race_options,
            format_func=lambda r: r.capitalize(),
            index=race_options.index(cur_race) if cur_race in race_options else 0,
            key="form_race"
        )
    with c_eth:
        eth_options = ["non_hispanic", "hispanic"]
        cur_eth = st.session_state.get("form_ethnicity", "non_hispanic").lower()
        eth_val = st.selectbox(
            "Ethnicity",
            options=eth_options,
            format_func=lambda e: "Non-Hispanic" if "non" in e else "Hispanic",
            index=eth_options.index(cur_eth) if cur_eth in eth_options else 0,
            key="form_ethnicity"
        )

    st.markdown("<hr />", unsafe_allow_html=True)

    # 2. Existing Documented Conditions
    chronic_cids = render_condition_picker(
        key_prefix="intake_chronic",
        title="Existing Chronic Conditions",
        subtitle="Conditions already documented for this patient. These conditions are excluded from new incident-risk predictions.",
        target_only=True
    )

    st.markdown("<hr />", unsafe_allow_html=True)

    # 3. Relevant Medical History (Background factors)
    bg_cids = render_condition_picker(
        key_prefix="intake_bg",
        title="Relevant Medical History",
        subtitle="Additional clinical history that may inform the risk model but is not itself a prediction target.",
        background_only=True
    )

    st.markdown("<hr />", unsafe_allow_html=True)

    # 4. Observation Span & Decision Settings
    st.markdown("### Longitudinal History & Parameters")
    c_obs, c_strat, c_topn = st.columns([0.35, 0.40, 0.25])
    with c_obs:
        obs_years = st.number_input(
            "EHR History Span (Years)",
            min_value=0.5,
            max_value=25.0,
            value=float(st.session_state.get("form_obs_years", 3.0)),
            step=0.5,
            help="Length of prior electronic health record history available.",
            key="form_obs_years"
        )
    with c_strat:
        strat_options = {
            "f1_optimal": "F1-Optimal (Balanced Sensitivity/Specificity)",
            "recall_80_threshold": "High Sensitivity (80% Recall Target)",
            "prevalence_matched_threshold": "Prevalence-Matched (High Specificity)"
        }
        selected_strategy = st.selectbox(
            "Threshold Operating Strategy",
            options=list(strat_options.keys()),
            format_func=lambda k: strat_options[k],
            index=0,
            key="form_thresh_strat"
        )
    with c_topn:
        top_n_val = st.selectbox(
            "Primary Targets to Display",
            options=[3, 5, 10, 15, 41],
            index=1,
            key="form_top_n"
        )

    # 5. Primary Completion CTA (Section 14)
    st.markdown(
        """
        <div class="assessment-cta-container">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                <div>
                    <div style="font-size: 1.05rem; font-weight: 700; color: #1E3A8A; margin-bottom: 2px;">
                        Ready to assess this patient?
                    </div>
                    <div style="font-size: 0.88rem; color: #475569;">
                        The model will evaluate 41 potential comorbidities and identify conditions with elevated predicted 1-year risk.
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    col_cta_l, col_cta_r = st.columns([0.65, 0.35])
    with col_cta_r:
        if st.button("Run assessment →", type="primary", use_container_width=True):
            with st.spinner("Calculating calibrated comorbidity risk across 41 targets..."):
                all_input_cids = list(set(chronic_cids + bg_cids))
                patient_input = PatientInput(
                    age=float(age_val),
                    gender=gender_val,
                    race=race_val,
                    ethnicity=eth_val,
                    current_condition_ids=all_input_cids,
                    prior_obs_years=float(obs_years)
                )
                
                bundle = get_cached_release_bundle()
                result = predict_patient_comorbidity_risk(
                    patient_input=patient_input,
                    bundle=bundle,
                    top_n=top_n_val,
                    threshold_strategy=selected_strategy,
                    include_explanations=True,
                    mask_existing_conditions=True
                )
                
                set_patient(patient_input, archetype_name=st.session_state.get("current_archetype_name"))
                set_result(result)
                st.session_state["threshold_strategy"] = selected_strategy
                st.session_state["top_n"] = top_n_val
                
                from streamlit_app.navigation.router import PAGE_RESULTS
                st.switch_page(PAGE_RESULTS)


if __name__ == "__main__":
    render()