"""
Module: streamlit_app.pages.comorbidity_network
Page 6: Comorbidity Network — Honest Reserved Placeholder Module.
"""

import streamlit as st

from streamlit_app.components.page_header import render_page_header
from streamlit_app.state.session import has_active_assessment


def render():
    render_page_header(
        title="Comorbidity Network",
        subtitle="Network-based disease relationship analysis will be available here in a future release."
    )

    # Clean Honest Placeholder (Section 22)
    st.markdown(
        """
        <div style="background-color: #FFFFFF; border: 1px dashed #CBD5E1; border-radius: 8px; 
                    padding: 3rem 2rem; text-align: center; margin: 1.5rem 0;">
            <div style="font-size: 1.15rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.75rem;">
                Comorbidity Network Analysis
            </div>
            <p style="color: #475569; max-width: 580px; margin: 0 auto 1.5rem auto; line-height: 1.5; font-size: 0.92rem;">
                Network-based disease relationship analysis and graph-based co-occurrence visualization 
                will be available here in a future release.
            </p>
            <p style="color: #64748B; font-size: 0.86rem; margin-bottom: 0;">
                The current ML-based risk assessment workflow is fully operational and usable without the network module.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if has_active_assessment():
            if st.button("Return to Risk Results", type="primary", use_container_width=True):
                from streamlit_app.navigation.router import PAGE_RESULTS
                st.switch_page(PAGE_RESULTS)
        else:
            if st.button("Start Patient Assessment", type="primary", use_container_width=True):
                from streamlit_app.navigation.router import PAGE_ASSESSMENT
                st.switch_page(PAGE_ASSESSMENT)


if __name__ == "__main__":
    render()