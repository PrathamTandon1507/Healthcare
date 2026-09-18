"""
Disease metadata package.
Provides canonical clinical terms, plain-language translations, category groupings,
and search capabilities for all 41 target conditions and 17 background conditions.
"""

from streamlit_app.disease_metadata.registry import (
    ConditionInfo,
    CONDITION_REGISTRY,
    CLINICAL_CATEGORIES,
    COMMON_INTAKE_SHORTCUTS,
    get_condition_info,
    search_conditions,
)

__all__ = [
    "ConditionInfo",
    "CONDITION_REGISTRY",
    "CLINICAL_CATEGORIES",
    "COMMON_INTAKE_SHORTCUTS",
    "get_condition_info",
    "search_conditions",
]
