"""
Module: src/graph/builder.py
Constructs, validates, and freezes the directed Disease Comorbidity Graph artifact.

Key Requirements (per plan.md Section 3):
1. Nodes: 41 curated chronic comorbidity targets (OMOP concept IDs, standard names, clinical categories).
2. Edges: Directed, temporal Relative Risk RR(A -> B) = P(B incident within 365d | A present at T_land) / P(B incident | A absent).
3. Leakage boundary: Built EXCLUSIVELY on training-split landmarks (0% validation or test data contribution).
4. Thresholding: Support >= 20, outcome count >= 5, Fisher's exact / chi-square test with Benjamini-Hochberg FDR correction (q < 0.05), RR >= 1.0.
5. Serialization: Freezes graph artifact with SHA256 checksum, graph topology, degree centralities, and community detection.
"""

import os
import sys
import json
import hashlib
import numpy as np
import pandas as pd
import duckdb
import networkx as nx
from typing import Dict, List, Any, Optional, Tuple, Set
from scipy.stats import fisher_exact, chi2_contingency
from datetime import datetime, timezone

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from streamlit_app.disease_metadata.registry import (
    CONDITION_REGISTRY,
    get_condition_info
)


DATA_PARQUET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "parquet")
GRAPH_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "graph")



def _benjamini_hochberg(p_values: List[float]) -> List[float]:
    """Applies Benjamini-Hochberg FDR correction to a list of p-values."""
    p_arr = np.array(p_values, dtype=float)
    n = len(p_arr)
    if n == 0:
        return []
    
    sorted_indices = np.argsort(p_arr)
    sorted_p = p_arr[sorted_indices]
    
    q_values = np.zeros(n, dtype=float)
    min_q = 1.0
    for i in range(n - 1, -1, -1):
        rank = i + 1
        q = (sorted_p[i] * n) / rank
        min_q = min(min_q, q)
        q_values[i] = min(min_q, 1.0)
        
    result = np.zeros(n, dtype=float)
    result[sorted_indices] = q_values
    return result.tolist()


def build_disease_comorbidity_graph(
    parquet_path: Optional[str] = None,
    output_path: Optional[str] = None,
    min_support: int = 20,
    min_outcome_count: int = 5,
    min_rr: float = 1.0,
    fdr_threshold: float = 0.05
) -> Dict[str, Any]:
    """
    Builds the directed comorbidity disease graph using training split data only.
    
    Parameters:
    - parquet_path: Path to splits_inpatient_ed.parquet (defaults to data/parquet/splits_inpatient_ed.parquet).
    - output_path: Path to save frozen graph JSON artifact.
    - min_support: Minimum number of exposed training landmarks.
    - min_outcome_count: Minimum exposed & incident event count.
    - min_rr: Minimum relative risk effect size floor.
    - fdr_threshold: Maximum Benjamini-Hochberg FDR q-value for significance.
    
    Returns:
    - Graph artifact dictionary.
    """
    if parquet_path is None:
        parquet_path = os.path.join(DATA_PARQUET_DIR, "splits_inpatient_ed.parquet")
    if output_path is None:
        output_path = os.path.join(GRAPH_OUTPUT_DIR, "disease_graph_v1.json")
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print(f"[GraphBuilder] Loading training split from {parquet_path}...")
    con = duckdb.connect()
    
    # Query training landmarks ONLY (strict leakage boundary)
    query = f"""
    SELECT 
        landmark_id,
        person_id,
        pre_landmark_condition_ids,
        * EXCLUDE (landmark_id, person_id, pre_landmark_condition_ids)
    FROM '{parquet_path.replace(os.sep, "/")}'
    WHERE split = 'train'
    """
    df_train = con.execute(query).df()
    n_train_landmarks = len(df_train)
    n_train_patients = df_train['person_id'].nunique()
    print(f"[GraphBuilder] Training data loaded: {n_train_landmarks} landmarks across {n_train_patients} unique patients.")
    
    # Extract target column names and IDs
    target_cols = [c for c in df_train.columns if c.startswith('target_')]
    target_ids = [int(c.replace('target_', '')) for c in target_cols]
    
    print(f"[GraphBuilder] Found {len(target_ids)} target comorbidity columns.")
    
    # 1. Build Nodes
    nodes: Dict[str, Dict[str, Any]] = {}
    for cid in target_ids:
        info = get_condition_info(cid)
        target_col = f"target_{cid}"
        incidence_count = int(df_train[target_col].sum()) if target_col in df_train.columns else 0
        incidence_rate = float(incidence_count / max(1, n_train_landmarks))
        
        nodes[str(cid)] = {
            "concept_id": cid,
            "concept_name": info.canonical_term,
            "category": info.category,
            "plain_explanation": info.plain_language_explanation,
            "icd10_hint": info.icd10_hint,
            "train_incident_count": incidence_count,
            "train_incident_rate": round(incidence_rate, 6)
        }
        
    # Pre-extract pre-landmark diagnosis sets for each training row
    print("[GraphBuilder] Indexing pre-landmark diagnosis sets...")
    pre_diag_sets: List[Set[int]] = []
    for diag_list in df_train['pre_landmark_condition_ids']:
        if isinstance(diag_list, np.ndarray):
            pre_diag_sets.append(set(diag_list.tolist()))
        elif isinstance(diag_list, list):
            pre_diag_sets.append(set(diag_list))
        else:
            pre_diag_sets.append(set())
            
    # Convert target binary columns to numpy boolean arrays for fast vectorized indexing
    target_arrays: Dict[int, np.ndarray] = {}
    for cid in target_ids:
        target_arrays[cid] = df_train[f"target_{cid}"].values.astype(bool)
        
    # 2. Compute Pairwise Temporal Relative Risk for all ordered pairs (A -> B)
    print("[GraphBuilder] Computing directed pairwise relative risks...")
    candidate_edges: List[Dict[str, Any]] = []
    
    # Create indicator matrix for exposure A
    exposure_arrays: Dict[int, np.ndarray] = {}
    for cid in target_ids:
        exposure_arrays[cid] = np.array([cid in s for s in pre_diag_sets], dtype=bool)
        
    p_values: List[float] = []
    
    for src_id in target_ids:
        exp_mask = exposure_arrays[src_id]
        n_exposed = int(np.sum(exp_mask))
        n_unexposed = n_train_landmarks - n_exposed
        
        if n_exposed == 0:
            continue
            
        for dst_id in target_ids:
            if src_id == dst_id:
                continue  # Skip self-loops
                
            dst_target = target_arrays[dst_id]
            
            # Contingency table:
            # a: exposed & B incident
            # b: exposed & B not incident
            # c: unexposed & B incident
            # d: unexposed & B not incident
            a = int(np.sum(exp_mask & dst_target))
            b = n_exposed - a
            c = int(np.sum((~exp_mask) & dst_target))
            d = n_unexposed - c
            
            p_exposed = a / max(1, n_exposed)
            p_unexposed = c / max(1, n_unexposed)
            
            # Smooth RR calculation to avoid zero-division
            if p_unexposed > 0:
                rr = p_exposed / p_unexposed
            elif p_exposed > 0:
                # Laplace smoothed estimate
                rr = ((a + 0.5) / (n_exposed + 1.0)) / ((c + 0.5) / (n_unexposed + 1.0))
            else:
                rr = 1.0
                
            # 2x2 contingency table test (Fisher exact if small cells, else chi-square)
            table = [[a, b], [c, d]]
            if min(a, b, c, d) < 5:
                _, p_val = fisher_exact(table)
            else:
                _, p_val, _, _ = chi2_contingency(table, correction=True)
                
            candidate_edges.append({
                "source_id": src_id,
                "target_id": dst_id,
                "source_name": nodes[str(src_id)]["concept_name"],
                "target_name": nodes[str(dst_id)]["concept_name"],
                "n_exposed": n_exposed,
                "n_unexposed": n_unexposed,
                "a_exposed_incident": a,
                "c_unexposed_incident": c,
                "p_exposed": round(float(p_exposed), 6),
                "p_unexposed": round(float(p_unexposed), 6),
                "relative_risk": round(float(rr), 4),
                "raw_p_value": float(p_val)
            })
            p_values.append(float(p_val))
            
    # Apply Benjamini-Hochberg FDR correction
    q_values = _benjamini_hochberg(p_values)
    
    # 3. Filter Significant Edges
    final_edges: List[Dict[str, Any]] = []
    significant_edge_count = 0
    
    for i, edge in enumerate(candidate_edges):
        q_val = q_values[i]
        edge["fdr_q_value"] = round(float(q_val), 6)
        
        # Combined statistical and effect size filter
        is_sig = bool(
            edge["n_exposed"] >= min_support and
            edge["a_exposed_incident"] >= min_outcome_count and
            edge["relative_risk"] >= min_rr and
            q_val < fdr_threshold
        )
        edge["is_significant"] = is_sig
        if is_sig:
            significant_edge_count += 1
            
        final_edges.append(edge)
        
    print(f"[GraphBuilder] Computed {len(final_edges)} total directed pairs; {significant_edge_count} passed significance filters.")
    
    # 4. Graph Topological Analysis using NetworkX
    G = nx.DiGraph()
    for cid in target_ids:
        G.add_node(cid, **nodes[str(cid)])
        
    for e in final_edges:
        if e["is_significant"]:
            G.add_edge(e["source_id"], e["target_id"], weight=e["relative_risk"])
            
    # Node degree centralities
    in_degree_dict = nx.in_degree_centrality(G)
    out_degree_dict = nx.out_degree_centrality(G)
    
    for cid in target_ids:
        nodes[str(cid)]["in_degree_centrality"] = round(float(in_degree_dict.get(cid, 0.0)), 4)
        nodes[str(cid)]["out_degree_centrality"] = round(float(out_degree_dict.get(cid, 0.0)), 4)
        nodes[str(cid)]["total_degree_centrality"] = round(float(in_degree_dict.get(cid, 0.0) + out_degree_dict.get(cid, 0.0)), 4)
        
    # Community Detection (using greedy modularity on undirected projection)
    G_undirected = G.to_undirected()
    try:
        communities = nx.community.greedy_modularity_communities(G_undirected)
        for comm_idx, comm_set in enumerate(communities):
            for node_cid in comm_set:
                if str(node_cid) in nodes:
                    nodes[str(node_cid)]["community_id"] = int(comm_idx)
    except Exception as exc:
        print(f"[GraphBuilder] Community detection fallback: {exc}")
        for cid in target_ids:
            nodes[str(cid)]["community_id"] = 0
            
    # Ensure every node has a community_id
    for cid in target_ids:
        if "community_id" not in nodes[str(cid)]:
            nodes[str(cid)]["community_id"] = 0
            
    # 5. Assemble Frozen Graph Artifact
    graph_artifact: Dict[str, Any] = {
        "version": "1.0.0",
        "name": "comorbidity_disease_graph",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "training_data_meta": {
            "source_parquet": os.path.basename(parquet_path),
            "split_used": "train",
            "landmark_count": n_train_landmarks,
            "patient_count": n_train_patients
        },
        "hyperparameters": {
            "min_support": min_support,
            "min_outcome_count": min_outcome_count,
            "min_rr": min_rr,
            "fdr_threshold": fdr_threshold
        },
        "graph_statistics": {
            "node_count": len(nodes),
            "total_tested_edges": len(final_edges),
            "significant_edges": significant_edge_count,
            "density": round(float(nx.density(G)), 4)
        },
        "nodes": nodes,
        "edges": final_edges
    }
    
    # Write JSON artifact
    json_str = json.dumps(graph_artifact, indent=2)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(json_str)
        
    sha256 = hashlib.sha256(json_str.encode("utf-8")).hexdigest()
    graph_artifact["sha256_checksum"] = sha256
    
    print(f"[GraphBuilder] Frozen graph saved to {output_path} (SHA256: {sha256[:12]}...)")
    return graph_artifact


if __name__ == "__main__":
    build_disease_comorbidity_graph()
