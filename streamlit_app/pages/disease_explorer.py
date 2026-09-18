"""
Module: streamlit_app.pages.disease_explorer
Page 5: Disease Explorer — Clean Clinical Comorbidity Reference Atlas.
"""

import streamlit as st

from streamlit_app.components.page_header import render_page_header
from streamlit_app.disease_metadata.registry import (
    CLINICAL_CATEGORIES,
    search_conditions,
    ConditionInfo
)


def render():
    render_page_header(
        title="Disease Explorer",
        subtitle="Explore the conditions supported by the comorbidity risk prediction model."
    )

    # Search & Category Filter Bar
    col_search, col_cat, col_role = st.columns([0.45, 0.35, 0.20])
    with col_search:
        search_query = st.text_input(
            "Search conditions",
            placeholder="Search by condition name, concept ID, ICD-10...",
            key="atlas_search"
        )
    with col_cat:
        cat_choices = ["All Categories"] + CLINICAL_CATEGORIES
        selected_category = st.selectbox(
            "Filter category",
            options=cat_choices,
            key="atlas_cat"
        )
    with col_role:
        role_choice = st.selectbox(
            "Filter type",
            options=["All Conditions", "Incident Targets Only", "Background Factors Only"],
            key="atlas_role"
        )

    # Filter Results
    target_only = (role_choice == "Incident Targets Only")
    cat_filter = None if selected_category == "All Categories" else selected_category
    results = search_conditions(query=search_query, category=cat_filter, target_only=target_only)
    
    if role_choice == "Background Factors Only":
        results = [c for c in results if c.is_background]

    st.markdown(f"**Showing {len(results)} Conditions**")
    st.markdown("<hr />", unsafe_allow_html=True)

    # Clean List Layout (Section 21: Whitespace rather than giant cards)
    if not results:
        st.info("No matching clinical conditions found. Please broaden your search criteria.")
        return

    for info in results:
        with st.container():
            role_label = "Incident prediction target" if info.is_target else "Background history feature"
            role_color = "#1E40AF" if info.is_target else "#64748B"
            role_bg = "#EFF6FF" if info.is_target else "#F8FAFC"
            role_border = "#BFDBFE" if info.is_target else "#CBD5E1"
            
            hint_str = f" &bull; ICD-10: {info.icd10_hint}" if info.icd10_hint else ""

            st.markdown(
                f"""
                <div style="padding: 0.85rem 0; border-bottom: 1px solid #F1F5F9;">
                    <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.25rem;">
                        <div>
                            <span style="font-size: 1.05rem; font-weight: 700; color: #0F172A;">{info.canonical_term}</span>
                            <span style="font-size: 0.80rem; color: #64748B; margin-left: 8px;">OMOP: {info.concept_id}{hint_str}</span>
                        </div>
                        <div>
                            <span style="background-color: {role_bg}; color: {role_color}; border: 1px solid {role_border}; 
                                         padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">
                                {role_label}
                            </span>
                        </div>
                    </div>
                    <div style="font-size: 0.90rem; color: #334155; line-height: 1.45;">
                        {info.plain_language_explanation}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


if __name__ == "__main__":
    render()