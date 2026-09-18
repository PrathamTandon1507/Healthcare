"""
Root Entrypoint for Streamlit Application.
Redirects directly to the modularized streamlit_app application router.
"""

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit_app.app
