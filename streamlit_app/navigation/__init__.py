"""
Navigation router package.
"""

from streamlit_app.navigation.router import (
    get_navigation_router,
    PAGE_OVERVIEW,
    PAGE_ASSESSMENT,
    PAGE_RESULTS,
    PAGE_EXPLAINABILITY,
    PAGE_EXPLORER,
    PAGE_NETWORK,
    PAGE_RESEARCH,
)

__all__ = [
    "get_navigation_router",
    "PAGE_OVERVIEW",
    "PAGE_ASSESSMENT",
    "PAGE_RESULTS",
    "PAGE_EXPLAINABILITY",
    "PAGE_EXPLORER",
    "PAGE_NETWORK",
    "PAGE_RESEARCH",
]
