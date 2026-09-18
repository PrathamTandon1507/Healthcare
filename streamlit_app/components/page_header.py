"""
Module: streamlit_app.components.page_header
Standardized clinical page header with title, subtitle, and active session context.
"""

from typing import Optional
import streamlit as st
from streamlit_app.state.session import get_patient, get_result


def render_page_header(
    title: str,
    subtitle: Optional[str] = None,
    show_session_banner: bool = False
) -> None:
    """Renders accessible, consistent page header with optional active assessment context."""
    st.title(title)
    if subtitle:
        st.markdown(
            f'<p style="color: #475569; font-size: 1.0rem; margin-top: -0.25rem; margin-bottom: 1.25rem;">'
            f'{subtitle}</p>',
            unsafe_allow_html=True
        )
    
    if show_session_banner:
        patient = get_patient()
        result = get_result()
        if patient is not None:
            cond_count = len(patient.current_condition_ids)
            archetype = st.session_state.get("current_archetype_name")
            archetype_tag = f" | Preset: {archetype}" if archetype else ""
            
            gender_str = "Male" if str(patient.gender).lower() in ["m", "male", "8507"] else "Female"
            summary_text = (
                f"**Active Patient**: Age {int(patient.age)}, {gender_str} | "
                f"{cond_count} Chronic Conditions Documented{archetype_tag}"
            )
            if result:
                n_elevated = len([p for p in result.top_ranked_predictions if p.is_flagged_elevated_risk])
                summary_text += f" | **{n_elevated} conditions flagged elevated**"
            
            st.info(summary_text)
