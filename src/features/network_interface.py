"""
Module: src/features/network_interface.py
Interface contract for the disease comorbidity graph / network feature module.

As specified in COMORBIDITY_ENSEMBLE_ML_PLAN.md (Section 2.4):
The network module provides network-derived features for every (patient snapshot S, candidate target disease T) pair.
Until the disease network graph module is integrated, this module provides a documented, fixed-schema stub
(with network_features_available = 0.0) ensuring that the ML ensemble, feature pipeline, and tests are stable
and can be swapped with the real graph module by modifying only this file.
"""

from typing import Set, Dict, Any, Optional, List


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


def get_network_features(
    existing_diagnoses: Set[int],
    target_disease: int,
    age: Optional[int] = None,
    gender_concept_id: Optional[int] = None
) -> Dict[str, float]:
    """
    Computes graph/network features for a patient diagnosis state S and a target disease T.
    
    Parameters:
    - existing_diagnoses: Set of OMOP condition_concept_id values present on or before landmark T.
    - target_disease: OMOP condition_concept_id of the candidate target comorbidity.
    - age: Patient age at landmark (optional, for age-stratified network queries).
    - gender_concept_id: Patient sex concept ID (optional, for sex-stratified network queries).
    
    Returns:
    - Dict mapping standard feature names to float values.
    """
    # Stub placeholder implementation (returns valid numerical zeros/placeholders)
    # When disease graph is integrated, this will compute personalized PageRank, relative risks, and path lengths.
    return {
        "net_max_relative_risk": 0.0,
        "net_mean_relative_risk": 0.0,
        "net_n_significant_edges": 0.0,
        "net_shortest_path_length": -1.0,  # -1 indicates disconnected / unavailable in stub
        "net_personalized_pagerank": 0.0,
        "net_target_degree_centrality": 0.0,
        "net_target_community_overlap": 0.0,
        "network_features_available": 0.0   # 0.0 = placeholder / stub mode; 1.0 = real graph active
    }


def get_network_feature_names() -> List[str]:
    """Returns the ordered list of network feature column names."""
    return list(NETWORK_FEATURE_NAMES)
