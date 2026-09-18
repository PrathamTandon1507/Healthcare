"""
Module: streamlit_app.components.condition_picker
Section 11: Structured Clinical Condition Selection Component.
"""

from typing import List, Set, Optional
import streamlit as st

from streamlit_app.disease_metadata.registry import (
    CONDITION_REGISTRY,
    CLINICAL_CATEGORIES,
    COMMON_INTAKE_SHORTCUTS,
    get_condition_info,
    search_conditions,
)
from streamlit_app.components.medical_term import format_condition_label


def render_condition_picker(
    key_prefix: str,
    title: str,
    subtitle: str,
    target_only: bool = False,
    background_only: bool = False,
    current_selection: List[int] = None
) -> List[int]:
    """
    Renders structured clinical condition picker with shortcuts, search, category filter, and removable items.
    Returns list of selected OMOP concept IDs.
    """
    state_key = f"{key_prefix}_selected_cids"
    if state_key not in st.session_state:
        st.session_state[state_key] = list(current_selection or [])
    
    # Sync with external updates (e.g. from archetype loader)
    if current_selection is not None and set(current_selection) != set(st.session_state[state_key]):
        st.session_state[state_key] = list(current_selection)

    st.markdown(f"### {title}")
    st.markdown(f'<p class="page-subtitle">{subtitle}</p>', unsafe_allow_html=True)

    # 1. Quick Shortcuts (for target chronic conditions)
    if not background_only:
        st.markdown(
            '<div style="font-size: 0.86rem; font-weight: 600; color: #334155; margin-bottom: 0.35rem;">'
            'Common Conditions (1-Click Add):</div>',
            unsafe_allow_html=True
        )
        shortcut_cols = st.columns(4)
        for idx, cid in enumerate(COMMON_INTAKE_SHORTCUTS):
            col = shortcut_cols[idx % 4]
            info = get_condition_info(cid)
            is_selected = cid in st.session_state[state_key]
            btn_label = f"{'✓ ' if is_selected else '+ '}{info.canonical_term}"
            if col.button(btn_label, key=f"{key_prefix}_sc_{cid}", use_container_width=True):
                if is_selected:
                    st.session_state[state_key].remove(cid)
                else:
                    st.session_state[state_key].append(cid)
                st.rerun()

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # 2. Search Box & Category Filter
    col_search, col_cat = st.columns([0.65, 0.35])
    with col_search:
        search_query = st.text_input(
            "Search conditions",
            placeholder="Search by diagnosis name or concept ID...",
            key=f"{key_prefix}_search"
        )
    with col_cat:
        cat_options = ["All Categories"] + [c for c in CLINICAL_CATEGORIES if not (background_only and c != "Background History")]
        selected_category = st.selectbox(
            "Filter category",
            options=cat_options,
            key=f"{key_prefix}_category"
        )

    # 3. Filter available condition candidates
    filtered = search_conditions(
        query=search_query,
        category=selected_category if selected_category != "All Categories" else None,
        target_only=target_only
    )
    if background_only:
        filtered = [c for c in filtered if c.is_background]

    available_cids = [c.concept_id for c in filtered]
    
    selected_from_dropdown = st.multiselect(
        "Select condition to add",
        options=available_cids,
        format_func=format_condition_label,
        default=[cid for cid in st.session_state[state_key] if cid in available_cids],
        key=f"{key_prefix}_multiselect",
        help="Search and select conditions."
    )
    
    # Merge dropdown selection with total state
    for cid in selected_from_dropdown:
        if cid not in st.session_state[state_key]:
            st.session_state[state_key].append(cid)

    # 4. Display Selected Conditions as Clean Removable Items
    selected_cids = st.session_state[state_key]
    st.markdown(
        f'<div style="font-size: 0.88rem; font-weight: 700; color: #1E3A8A; margin-top: 0.75rem; margin-bottom: 0.35rem;">'
        f'Selected Conditions ({len(selected_cids)}):</div>',
        unsafe_allow_html=True
    )
    
    if not selected_cids:
        st.markdown(
            '<p style="color: #94A3B8; font-size: 0.88rem; font-style: italic; margin-bottom: 0.5rem;">'
            'No conditions added yet. Use shortcuts or search above.'
            '</p>',
            unsafe_allow_html=True
        )
    else:
        chip_cols = st.columns(3)
        for idx, cid in enumerate(list(selected_cids)):
            col = chip_cols[idx % 3]
            info = get_condition_info(cid)
            c1, c2 = col.columns([0.85, 0.15])
            with c1:
                st.markdown(
                    f'<div style="background-color: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 4px; '
                    f'padding: 5px 10px; font-size: 0.84rem; font-weight: 600; color: #1E3A8A; '
                    f'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{info.canonical_term}">'
                    f'{info.canonical_term}</div>',
                    unsafe_allow_html=True
                )
            with c2:
                if st.button("✕", key=f"{key_prefix}_del_{cid}", help=f"Remove {info.canonical_term}"):
                    st.session_state[state_key].remove(cid)
                    st.rerun()

    return st.session_state[state_key]