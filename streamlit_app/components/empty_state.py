"""
Module: streamlit_app.components.empty_state
Clean, non-technical empty state with direct clinical call-to-action.
"""

import streamlit as st


def render_empty_assessment_state(
    title: str = "No Assessment Active",
    message: str = "To view predicted comorbidity risks or explainability factors, please start by completing a patient assessment.",
    button_label: str = "Go to Patient Assessment"
) -> None:
    """Renders a friendly, calm empty state with a direct CTA button."""
    st.markdown(
        f"""
        <div style="background-color: #FFFFFF; border: 1px dashed #CBD5E1; border-radius: 8px; 
                    padding: 2.5rem 1.5rem; text-align: center; margin: 1.5rem 0;">
            <h3 style="color: #0F172A; margin-bottom: 0.5rem;">{title}</h3>
            <p style="color: #64748B; max-width: 500px; margin: 0 auto 1.5rem auto; line-height: 1.5;">
                {message}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button(button_label, type="primary", use_container_width=True):
            from streamlit_app.navigation.router import get_pages
            st.switch_page(get_pages()["assessment"])

