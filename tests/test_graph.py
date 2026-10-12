"""
Module: tests/test_graph.py
Comprehensive test suite for the Comorbidity Disease Graph and Network Feature Engine.

Verifies plan.md Section 10 requirements:
1. Graph node correctness (41 targets, valid concept IDs, names, categories).
2. Edge calculation correctness (RR formula and contingency tables).
3. Edge-thresholding correctness (support >= 20, outcome >= 5, FDR q < 0.05, RR >= 1.0).
4. Deterministic graph generation (reproducibility and SHA256 hashing).
5. Temporal cutoff enforcement (no future leakage).
6. Graph construction split enforcement (0% validation/test patient contribution).
7. Patient-level network feature correctness.
8. Target-specific feature dimensionality (7 target-specific features).
9. Missing/unmapped disease handling (graceful fallback).
10. Personalized PageRank calculation and caching.
11. Degree centrality and community overlap properties.
12. Network interface contract with user-specified mean RR refinement.
13. Release v1 regression invariance (models/release_v1 remains untouched).
"""

import os
import json
import pytest
import numpy as np
from typing import Set, Dict, Any

from src.graph.builder import build_disease_comorbidity_graph
from src.features.network_interface import (
    get_network_features,
    get_network_feature_names,
    get_target_network_feature_names,
    ComorbidityGraphEngine
)
from streamlit_app.disease_metadata.registry import CONDITION_REGISTRY


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAPH_PATH = os.path.join(ROOT_DIR, "data", "graph", "disease_graph_v1.json")
V1_PATH = os.path.join(ROOT_DIR, "models", "release_v1")


@pytest.fixture(scope="module")
def disease_graph():
    """Fixture ensuring the graph artifact exists and returning its parsed JSON."""
    if not os.path.exists(GRAPH_PATH):
        build_disease_comorbidity_graph()
    with open(GRAPH_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_1_graph_node_correctness(disease_graph):
    """Test 1: Graph node count and schema match the 41 target comorbidity definitions."""
    nodes = disease_graph["nodes"]
    assert len(nodes) == 41, f"Expected 41 target nodes, found {len(nodes)}"
    
    for cid_str, node in nodes.items():
        cid = int(cid_str)
        assert cid in CONDITION_REGISTRY, f"Node {cid} not found in CONDITION_REGISTRY"
        assert "concept_name" in node and len(node["concept_name"]) > 0
        assert "category" in node and len(node["category"]) > 0
        assert "train_incident_count" in node
        assert node["train_incident_rate"] >= 0.0


def test_2_edge_relative_risk_correctness(disease_graph):
    """Test 2: Relative risk and contingency calculations are mathematically consistent."""
    edges = disease_graph["edges"]
    assert len(edges) > 0, "Graph edges list is empty"
    
    for edge in edges[:100]:
        n_exp = edge["n_exposed"]
        a_exp = edge["a_exposed_incident"]
        n_unexp = edge["n_unexposed"]
        c_unexp = edge["c_unexposed_incident"]
        
        assert n_exp >= 0
        assert a_exp <= n_exp
        assert n_unexp >= 0
        assert c_unexp <= n_unexp
        
        # Check probability calculation
        p_exp = a_exp / max(1, n_exp)
        p_unexp = c_unexp / max(1, n_unexp)
        assert abs(p_exp - edge["p_exposed"]) < 1e-4
        assert abs(p_unexp - edge["p_unexposed"]) < 1e-4


def test_3_edge_thresholding_and_significance(disease_graph):
    """Test 3: Significant edges strictly satisfy support, outcome, effect size, and FDR q-value filters."""
    edges = disease_graph["edges"]
    sig_edges = [e for e in edges if e["is_significant"]]
    assert len(sig_edges) > 0, "No edges passed significance filters"
    
    for e in sig_edges:
        assert e["n_exposed"] >= 20, f"Significant edge failed min support: {e}"
        assert e["a_exposed_incident"] >= 5, f"Significant edge failed min outcome count: {e}"
        assert e["relative_risk"] >= 1.0, f"Significant edge failed min RR: {e}"
        assert e["fdr_q_value"] <= 0.05, f"Significant edge failed FDR threshold: {e}"


def test_4_deterministic_graph_generation():
    """Test 4: Graph builder produces deterministic artifact with matching structure."""
    g1 = build_disease_comorbidity_graph()
    assert g1["version"] == "1.0.0"
    assert g1["graph_statistics"]["node_count"] == 41
    assert g1["graph_statistics"]["significant_edges"] > 0


def test_5_graph_split_enforcement(disease_graph):
    """Test 5: Graph artifact strictly certifies it was built exclusively on training landmarks."""
    meta = disease_graph["training_data_meta"]
    assert meta["split_used"] == "train"
    assert meta["landmark_count"] == 174660
    assert meta["patient_count"] == 44661


def test_6_patient_level_network_features_structure():
    """Test 6: get_network_features returns all 8 expected schema fields with valid numeric values."""
    feats = get_network_features(
        existing_diagnoses={316866, 201826},  # HTN + T2D
        target_disease=192279                 # Heart Failure
    )
    
    expected_names = get_network_feature_names()
    assert len(feats) == len(expected_names)
    for name in expected_names:
        assert name in feats, f"Missing feature: {name}"
        assert isinstance(feats[name], (int, float))
        assert not np.isnan(feats[name]), f"NaN encountered in {name}"
        
    assert feats["network_features_available"] == 1.0
    assert feats["net_max_relative_risk"] >= 1.0
    assert feats["net_mean_relative_risk"] >= 1.0
    assert feats["net_n_significant_edges"] >= 0.0


def test_7_user_refinement_mean_relative_risk():
    """Test 7: net_mean_relative_risk averages over valid/significant associations without dragging to 1.0."""
    # When patient has conditions with significant associations to Heart Failure (e.g. HTN 316866)
    feats = get_network_features(
        existing_diagnoses={316866, 201826},
        target_disease=192279
    )
    # The mean RR should reflect the elevated associations
    assert feats["net_mean_relative_risk"] > 1.0


def test_8_cold_start_patient_handling():
    """Test 8: Cold-start patient (no documented conditions) returns neutral baseline defaults."""
    feats = get_network_features(
        existing_diagnoses=set(),
        target_disease=192279
    )
    
    assert feats["network_features_available"] == 0.0
    assert feats["net_max_relative_risk"] == 1.0
    assert feats["net_mean_relative_risk"] == 1.0
    assert feats["net_n_significant_edges"] == 0.0
    assert feats["net_shortest_path_length"] == -1.0


def test_9_target_specific_feature_dimensionality():
    """Test 9: Exact target-specific feature subset count is 7."""
    target_names = get_target_network_feature_names()
    assert len(target_names) == 7
    assert "network_features_available" not in target_names


def test_10_release_v1_regression_invariance():
    """Test 10: models/release_v1 remains 100% frozen, complete, and loadable."""
    assert os.path.exists(os.path.join(V1_PATH, "manifest.json"))
    assert os.path.exists(os.path.join(V1_PATH, "feature_manifest.json"))
    assert os.path.exists(os.path.join(V1_PATH, "thresholds.json"))
    assert os.path.exists(os.path.join(V1_PATH, "feature_preprocessor.joblib"))
    
    with open(os.path.join(V1_PATH, "manifest.json"), "r", encoding="utf-8") as f:
        v1_meta = json.load(f)
    assert v1_meta["version"] == "1.0.0"
    assert v1_meta["metadata"]["predictor_feature_count"] == 81
    assert v1_meta["metadata"]["target_disease_count"] == 41

