"""
Module: streamlit_app.app
Clinical Decision Support System for Future Comorbidity Risk Prediction.
Master application entrypoint and router execution.
"""

import os
import sys
from pathlib import Path
import streamlit as st

# Setup sys.path for workspace imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from streamlit_app.state.session import init_session_state
from streamlit_app.navigation.router import get_navigation_router

# 1. Streamlit Application Configuration
st.set_page_config(
    page_title="Comorbidity Risk Assessment",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject Calm Clinical Design System CSS
css_path = Path(__file__).resolve().parent / "styles" / "theme.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 3. Sidebar Header Branding
with st.sidebar:
    st.markdown(
        """
        <div style="padding: 0.15rem 0 0.75rem 0; border-bottom: 1px solid #E2E8F0; margin-bottom: 0.5rem;">
            <div style="font-size: 0.95rem; font-weight: 800; color: #1E3A8A; letter-spacing: 0.05em; text-transform: uppercase;">
                Comorbidity Risk
            </div>
            <div style="font-size: 0.78rem; color: #64748B; font-weight: 500;">
                Clinical Decision Support
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# 4. Initialize Shared Session State
init_session_state()

# 5. Assemble Multi-Page Router & Execute Active Page
nav = get_navigation_router()
nav.run()