"""
Module: src/features/network_interface.py
Real, production implementation of the Disease Comorbidity Network feature extractor.

Implements plan.md Section 4 & 4.1 with user-directed refinement:
- net_max_relative_risk: Maximum RR(s -> Tgt) among valid/significant edges from patient history S.
- net_mean_relative_risk: Mean RR(s -> Tgt) averaged over valid/significant network associations from S.
- net_n_significant_edges: Count of significant directed connections from S to Tgt.
- net_shortest_path_length: Minimum unweighted graph distance from S to Tgt (-1.0 if disconnected).
- net_personalized_pagerank: Personalized PageRank with restart over S, cached per unique diagnosis set.
- net_target_degree_centrality: Precomputed graph centrality for target comorbidity.
- net_target_community_overlap: Fraction of patient conditions S sharing the target's detected community.
- network_features_available: 1.0 if patient conditions map to graph, 0.0 otherwise.
"""

import os
import json
from functools import lru_cache
from typing import Set, Dict, Any, Optional, List, Tuple
import networkx as nx
import numpy as np


# Standard schema fields for network features
NETWORK_FEATURE_NAMES: List[str] = [
    "net_max_relative_risk",
    "net_mean_relative_risk",
    "net_n_significant_edges",
    "net_shortest_path_length",
    "net_personalized_pagerank",
    "net_target_degree_centrality",
    "net_target_community_overlap",
    "network_features_available"
]

# The 7 target-specific numeric features (excluding the global availability flag)
TARGET_NETWORK_FEATURE_NAMES: List[str] = [
    "net_max_relative_risk",
    "net_mean_relative_risk",
    "net_n_significant_edges",
    "net_shortest_path_length",
    "net_personalized_pagerank",
    "net_target_degree_centrality",
    "net_target_community_overlap"
]


class ComorbidityGraphEngine:
    """Singleton engine caching the frozen disease graph artifact and topology."""
    
    _instance: Optional["ComorbidityGraphEngine"] = None
    
    def __init__(self, graph_path: Optional[str] = None):
        if graph_path is None:
            # Check models/release_v2 first, then data/graph
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            candidate_v2 = os.path.join(root_dir, "models", "release_v2", "disease_graph.json")
            candidate_v1 = os.path.join(root_dir, "data", "graph", "disease_graph_v1.json")
            if os.path.exists(candidate_v2):
                graph_path = candidate_v2
            else:
                graph_path = candidate_v1
                
        self.graph_path = graph_path
        self.nodes: Dict[int, Dict[str, Any]] = {}
        self.edge_lookup: Dict[Tuple[int, int], Dict[str, Any]] = {}
        self.nx_digraph = nx.DiGraph()
        self.target_communities: Dict[int, int] = {}
        self.degree_centralities: Dict[int, float] = {}
        self.shortest_paths: Dict[int, Dict[int, int]] = {}
        self.is_loaded = False
        
        self._load_graph()
        
    def _load_graph(self):
        if not os.path.exists(self.graph_path):
            # Safe empty initialization if file does not exist yet
            return
            
        with open(self.graph_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Parse nodes
        for cid_str, node_data in data.get("nodes", {}).items():
            cid = int(cid_str)
            self.nodes[cid] = node_data
            self.target_communities[cid] = node_data.get("community_id", 0)
            self.degree_centralities[cid] = float(node_data.get("total_degree_centrality", 0.0))
            self.nx_digraph.add_node(cid, **node_data)
            
        # Parse edges
        for edge in data.get("edges", []):
            src = int(edge["source_id"])
            dst = int(edge["target_id"])
            self.edge_lookup[(src, dst)] = edge
            if edge.get("is_significant", False):
                self.nx_digraph.add_edge(src, dst, weight=float(edge.get("relative_risk", 1.0)))
                
        # Precompute all-pairs shortest paths on the significant graph
        try:
            self.shortest_paths = dict(nx.all_pairs_shortest_path_length(self.nx_digraph))
        except Exception:
            self.shortest_paths = {}
            
        self.is_loaded = True
        
    @classmethod
    def get_instance(cls, graph_path: Optional[str] = None) -> "ComorbidityGraphEngine":
        if cls._instance is None or (graph_path is not None and cls._instance.graph_path != graph_path):
            cls._instance = cls(graph_path=graph_path)
        return cls._instance
        
    def compute_personalized_pagerank(self, diagnosis_tuple: Tuple[int, ...]) -> Dict[int, float]:
        """Computes and caches Personalized PageRank for a unique tuple of patient diagnoses."""
        valid_nodes = [c for c in diagnosis_tuple if c in self.nx_digraph]
        if not valid_nodes or len(self.nx_digraph) == 0:
            return {cid: 0.0 for cid in self.nodes}
            
        personalization = {node: (1.0 / len(valid_nodes) if node in valid_nodes else 0.0) for node in self.nx_digraph.nodes}
        try:
            ppr = nx.pagerank(self.nx_digraph, alpha=0.85, personalization=personalization, max_iter=100, tol=1e-6)
            return ppr
        except Exception:
            return {cid: 0.0 for cid in self.nodes}


@lru_cache(maxsize=10000)
def _cached_ppr_vector(diag_tuple: Tuple[int, ...], graph_path: Optional[str] = None) -> Dict[int, float]:
    engine = ComorbidityGraphEngine.get_instance(graph_path=graph_path)
    return engine.compute_personalized_pagerank(diag_tuple)


def get_network_features(
    existing_diagnoses: Set[int],
    target_disease: int,
    age: Optional[int] = None,
    gender_concept_id: Optional[int] = None,
    graph_path: Optional[str] = None
) -> Dict[str, float]:
    """
    Computes graph/network features for a patient diagnosis state S and a target disease T.
    
    Parameters:
    - existing_diagnoses: Set of OMOP condition_concept_id values present on or before landmark T.
    - target_disease: OMOP condition_concept_id of the candidate target comorbidity.
    - age: Patient age at landmark (optional).
    - gender_concept_id: Patient sex concept ID (optional).
    - graph_path: Optional custom path to graph JSON artifact.
    
    Returns:
    - Dict mapping standard feature names to float values.
    """
    engine = ComorbidityGraphEngine.get_instance(graph_path=graph_path)
    
    if not engine.is_loaded:
        # Fallback if graph artifact is not yet built
        return {
            "net_max_relative_risk": 1.0,
            "net_mean_relative_risk": 1.0,
            "net_n_significant_edges": 0.0,
            "net_shortest_path_length": -1.0,
            "net_personalized_pagerank": 0.0,
            "net_target_degree_centrality": 0.0,
            "net_target_community_overlap": 0.0,
            "network_features_available": 0.0
        }
        
    tgt = int(target_disease)
    valid_existing = [c for c in existing_diagnoses if c in engine.nodes]
    
    if not valid_existing:
        # Patient has no mapped graph conditions (cold start)
        return {
            "net_max_relative_risk": 1.0,
            "net_mean_relative_risk": 1.0,
            "net_n_significant_edges": 0.0,
            "net_shortest_path_length": -1.0,
            "net_personalized_pagerank": 0.0,
            "net_target_degree_centrality": float(engine.degree_centralities.get(tgt, 0.0)),
            "net_target_community_overlap": 0.0,
            "network_features_available": 0.0
        }
        
    # 1. Edge-based relative risks
    significant_rrs = []
    all_valid_rrs = []
    
    for src in valid_existing:
        if (src, tgt) in engine.edge_lookup:
            edge = engine.edge_lookup[(src, tgt)]
            rr = float(edge.get("relative_risk", 1.0))
            all_valid_rrs.append(rr)
            if edge.get("is_significant", False):
                significant_rrs.append(rr)
                
    # Max RR: highest risk factor connecting to target (or 1.0 baseline)
    net_max_rr = float(max(significant_rrs)) if significant_rrs else (float(max(all_valid_rrs)) if all_valid_rrs else 1.0)
    
    # Mean RR: User-specified refinement -> average over valid/significant network associations
    if significant_rrs:
        net_mean_rr = float(np.mean(significant_rrs))
    elif all_valid_rrs:
        net_mean_rr = float(np.mean(all_valid_rrs))
    else:
        net_mean_rr = 1.0
        
    net_n_sig = float(len(significant_rrs))
    
    # 2. Shortest Path Length
    min_dist = float("inf")
    for src in valid_existing:
        if src in engine.shortest_paths and tgt in engine.shortest_paths[src]:
            d = engine.shortest_paths[src][tgt]
            if d < min_dist:
                min_dist = d
                
    net_shortest_path = float(min_dist) if min_dist != float("inf") else -1.0
    
    # 3. Personalized PageRank
    diag_tuple = tuple(sorted(valid_existing))
    ppr_vector = _cached_ppr_vector(diag_tuple, graph_path=graph_path)
    net_ppr = float(ppr_vector.get(tgt, 0.0))
    
    # 4. Target Degree Centrality
    net_deg_cent = float(engine.degree_centralities.get(tgt, 0.0))
    
    # 5. Target Community Overlap
    tgt_comm = engine.target_communities.get(tgt, -1)
    if tgt_comm != -1:
        same_comm_count = sum(1 for src in valid_existing if engine.target_communities.get(src, -2) == tgt_comm)
        net_comm_overlap = float(same_comm_count / len(valid_existing))
    else:
        net_comm_overlap = 0.0
        
    return {
        "net_max_relative_risk": round(net_max_rr, 4),
        "net_mean_relative_risk": round(net_mean_rr, 4),
        "net_n_significant_edges": net_n_sig,
        "net_shortest_path_length": net_shortest_path,
        "net_personalized_pagerank": round(net_ppr, 6),
        "net_target_degree_centrality": round(net_deg_cent, 4),
        "net_target_community_overlap": round(net_comm_overlap, 4),
        "network_features_available": 1.0
    }


def get_network_feature_names() -> List[str]:
    """Returns the ordered list of all network feature column names."""
    return list(NETWORK_FEATURE_NAMES)


def get_target_network_feature_names() -> List[str]:
    """Returns the 7 target-specific network feature column names."""
    return list(TARGET_NETWORK_FEATURE_NAMES)
