import os
import json
import streamlit as st

from streamlit_app.components.page_header import render_page_header
from streamlit_app.disease_metadata.registry import (
    CLINICAL_CATEGORIES,
    search_conditions,
    ConditionInfo
)


# Load frozen graph
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GRAPH_PATH_V2 = os.path.join(ROOT_DIR, "models", "release_v2", "disease_graph.json")
GRAPH_PATH_V1 = os.path.join(ROOT_DIR, "data", "graph", "disease_graph_v1.json")


@st.cache_data
def load_graph_data():
    path = GRAPH_PATH_V2 if os.path.exists(GRAPH_PATH_V2) else GRAPH_PATH_V1
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def render():
    render_page_header(
        title="Disease Explorer",
        subtitle="Explore the conditions supported by the comorbidity risk prediction model and their network relationships."
    )

    graph_data = load_graph_data()
    nodes_graph = graph_data.get("nodes", {}) if graph_data else {}
    edges_graph = graph_data.get("edges", []) if graph_data else []

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

            cid_str = str(info.concept_id)
            node_meta = nodes_graph.get(cid_str, {})
            out_deg = node_meta.get("out_degree_centrality", 0.0)
            in_deg = node_meta.get("in_degree_centrality", 0.0)

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
                    <div style="font-size: 0.90rem; color: #334155; line-height: 1.45; margin-bottom: 0.35rem;">
                        {info.plain_language_explanation}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Show network connections if it's a target node in the graph
            if info.is_target and node_meta:
                with st.expander(f"Network Associations & Centrality for {info.canonical_term}"):
                    net_c1, net_c2 = st.columns(2)
                    with net_c1:
                        st.caption(f"**Network In-Degree**: `{in_deg:.3f}` | **Out-Degree**: `{out_deg:.3f}`")
                        # Top upstream drivers (incoming edges)
                        incoming = [e for e in edges_graph if int(e["target_id"]) == info.concept_id and e.get("is_significant")]
                        incoming.sort(key=lambda x: x.get("relative_risk", 1.0), reverse=True)
                        if incoming:
                            st.markdown("**Top Preceding Risk Drivers:**")
                            for inc in incoming[:4]:
                                st.markdown(f"- {inc['source_name']}: **{inc['relative_risk']:.2f}×** relative risk")
                        else:
                            st.caption("No significant upstream drivers in graph.")

                    with net_c2:
                        # Top downstream complications (outgoing edges)
                        outgoing = [e for e in edges_graph if int(e["source_id"]) == info.concept_id and e.get("is_significant")]
                        outgoing.sort(key=lambda x: x.get("relative_risk", 1.0), reverse=True)
                        if outgoing:
                            st.markdown("**Top Downstream Complications:**")
                            for out in outgoing[:4]:
                                st.markdown(f"- {out['target_name']}: **{out['relative_risk']:.2f}×** relative risk")
                        else:
                            st.caption("No significant downstream associations in graph.")


if __name__ == "__main__":
    render()