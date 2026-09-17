"""
Automated unit and validation test suite for Phase 4: Feature Engineering & Target Dissection EDA.

Validates:
1. Row alignment: Exact 1-to-1 correspondence between prediction landmarks and extracted feature matrices.
2. Temporal non-leakage: All features strictly derived from data on or before landmark date T (condition_start_date <= T).
3. Null checks & value validity: Zero unexpected NULLs in feature matrices, valid age/utilization ranges.
4. Interaction term logic: Correct boolean algebra for multi-disease interaction indicators.
5. Network interface contract: Exact schema fields, data types, and default stub values.
"""

import os
import sys
from pathlib import Path
import pytest
import duckdb

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.features.network_interface import get_network_features, get_network_feature_names, NETWORK_FEATURE_NAMES


@pytest.fixture(scope="session")
def db_connection():
    con = duckdb.connect()
    return con


def test_feature_matrix_row_alignment(db_connection):
    """
    Requirement 1: Feature matrices must have exact 1-to-1 row alignment with prediction landmark tables.
    """
    con = db_connection
    
    # Inpatient / ED cohort
    res_inpatient = con.execute("""
        SELECT 
            (SELECT COUNT(*) FROM read_parquet('data/parquet/features_inpatient_ed.parquet')) AS feat_cnt,
            (SELECT COUNT(*) FROM read_parquet('data/parquet/prediction_landmarks_inpatient_ed.parquet')) AS lm_cnt,
            (SELECT COUNT(DISTINCT landmark_id) FROM read_parquet('data/parquet/features_inpatient_ed.parquet')) AS unique_feat_lm;
    """).fetchone()

    assert res_inpatient[0] == 325259, f"Expected 325,259 Inpatient feature rows, got {res_inpatient[0]}"
    assert res_inpatient[0] == res_inpatient[1], f"Mismatch between Inpatient features ({res_inpatient[0]}) and landmarks ({res_inpatient[1]})"
    assert res_inpatient[0] == res_inpatient[2], f"Duplicate landmark_ids in Inpatient features!"

    # General cohort
    res_gen = con.execute("""
        SELECT 
            (SELECT COUNT(*) FROM read_parquet('data/parquet/features_general.parquet')) AS feat_cnt,
            (SELECT COUNT(*) FROM read_parquet('data/parquet/prediction_landmarks.parquet')) AS lm_cnt,
            (SELECT COUNT(DISTINCT landmark_id) FROM read_parquet('data/parquet/features_general.parquet')) AS unique_feat_lm;
    """).fetchone()

    assert res_gen[0] == 3364928, f"Expected 3,364,928 General feature rows, got {res_gen[0]}"
    assert res_gen[0] == res_gen[1], f"Mismatch between General features ({res_gen[0]}) and landmarks ({res_gen[1]})"
    assert res_gen[0] == res_gen[2], f"Duplicate landmark_ids in General features!"


def test_feature_value_ranges_and_nulls(db_connection):
    """
    Requirement 2: No unexpected NULLs in feature columns; demographic & burden indices in valid ranges.
    """
    con = db_connection
    res = con.execute("""
        SELECT 
            COUNT(CASE WHEN age_at_landmark IS NULL OR age_at_landmark < 0 THEN 1 END) AS invalid_age,
            COUNT(CASE WHEN total_prior_condition_count IS NULL OR total_prior_condition_count < 1 THEN 1 END) AS invalid_burden,
            COUNT(CASE WHEN prior_obs_years IS NULL OR prior_obs_years < 1.0 THEN 1 END) AS invalid_prior_obs,
            COUNT(CASE WHEN (gender_male + gender_female) = 0 THEN 1 END) AS invalid_gender,
            COUNT(CASE WHEN (age_lt_30 + age_30_39 + age_40_49 + age_50_59 + age_60_69 + age_70_79 + age_gte_80) != 1 THEN 1 END) AS invalid_age_bins
        FROM read_parquet('data/parquet/features_inpatient_ed.parquet');
    """).fetchone()

    assert res[0] == 0, f"Found {res[0]} invalid/missing age values!"
    assert res[1] == 0, f"Found {res[1]} landmarks with invalid condition counts (< 1)!"
    assert res[2] == 0, f"Found {res[2]} landmarks with prior observation < 1 year!"
    assert res[3] == 0, f"Found {res[3]} landmarks with missing gender indicators!"
    assert res[4] == 0, f"Found {res[4]} landmarks where age decade bins do not sum to exactly 1!"


def test_feature_temporal_non_leakage(db_connection):
    """
    Requirement 3: Feature indicators (has_hist_<cid>) must match strictly condition_start_date <= landmark_date.
    No future diagnoses may leak into pre-landmark feature columns.
    """
    con = db_connection
    
    # Audit across sample of diverse patients
    test_pids = [3, 5, 7, 10, 11, 12, 13, 16, 17, 18, 22, 23, 39, 51]
    
    for pid in test_pids:
        rows = con.execute("""
            SELECT 
                f.landmark_id,
                f.landmark_date,
                f.has_hist_316866,
                f.has_hist_201826,
                f.has_hist_4311629,
                f.has_hist_4229440
            FROM read_parquet('data/parquet/features_inpatient_ed.parquet') f
            WHERE f.person_id = ?
            LIMIT 3;
        """, [pid]).fetchall()

        for lm_id, T, h_htn, h_t2d, h_predm, h_ckd in rows:
            # Query raw condition occurrence table to verify ground truth at T
            raw_cids_at_T = con.execute("""
                SELECT DISTINCT condition_concept_id
                FROM read_parquet('data/parquet/condition_occurrence.parquet')
                WHERE person_id = ? AND CAST(condition_start_date AS DATE) <= ?;
            """, [pid, T]).fetchall()
            raw_cids = {c[0] for c in raw_cids_at_T}

            assert h_htn == (1 if 316866 in raw_cids else 0), f"Hypertension history leakage/mismatch for pt {pid} at {T}!"
            assert h_t2d == (1 if 201826 in raw_cids else 0), f"T2D history leakage/mismatch for pt {pid} at {T}!"
            assert h_predm == (1 if 4311629 in raw_cids else 0), f"Prediabetes history leakage/mismatch for pt {pid} at {T}!"
            assert h_ckd == (1 if 4229440 in raw_cids else 0), f"CKD history leakage/mismatch for pt {pid} at {T}!"


def test_interaction_term_logic(db_connection):
    """
    Requirement 4: Interaction terms must strictly evaluate to 1 iff both underlying conditions are present.
    """
    con = db_connection
    res = con.execute("""
        SELECT 
            COUNT(CASE 
                WHEN interaction_diabetes_and_hypertension = 1 
                 AND NOT ((has_hist_201826 = 1 OR has_hist_4311629 = 1 OR has_hist_4214376 = 1) AND has_hist_316866 = 1) 
                THEN 1 END) AS false_positives,
            COUNT(CASE 
                WHEN interaction_diabetes_and_hypertension = 0 
                 AND ((has_hist_201826 = 1 OR has_hist_4311629 = 1 OR has_hist_4214376 = 1) AND has_hist_316866 = 1) 
                THEN 1 END) AS false_negatives
        FROM read_parquet('data/parquet/features_inpatient_ed.parquet');
    """).fetchone()

    assert res[0] == 0, f"Found {res[0]} false positive interaction_diabetes_and_hypertension rows!"
    assert res[1] == 0, f"Found {res[1]} false negative interaction_diabetes_and_hypertension rows!"


def test_network_interface_contract():
    """
    Requirement 5: Network interface stub returns exact schema dictionary with valid numerical float outputs.
    """
    features = get_network_features(existing_diagnoses={316866, 201826}, target_disease=4229440, age=55, gender_concept_id=8507)
    
    assert isinstance(features, dict), "get_network_features must return a dictionary!"
    expected_names = get_network_feature_names()
    
    for name in expected_names:
        assert name in features, f"Missing expected network feature: {name}"
        assert isinstance(features[name], float), f"Network feature {name} must be float, got {type(features[name])}"
    
    assert features["network_features_available"] == 0.0, "network_features_available must be 0.0 in stub mode"
    assert features["net_shortest_path_length"] == -1.0, "net_shortest_path_length must be -1.0 in stub mode"
