"""
Module: streamlit_app.state.session
Session state management and accessors for multi-page clinical workflow.
"""

from datetime import datetime
from typing import Optional
import streamlit as st

from src.inference.predict import PatientInput, PatientPredictionResult


def init_session_state() -> None:
    """Initializes default keys in st.session_state if not present."""
    if "current_patient" not in st.session_state:
        st.session_state["current_patient"] = None
    if "current_result" not in st.session_state:
        st.session_state["current_result"] = None
    if "current_archetype_name" not in st.session_state:
        st.session_state["current_archetype_name"] = None
    if "selected_explanation_cid" not in st.session_state:
        st.session_state["selected_explanation_cid"] = None
    if "threshold_strategy" not in st.session_state:
        st.session_state["threshold_strategy"] = "f1_optimal"
    if "top_n" not in st.session_state:
        st.session_state["top_n"] = 5
    if "assessment_timestamp" not in st.session_state:
        st.session_state["assessment_timestamp"] = None


def set_patient(patient: PatientInput, archetype_name: Optional[str] = None) -> None:
    """Sets current patient input in session state."""
    st.session_state["current_patient"] = patient
    st.session_state["current_archetype_name"] = archetype_name


def set_result(result: PatientPredictionResult) -> None:
    """Sets current prediction result and records assessment timestamp."""
    st.session_state["current_result"] = result
    st.session_state["assessment_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_patient() -> Optional[PatientInput]:
    """Returns the current patient input or None."""
    return st.session_state.get("current_patient", None)


def get_result() -> Optional[PatientPredictionResult]:
    """Returns the active prediction result or None."""
    return st.session_state.get("current_result", None)


def has_active_assessment() -> bool:
    """Returns True if an assessment result is available in session."""
    return st.session_state.get("current_result") is not None


def clear_assessment() -> None:
    """Clears current patient and result from session state."""
    st.session_state["current_patient"] = None
    st.session_state["current_result"] = None
    st.session_state["current_archetype_name"] = None
    st.session_state["selected_explanation_cid"] = None
    st.session_state["assessment_timestamp"] = None


def set_selected_explanation(cid: int) -> None:
    """Sets the target concept ID to view on Explainability page."""
    st.session_state["selected_explanation_cid"] = cid


def get_selected_explanation() -> Optional[int]:
    """Gets the currently selected concept ID for explainability."""
    return st.session_state.get("selected_explanation_cid", None)
