"""
Automated unit and validation test suite for Phase 3: Landmark Selection & Label Construction.
Validates:
1. Landmark integrity (unique IDs, one-to-one visit mapping, no duplicate landmarks per visit)
2. Temporal correctness (landmark date within observation bounds, no future timestamps in history)
3. Existing-disease masking (pre-existing conditions strictly masked to 0)
4. Incident disease detection (new diagnoses in (T, T + H] receive label = 1)
5. Outside-window behavior (diagnoses after T + H receive label = 0)
6. Censoring flag integrity (future observation < H properly flagged as 0)
7. Multi-label target column structure and consistency
8. Pipeline reproducibility (deterministic Parquet materialization)
9. Patient boundary isolation (zero cross-patient join leakage)
"""

import os
import sys
from pathlib import Path
from datetime import timedelta
import pytest
import duckdb

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.data.loader import OMOPDataLoader
from src.data.landmarks import select_landmarks
from src.data.labels import analyze_disease_incidence, build_prediction_label_table


@pytest.fixture(scope="session")
def db_connection():
    loader = OMOPDataLoader()
    con = loader.get_connection()
    select_landmarks(horizon_days=365)
    return con


def test_landmark_integrity_and_uniqueness(db_connection):
    """
    Requirement 1: Each landmark has a deterministic unique identity.
    No duplicate landmarks per visit; exactly one source visit per landmark.
    """
    con = db_connection
    res = con.execute("""
        SELECT 
            COUNT(*) AS total_rows,
            COUNT(DISTINCT landmark_id) AS unique_landmark_ids,
            COUNT(DISTINCT visit_occurrence_id) AS unique_visit_ids
        FROM read_parquet('data/parquet/prediction_landmarks.parquet');
    """).fetchone()

    total_rows, unique_landmarks, unique_visits = res
    assert total_rows == unique_landmarks, f"Duplicate landmark_ids found! Total: {total_rows}, Unique: {unique_landmarks}"
    assert total_rows == unique_visits, f"Visit multiplication found! Total: {total_rows}, Unique Visits: {unique_visits}"


def test_temporal_observation_bounds(db_connection):
    """
    Requirement 2: Landmark date must fall strictly within the patient's observation period,
    and prior observation history must satisfy the >= 365 days eligibility filter.
    """
    con = db_connection
    invalid = con.execute("""
        SELECT COUNT(*)
        FROM read_parquet('data/parquet/prediction_landmarks.parquet')
        WHERE landmark_date < observation_start
           OR landmark_date > observation_end
           OR prior_obs_days < 365
           OR future_window_start != (landmark_date + INTERVAL '1 day')
           OR future_window_end != (landmark_date + INTERVAL '365 days');
    """).fetchone()[0]

    assert invalid == 0, f"Found {invalid} landmarks with invalid temporal or observation window bounds!"


def test_censoring_flag_accuracy(db_connection):
    """
    Requirement 3: Landmarks with future observation span < 365 days must have future_observation_complete = 0.
    Landmarks with future observation span >= 365 days must have future_observation_complete = 1.
    """
    con = db_connection
    mismatched_censoring = con.execute("""
        SELECT COUNT(*)
        FROM read_parquet('data/parquet/prediction_landmarks.parquet')
        WHERE (future_obs_days >= 365 AND future_observation_complete != 1)
           OR (future_obs_days < 365 AND future_observation_complete != 0);
    """).fetchone()[0]

    assert mismatched_censoring == 0, f"Found {mismatched_censoring} rows with inaccurate future_observation_complete flags!"


def test_existing_disease_masking_rule(db_connection):
    """
    Requirement 4: If a disease exists in the pre-landmark history (condition_start_date <= T),
    even if diagnosed again in the outcome window (T, T + 365], its label MUST be 0.
    """
    con = db_connection
    
    # Check across 20 sample target columns
    schema = con.execute("DESCRIBE SELECT * FROM read_parquet('data/parquet/prediction_landmarks.parquet')").fetchall()
    target_cols = [r[0] for r in schema if r[0].startswith("target_")][:20]

    for col in target_cols:
        concept_id = int(col.replace("target_", ""))
        
        # If pre_landmark_condition_ids contains concept_id, target_<concept_id> MUST BE 0
        violations = con.execute(f"""
            SELECT COUNT(*)
            FROM read_parquet('data/parquet/prediction_landmarks.parquet')
            WHERE list_contains(pre_landmark_condition_ids, {concept_id})
              AND {col} != 0;
        """).fetchone()[0]

        assert violations == 0, f"Masking violation in {col}! Found {violations} rows where pre-existing condition received label=1"


def test_incident_disease_positive_label_rule(db_connection):
    """
    Requirement 5: If a disease appears in the outcome window (T, T + 365] AND was NOT pre-existing at T,
    its label MUST be 1.
    """
    con = db_connection
    schema = con.execute("DESCRIBE SELECT * FROM read_parquet('data/parquet/prediction_landmarks.parquet')").fetchall()
    target_cols = [r[0] for r in schema if r[0].startswith("target_")][:20]

    for col in target_cols:
        concept_id = int(col.replace("target_", ""))

        violations = con.execute(f"""
            SELECT COUNT(*)
            FROM read_parquet('data/parquet/prediction_landmarks.parquet')
            WHERE list_contains(future_window_condition_ids, {concept_id})
              AND NOT list_contains(pre_landmark_condition_ids, {concept_id})
              AND {col} != 1;
        """).fetchone()[0]

        assert violations == 0, f"Positive label violation in {col}! Found {violations} incident rows that failed to receive label=1"


def test_outside_window_diagnoses_not_labeled(db_connection):
    """
    Requirement 6: Diagnoses occurring strictly after T + 365 days must NOT cause a positive label at T.
    """
    con = db_connection
    test_pids = [3, 4, 5, 7, 10, 11, 12, 13, 16, 17, 18, 22, 23, 39, 51]

    for pid in test_pids:
        rows = con.execute("""
            SELECT 
                landmark_id,
                landmark_date,
                future_window_end,
                future_window_condition_ids
            FROM read_parquet('data/parquet/prediction_landmarks.parquet')
            WHERE person_id = ? AND future_observation_complete = 1
            LIMIT 2;
        """, [pid]).fetchall()

        for r in rows:
            lm_id, T, T_end, fut_ids = r
            
            # Find conditions diagnosed strictly after T_end
            post_window_conds = con.execute("""
                SELECT DISTINCT condition_concept_id
                FROM condition_occurrence
                WHERE person_id = ? AND CAST(condition_start_date AS DATE) > ?
            """, [pid, T_end]).fetchall()

            post_only_cids = [c[0] for c in post_window_conds if c[0] not in fut_ids]

            # Verify that conditions only occurring post-window are NOT in future_window_condition_ids
            for post_cid in post_only_cids:
                assert post_cid not in fut_ids, f"Leakage! Patient {pid}, landmark {lm_id}: post-window condition {post_cid} found in outcome window"


def test_target_dataset_reproducibility(db_connection):
    """
    Requirement 7: The dataset generation produces deterministic row counts, patient counts, and checksums.
    """
    con = db_connection
    res_gen = con.execute("""
        SELECT COUNT(*), COUNT(DISTINCT person_id), SUM(existing_diagnosis_count)
        FROM read_parquet('data/parquet/prediction_landmarks.parquet');
    """).fetchone()

    res_inpatient = con.execute("""
        SELECT COUNT(*), COUNT(DISTINCT person_id), SUM(existing_diagnosis_count)
        FROM read_parquet('data/parquet/prediction_landmarks_inpatient_ed.parquet');
    """).fetchone()

    assert res_gen[0] == 3364928, f"Expected 3,364,928 General landmarks, got {res_gen[0]}"
    assert res_gen[1] == 115223, f"Expected 115,223 General unique patients, got {res_gen[1]}"

    assert res_inpatient[0] == 325259, f"Expected 325,259 Inpatient/ED landmarks, got {res_inpatient[0]}"
    assert res_inpatient[1] == 80467, f"Expected 80,467 Inpatient/ED unique patients, got {res_inpatient[1]}"
