"""
Module: streamlit_app.pages.overview
Page 1: Overview — Clinical Orientation and Session Snapshot.
"""

import streamlit as st
from streamlit_app.components.page_header import render_page_header
from streamlit_app.state.session import get_patient, get_result


def render():
    render_page_header(
        title="Comorbidity Risk Overview",
        subtitle="Clinical decision-support system estimating the 1-year risk of developing new chronic conditions."
    )

    # Clinical Scope Notice
    st.markdown(
        """
        <div class="clinical-summary-box">
            <div style="font-weight: 700; font-size: 1.05rem; color: #1E3A8A; margin-bottom: 0.35rem;">
                Clinical Decision Support Scope
            </div>
            <p style="color: #334155; font-size: 0.92rem; line-height: 1.55; margin-bottom: 0.5rem;">
                This system estimates the 1-year calibrated probability of onset across <strong>41 target chronic conditions</strong> 
                by evaluating patient demographics, documented active diagnoses, and longitudinal EHR patterns.
            </p>
            <p class="clinical-disclaimer">
                <strong>Clinical Note:</strong> Predictions represent empirical statistical estimates derived from longitudinal electronic health records. 
                This tool is designed to assist clinical vigilance and preventive screening, not to replace clinical diagnostic judgment.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Active Session Snapshot (if assessment exists)
    patient = get_patient()
    result = get_result()

    if patient is not None and result is not None:
        st.markdown("### Active Patient Session")
        with st.container():
            st.markdown(
                """
                <div style="background-color: #FFFFFF; border: 1px solid #BFDBFE; border-left: 4px solid #2563EB; border-radius: 6px; padding: 1.25rem; margin-bottom: 1.5rem;">
                """,
                unsafe_allow_html=True
            )
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                gender_str = "Male" if str(patient.gender).lower() in ["m", "male", "8507"] else "Female"
                st.metric("Demographics", f"{int(patient.age)} yrs, {gender_str}")
            with c2:
                st.metric("Diagnosed Conditions", f"{len(patient.current_condition_ids)}")
            with c3:
                n_elevated = len([p for p in result.top_ranked_predictions if p.is_flagged_elevated_risk])
                st.metric("Elevated Risks", f"{n_elevated} flagged")
            with c4:
                st.metric("Conditions Evaluated", "41 targets")

            col_a, col_b = st.columns([0.5, 0.5])
            with col_a:
                if st.button("Resume Active Results →", type="primary", use_container_width=True):
                    from streamlit_app.navigation.router import get_pages
                    st.switch_page(get_pages()["results"])
            with col_b:
                if st.button("Start New Assessment", use_container_width=True):
                    from streamlit_app.navigation.router import get_pages
                    st.switch_page(get_pages()["assessment"])

            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            '<p style="color: #475569; font-size: 0.95rem; margin-bottom: 1.25rem;">'
            'Enter patient demographics and documented diagnoses to compute 1-year incident comorbidity risks.'
            '</p>',
            unsafe_allow_html=True
        )
        if st.button("Start Patient Assessment →", type="primary"):
            from streamlit_app.navigation.router import get_pages
            st.switch_page(get_pages()["assessment"])


    st.markdown("<hr />", unsafe_allow_html=True)

    # Workflow Steps
    st.markdown("### Clinical Workflow")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
            <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-top: 3px solid #1E3A8A; border-radius: 6px; padding: 1.15rem; height: 100%;">
                <div style="font-weight: 700; color: #1E3A8A; font-size: 0.95rem; margin-bottom: 0.25rem;">1. Patient Assessment</div>
                <p style="color: #475569; font-size: 0.88rem; line-height: 1.45; margin-bottom: 0;">
                    Enter demographics, active chronic diagnoses, and background clinical history.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            """
            <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-top: 3px solid #2563EB; border-radius: 6px; padding: 1.15rem; height: 100%;">
                <div style="font-weight: 700; color: #2563EB; font-size: 0.95rem; margin-bottom: 0.25rem;">2. Risk Results</div>
                <p style="color: #475569; font-size: 0.88rem; line-height: 1.45; margin-bottom: 0;">
                    Review ranked 1-year calibrated incident probabilities with population baseline comparisons.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            """
            <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-top: 3px solid #0F172A; border-radius: 6px; padding: 1.15rem; height: 100%;">
                <div style="font-weight: 700; color: #0F172A; font-size: 0.95rem; margin-bottom: 0.25rem;">3. Explainability</div>
                <p style="color: #475569; font-size: 0.88rem; line-height: 1.45; margin-bottom: 0;">
                    Understand clinical contributing factors and multi-model consensus for each condition.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )


if __name__ == "__main__":
    render()