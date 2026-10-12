"""
Module: streamlit_app.pages.comorbidity_network
Page 5: Comorbidity Disease Network Explorer.

Interactive clinical disease-comorbidity graph visualizer powered by the frozen
directed temporal relative risk graph (41 target conditions, FDR q < 0.05).
"""

import os
import json
import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

from streamlit_app.components.page_header import render_page_header
from streamlit_app.state.session import has_active_assessment, get_patient, get_result
from streamlit_app.disease_metadata.registry import get_condition_info, CLINICAL_CATEGORIES



# Path to frozen graph
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GRAPH_PATH_V2 = os.path.join(ROOT_DIR, "models", "release_v2", "disease_graph.json")
GRAPH_PATH_V1 = os.path.join(ROOT_DIR, "data", "graph", "disease_graph_v1.json")


@st.cache_data
def load_disease_graph() -> Optional[Dict[str, Any]]:
    path = GRAPH_PATH_V2 if os.path.exists(GRAPH_PATH_V2) else GRAPH_PATH_V1
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def render():
    render_page_header(
        title="Comorbidity Disease Network",
        subtitle="Interpretable directed temporal graph of disease-disease associations and incident comorbidity pathways."
    )
    
    graph_data = load_disease_graph()
    if graph_data is None:
        st.warning("Disease comorbidity graph artifact not found. Please run the graph builder script.")
        return
        
    nodes = graph_data.get("nodes", {})
    edges = graph_data.get("edges", [])
    graph_stats = graph_data.get("graph_statistics", {})
    
    # -------------------------------------------------------------------------
    # 1. Summary KPI Metrics
    # -------------------------------------------------------------------------
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Graph Nodes", value=f"{graph_stats.get('node_count', len(nodes))} Targets")
    with col2:
        st.metric(label="Significant Edges", value=f"{graph_stats.get('significant_edges', 0)}")
    with col3:
        st.metric(label="Edge Metric", value="Relative Risk (RR)")
    with col4:
        st.metric(label="Leakage Boundary", value="Train-Split Only")
        
    # -------------------------------------------------------------------------
    # 2. Patient Overlay Banner (if assessment is active)
    # -------------------------------------------------------------------------
    patient = get_patient() if has_active_assessment() else None
    result = get_result() if has_active_assessment() else None
    
    if patient and result:
        existing_cids = set(getattr(patient, "current_condition_ids", getattr(patient, "conditions", [])))
        high_risk_cids = set(getattr(result, "high_risk_conditions", [p.concept_id for p in getattr(result, "top_ranked_predictions", []) if getattr(p, "is_flagged_elevated_risk", False)]))
        
        # Build patient's active disease pathways from graph
        patient_pathways = []
        for e in edges:
            s_id = int(e["source_id"])
            t_id = int(e["target_id"])
            if s_id in existing_cids and t_id in high_risk_cids:
                patient_pathways.append(e)
        patient_pathways.sort(key=lambda x: x.get("relative_risk", 1.0), reverse=True)

        with st.container():
            st.markdown(
                """
                <div style="background-color: #FFFFFF; border: 1px solid #BFDBFE; border-left: 5px solid #2563EB; border-radius: 8px; padding: 1.25rem 1.4rem; margin-bottom: 1.25rem; box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);">
                    <div style="font-size: 1.05rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.5rem;">
                        Active Patient Network Overlay
                    </div>
                    <div style="display: flex; flex-wrap: wrap; gap: 0.65rem; margin-bottom: 0.85rem;">
                """,
                unsafe_allow_html=True
            )
            
            c_overlay1, c_overlay2 = st.columns(2)
            with c_overlay1:
                st.markdown("**Diagnosed Conditions (Source Nodes):**")
                chips_html = "".join([
                    f'<span style="display: inline-block; background-color: #EFF6FF; border: 1px solid #93C5FD; color: #1E40AF; padding: 3px 10px; border-radius: 4px; font-size: 0.84rem; font-weight: 600; margin: 2px 4px 4px 0;">'
                    f'● {get_condition_info(cid).canonical_term}</span>'
                    for cid in existing_cids
                ])
                st.markdown(chips_html, unsafe_allow_html=True)

            with c_overlay2:
                st.markdown("**Elevated Incident Risks (Target Nodes):**")
                if high_risk_cids:
                    chips_risk = "".join([
                        f'<span style="display: inline-block; background-color: #FEF2F2; border: 1px solid #FCA5A5; color: #991B1B; padding: 3px 10px; border-radius: 4px; font-size: 0.84rem; font-weight: 700; margin: 2px 4px 4px 0;">'
                        f'▲ {get_condition_info(cid).canonical_term}</span>'
                        for cid in high_risk_cids
                    ])
                    st.markdown(chips_risk, unsafe_allow_html=True)
                else:
                    st.caption("No comorbidity endpoints flagged above the decision threshold.")

            if patient_pathways:
                st.markdown("<hr style='margin: 0.75rem 0;' />", unsafe_allow_html=True)
                st.markdown(f"**Identified Active Longitudinal Pathways ({len(patient_pathways)} validated pathways):**")
                for pw in patient_pathways:
                    fdr_val = float(pw.get("fdr_q_value", 0.0))
                    raw_p = float(pw.get("raw_p_value", 0.0))
                    if fdr_val > 0.0:
                        q_str = f"FDR q = {fdr_val:.2e}"
                    elif raw_p > 0.0:
                        q_str = f"p = {raw_p:.1e} (q < 10⁻¹⁰)"
                    else:
                        q_str = "FDR q < 0.001"

                    st.markdown(
                        f"""
                        <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-left: 4px solid #DC2626; border-radius: 6px; padding: 0.65rem 0.95rem; margin-bottom: 0.45rem; display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span style="color: #1E40AF; font-weight: 700; font-size: 0.90rem;">{pw['source_name']}</span>
                                <span style="color: #64748B; margin: 0 6px;">⟶</span>
                                <span style="color: #991B1B; font-weight: 700; font-size: 0.90rem;">{pw['target_name']}</span>
                            </div>
                            <div>
                                <span style="background-color: #FEF2F2; color: #DC2626; border: 1px solid #FCA5A5; padding: 2px 8px; border-radius: 4px; font-size: 0.82rem; font-weight: 700;">
                                    RR: {pw.get('relative_risk', 1.0):.2f}×
                                </span>
                                <span style="color: #64748B; font-size: 0.78rem; margin-left: 8px;">
                                    {q_str}
                                </span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        existing_cids = set()
        high_risk_cids = set()
        patient_pathways = []
        
    st.markdown("---")
    
    # -------------------------------------------------------------------------
    # 3. Interactive Network Controls & Filters
    # -------------------------------------------------------------------------
    f_col1, f_col2, f_col3 = st.columns([1.5, 1.5, 1])
    with f_col1:
        category_filter = st.selectbox(
            "Filter Source Category",
            options=["All Categories"] + [c for c in CLINICAL_CATEGORIES if c != "Background History"],
            index=0
        )
    with f_col2:
        min_rr_filter = st.slider("Minimum Relative Risk (RR)", min_value=1.0, max_value=20.0, value=2.0, step=0.5)
    with f_col3:
        sig_only = st.checkbox("Significant Only (FDR q < 0.05)", value=True)
        
    # Filter edges
    filtered_edges = []
    for e in edges:
        if sig_only and not e.get("is_significant", False):
            continue
        if float(e.get("relative_risk", 1.0)) < min_rr_filter:
            continue
        src_info = nodes.get(str(e["source_id"]), {})
        if category_filter != "All Categories" and src_info.get("category") != category_filter:
            continue
        filtered_edges.append(e)
        
    # Sort by relative risk
    filtered_edges.sort(key=lambda x: x.get("relative_risk", 0.0), reverse=True)
    
    # -------------------------------------------------------------------------
    # 4. Disease Network Connections & Pathways Table
    # -------------------------------------------------------------------------
    st.markdown(f"### Directed Disease Pathways ({len(filtered_edges)} associations)")
    st.caption("Each edge represents: *Given pre-existing condition A, the relative risk of developing condition B within 1 year.*")
    
    if filtered_edges:
        table_rows = []
        for e in filtered_edges[:50]:
            src_id = int(e["source_id"])
            tgt_id = int(e["target_id"])
            
            # Status flags for patient overlay
            src_tag = " [Patient Has]" if src_id in existing_cids else ""
            tgt_tag = " [HIGH RISK]" if tgt_id in high_risk_cids else ""
            
            table_rows.append({
                "Pre-Existing Condition (A)": f"{e['source_name']}{src_tag}",
                "Incident Comorbidity (B)": f"{e['target_name']}{tgt_tag}",
                "Relative Risk (RR)": f"{e.get('relative_risk', 1.0):.2f}×",
                "FDR q-value": f"{e.get('fdr_q_value', 0.0):.4e}",
                "Exposed Cases": f"{e.get('a_exposed_incident', 0)} / {e.get('n_exposed', 0)}",
                "Status": "Active Pathway" if src_id in existing_cids and tgt_id in high_risk_cids else "Population Association"
            })
            
        df_display = pd.DataFrame(table_rows)
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No network edges match the selected filters. Try lowering the Minimum Relative Risk.")
        
    # -------------------------------------------------------------------------
    # 5. Top Comorbidity Hubs (Degree Centrality)
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### Comorbidity Hubs & Network Centrality")
    
    hub_col1, hub_col2 = st.columns(2)
    with hub_col1:
        st.markdown("#### Top Risk Drivers (Highest Out-Degree)")
        st.caption("Conditions most frequently associated with downstream multi-organ comorbidity cascades.")
        sorted_out = sorted(nodes.values(), key=lambda x: x.get("out_degree_centrality", 0.0), reverse=True)[:6]
        for node in sorted_out:
            st.markdown(
                f"- **{node['concept_name']}** ({node.get('category', 'General')}) — "
                f"Out-Degree Centrality: `{node.get('out_degree_centrality', 0.0):.3f}`"
            )
            
    with hub_col2:
        st.markdown("#### Top Comorbidity Endpoints (Highest In-Degree)")
        st.caption("Conditions most frequently preceded by diverse antecedent risk factors.")
        sorted_in = sorted(nodes.values(), key=lambda x: x.get("in_degree_centrality", 0.0), reverse=True)[:6]
        for node in sorted_in:
            st.markdown(
                f"- **{node['concept_name']}** ({node.get('category', 'General')}) — "
                f"In-Degree Centrality: `{node.get('in_degree_centrality', 0.0):.3f}`"
            )


if __name__ == "__main__":
    render()