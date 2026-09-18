"""
Module: streamlit_app.components.medical_term
Section 6.5 Reusable Medical Term + Plain-Language Component.
"""

from typing import Optional
import streamlit as st

from streamlit_app.disease_metadata.registry import get_condition_info, ConditionInfo


def render_medical_term(
    concept_id: int,
    show_plain_language: bool = True,
    show_code: bool = True,
    show_category: bool = False
) -> None:
    """
    Renders canonical medical term with plain-language explanation and optional metadata.
    Preserves exact clinical terminology while providing immediate accessible context.
    """
    info: ConditionInfo = get_condition_info(concept_id)
    
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.markdown(
            f'<div class="medical-term-title">{info.canonical_term}</div>',
            unsafe_allow_html=True
        )
        if show_plain_language:
            st.markdown(
                f'<div class="medical-term-plain">{info.plain_language_explanation}</div>',
                unsafe_allow_html=True
            )
    with col2:
        meta_html = []
        if show_code:
            hint = f" ({info.icd10_hint})" if info.icd10_hint else ""
            meta_html.append(f'<div class="medical-term-code">OMOP: {concept_id}{hint}</div>')
        if show_category:
            meta_html.append(f'<span class="status-chip">{info.category}</span>')
        if meta_html:
            st.markdown("".join(meta_html), unsafe_allow_html=True)


def format_condition_label(concept_id: int) -> str:
    """Returns canonical formatted string for dropdowns or list items."""
    info = get_condition_info(concept_id)
    hint = f" [{info.icd10_hint}]" if info.icd10_hint else ""
    return f"{info.canonical_term}{hint} (OMOP {concept_id})"
