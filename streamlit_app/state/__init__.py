"""
Session state management package.
"""

from streamlit_app.state.session import (
    init_session_state,
    set_patient,
    set_result,
    get_patient,
    get_result,
    has_active_assessment,
    clear_assessment,
    set_selected_explanation,
    get_selected_explanation,
)

__all__ = [
    "init_session_state",
    "set_patient",
    "set_result",
    "get_patient",
    "get_result",
    "has_active_assessment",
    "clear_assessment",
    "set_selected_explanation",
    "get_selected_explanation",
]
