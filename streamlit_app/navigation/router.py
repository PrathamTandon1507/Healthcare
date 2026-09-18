"""
Module: streamlit_app.navigation.router
Assembles multi-page navigation router with Clinical Workflow and Research tiers.
"""

from typing import Dict, List
import streamlit as st

import streamlit_app.pages.overview as page_overview
import streamlit_app.pages.patient_assessment as page_assessment
import streamlit_app.pages.risk_results as page_results
import streamlit_app.pages.explainability as page_explainability
import streamlit_app.pages.disease_explorer as page_explorer
import streamlit_app.pages.comorbidity_network as page_network
import streamlit_app.pages.model_research as page_research


# Page definitions
PAGE_OVERVIEW = st.Page(
    page_overview.render,
    title="Overview",
    url_path="overview",
    default=True
)

PAGE_ASSESSMENT = st.Page(
    page_assessment.render,
    title="Patient Assessment",
    url_path="assessment"
)

PAGE_RESULTS = st.Page(
    page_results.render,
    title="Risk Results",
    url_path="results"
)

PAGE_EXPLAINABILITY = st.Page(
    page_explainability.render,
    title="Explainability",
    url_path="explainability"
)

PAGE_EXPLORER = st.Page(
    page_explorer.render,
    title="Disease Explorer",
    url_path="explorer"
)

PAGE_NETWORK = st.Page(
    page_network.render,
    title="Comorbidity Network",
    url_path="network"
)

PAGE_RESEARCH = st.Page(
    page_research.render,
    title="Model & Research",
    url_path="research"
)


def get_navigation_router():
    """
    Returns st.navigation router object structured into:
    1. Clinical Workflow (6 primary sequential pages)
    2. Research & Governance (1 secondary model evidence page)
    """
    pages_structure = {
        "Clinical Workflow": [
            PAGE_OVERVIEW,
            PAGE_ASSESSMENT,
            PAGE_RESULTS,
            PAGE_EXPLAINABILITY,
            PAGE_EXPLORER,
            PAGE_NETWORK,
        ],
        "Research & Governance": [
            PAGE_RESEARCH,
        ]
    }
    return st.navigation(pages_structure)
