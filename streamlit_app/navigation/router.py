"""
Module: streamlit_app.navigation.router
Assembles multi-page navigation router with Clinical Workflow and Research tiers.

IMPORTANT: st.Page objects MUST be created inside the Streamlit ScriptRunContext
(i.e., during a live rerun, not at module import time). Creating them at import
time causes st.Page.__init__ to return early with no-op, leaving _url_path,
_script_hash etc. unset, which breaks st.switch_page with AttributeError.

All page objects are created lazily inside get_navigation_router() and cached
in st.session_state["_nav_pages"] so they remain stable across reruns.
Use get_pages() to retrieve the current session's page objects for switch_page.
"""

import streamlit as st

import streamlit_app.pages.overview as page_overview
import streamlit_app.pages.patient_assessment as page_assessment
import streamlit_app.pages.risk_results as page_results
import streamlit_app.pages.explainability as page_explainability
import streamlit_app.pages.disease_explorer as page_explorer
import streamlit_app.pages.comorbidity_network as page_network
import streamlit_app.pages.model_research as page_research


def _build_pages() -> dict:
    """Build all st.Page objects within an active ScriptRunContext."""
    return {
        "overview": st.Page(
            page_overview.render,
            title="Overview",
            url_path="overview",
            default=True,
        ),
        "assessment": st.Page(
            page_assessment.render,
            title="Patient Assessment",
            url_path="assessment",
        ),
        "results": st.Page(
            page_results.render,
            title="Risk Results",
            url_path="results",
        ),
        "explainability": st.Page(
            page_explainability.render,
            title="Explainability",
            url_path="explainability",
        ),
        "explorer": st.Page(
            page_explorer.render,
            title="Disease Explorer",
            url_path="explorer",
        ),
        "network": st.Page(
            page_network.render,
            title="Comorbidity Network",
            url_path="network",
        ),
        "research": st.Page(
            page_research.render,
            title="Model & Research",
            url_path="research",
        ),
    }


def get_pages() -> dict:
    """
    Returns the dict of page objects for this session.
    Pages are created once per session and stored in session_state.
    Call this inside any page that needs to st.switch_page().
    """
    if "_nav_pages" not in st.session_state:
        st.session_state["_nav_pages"] = _build_pages()
    return st.session_state["_nav_pages"]


def get_navigation_router():
    """
    Builds and returns st.navigation() router structured into:
    1. Clinical Workflow (6 primary sequential pages)
    2. Research & Governance (1 secondary model evidence page)
    """
    pages = _build_pages()
    # Cache for use by switch_page calls within this session
    st.session_state["_nav_pages"] = pages

    pages_structure = {
        "Clinical Workflow": [
            pages["overview"],
            pages["assessment"],
            pages["results"],
            pages["explainability"],
            pages["explorer"],
            pages["network"],
        ],
        "Research & Governance": [
            pages["research"],
        ],
    }
    return st.navigation(pages_structure)
