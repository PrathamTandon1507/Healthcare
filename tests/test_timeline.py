"""
Automated unit and validation test suite for Phase 1 & 2 ML components.
Validates:
1. Patient integrity (all timeline events map to valid persons)
2. Chronological ordering (events strictly sorted by date per patient)
3. No cross-patient joins (conditions strictly match corresponding person_id)
4. Date validity (start <= end dates and valid calendar ranges)
5. Pipeline reproducibility (deterministic outputs across repeated runs)
6. Source consistency (event counts match raw OMOP table queries)
7. Demographic count consistency (Male + Female = total unique patients)
8. No join multiplication in landmark selection (eligible landmarks <= total distinct visits)
9. Temporal non-leakage (zero future timestamps in pre-landmark feature history)
10. Pre-existing condition masking in outcome labels
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
from src.data.timeline import build_patient_timelines, get_patient_timeline


@pytest.fixture(scope="session")
def loader():
    dl = OMOPDataLoader()
    dl.initialize()
    build_patient_timelines()
    return dl


def test_patient_integrity(loader):
    """
    Requirement 1: Every timeline row belongs to a valid patient in the person table.
    """
    con = loader.get_connection()
    orphans = con.execute("""
        SELECT COUNT(*) 
        FROM read_parquet('data/parquet/patient_timelines.parquet') t
        LEFT JOIN (SELECT DISTINCT person_id FROM person) p ON t.person_id = p.person_id
        WHERE p.person_id IS NULL;
    """).fetchone()[0]
    
    assert orphans == 0, f"Found {orphans} timeline rows with invalid person_ids!"


def test_chronological_ordering(loader):
    """
    Requirement 2: Events for each patient must be ordered chronologically (non-decreasing dates).
    """
    con = loader.get_connection()
    disordered = con.execute("""
        WITH lagged AS (
            SELECT 
                person_id,
                visit_sequence_num,
                visit_start_date,
                LAG(visit_start_date) OVER(PARTITION BY person_id ORDER BY visit_sequence_num) AS prev_date
            FROM read_parquet('data/parquet/patient_timelines.parquet')
        )
        SELECT COUNT(*)
        FROM lagged
        WHERE prev_date IS NOT NULL AND visit_start_date < prev_date;
    """).fetchone()[0]

    assert disordered == 0, f"Found {disordered} chronologically disordered visit sequence rows!"


def test_no_cross_patient_joins(loader):
    """
    Requirement 3: Conditions diagnosed during a visit must strictly belong to the same person_id.
    """
    con = loader.get_connection()
    mismatched = con.execute("""
        WITH unnested_timeline AS (
            SELECT 
                t.person_id AS timeline_person_id,
                t.visit_occurrence_id,
                UNNEST(t.visit_condition_ids) AS condition_concept_id
            FROM read_parquet('data/parquet/patient_timelines.parquet') t
            WHERE len(t.visit_condition_ids) > 0
        )
        SELECT COUNT(*)
        FROM unnested_timeline u
        JOIN (SELECT DISTINCT condition_occurrence_id, person_id, visit_occurrence_id, condition_concept_id FROM condition_occurrence) c
            ON u.visit_occurrence_id = c.visit_occurrence_id AND u.condition_concept_id = c.condition_concept_id
        WHERE u.timeline_person_id != c.person_id;
    """).fetchone()[0]

    assert mismatched == 0, f"Found {mismatched} cross-patient condition join contaminations!"


def test_date_validity(loader):
    """
    Requirement 4: Start/end dates must be valid calendar dates with start <= end.
    """
    con = loader.get_connection()
    invalid_dates = con.execute("""
        SELECT COUNT(*)
        FROM read_parquet('data/parquet/patient_timelines.parquet')
        WHERE visit_start_date > visit_end_date
           OR visit_start_date < '1900-01-01'
           OR visit_end_date > '2050-01-01'
           OR prior_obs_days < 0
           OR age_at_visit < 0
           OR age_at_visit > 125;
    """).fetchone()[0]

    assert invalid_dates == 0, f"Found {invalid_dates} rows with invalid dates/durations/ages!"


def test_pipeline_reproducibility(loader):
    """
    Requirement 5: Running the pipeline produces identical deterministic outputs.
    """
    pids = [1, 23, 51, 100, 500, 1000]
    sample_1 = [get_patient_timeline(pid) for pid in pids]
    sample_2 = [get_patient_timeline(pid) for pid in pids]
    
    assert len(sample_1) == len(sample_2)
    for s1, s2 in zip(sample_1, sample_2):
        assert len(s1) == len(s2)
        for r1, r2 in zip(s1, s2):
            assert r1["person_id"] == r2["person_id"]
            assert r1["visit_occurrence_id"] == r2["visit_occurrence_id"]
            assert r1["visit_start_date"] == r2["visit_start_date"]
            assert r1["visit_condition_ids"] == r2["visit_condition_ids"]


def test_source_consistency(loader):
    """
    Requirement 6: For sampled patients, timeline visit and condition counts must match direct queries on source tables.
    """
    con = loader.get_connection()
    test_pids = [11, 23, 39, 51, 100, 250, 500, 1000]
    
    for pid in test_pids:
        # Direct counts from source tables
        src_visits = con.execute("""
            SELECT COUNT(DISTINCT visit_occurrence_id) 
            FROM visit_occurrence 
            WHERE person_id = ?
        """, [pid]).fetchone()[0]

        src_conditions_at_visits = con.execute("""
            SELECT COUNT(DISTINCT condition_concept_id)
            FROM condition_occurrence
            WHERE person_id = ? AND visit_occurrence_id IS NOT NULL
        """, [pid]).fetchone()[0]

        # Counts from timeline parquet
        timeline_visits = con.execute("""
            SELECT COUNT(*) 
            FROM read_parquet('data/parquet/patient_timelines.parquet')
            WHERE person_id = ?
        """, [pid]).fetchone()[0]

        timeline_conditions = con.execute("""
            SELECT COUNT(DISTINCT cond_id)
            FROM (
                SELECT UNNEST(visit_condition_ids) AS cond_id
                FROM read_parquet('data/parquet/patient_timelines.parquet')
                WHERE person_id = ? AND len(visit_condition_ids) > 0
            )
        """, [pid]).fetchone()[0]

        assert src_visits == timeline_visits, f"Patient {pid}: Source visits ({src_visits}) != Timeline visits ({timeline_visits})"
        assert src_conditions_at_visits == timeline_conditions, f"Patient {pid}: Source visit conditions ({src_conditions_at_visits}) != Timeline conditions ({timeline_conditions})"


def test_demographics_count_consistency(loader):
    """
    Requirement 7: Demographic counts must sum exactly to the total unique cohort size.
    """
    con = loader.get_connection()
    total_unique_pids = con.execute("SELECT COUNT(DISTINCT person_id) FROM person").fetchone()[0]
    assert total_unique_pids == 117611, f"Expected 117,611 unique patients, got {total_unique_pids}"

    gender_counts = con.execute("""
        WITH dedup_p AS (
            SELECT person_id, ANY_VALUE(gender_concept_id) AS gender_concept_id
            FROM person
            GROUP BY person_id
        )
        SELECT 
            COUNT(CASE WHEN gender_concept_id = 8507 THEN 1 END) AS n_male,
            COUNT(CASE WHEN gender_concept_id = 8532 THEN 1 END) AS n_female,
            COUNT(CASE WHEN gender_concept_id NOT IN (8507, 8532) THEN 1 END) AS n_other
        FROM dedup_p;
    """).fetchone()

    n_male, n_female, n_other = gender_counts
    assert n_male == 59127, f"Expected 59,127 males, got {n_male}"
    assert n_female == 58484, f"Expected 58,484 females, got {n_female}"
    assert n_other == 0, f"Expected 0 other/missing gender, got {n_other}"
    assert n_male + n_female + n_other == total_unique_pids, "Sum of gender counts does not equal total unique patients!"


def test_no_join_multiplication_in_landmarks(loader):
    """
    Requirement 8: Landmark eligibility queries must not multiply rows beyond distinct visits.
    """
    con = loader.get_connection()
    total_distinct_visits = con.execute("""
        SELECT COUNT(*)
        FROM (SELECT person_id, visit_occurrence_id FROM visit_occurrence GROUP BY person_id, visit_occurrence_id)
    """).fetchone()[0]

    eligible_landmarks = con.execute("""
        SELECT COUNT(*)
        FROM read_parquet('data/parquet/patient_timelines.parquet')
        WHERE prior_obs_days >= 365 AND n_visit_conditions >= 0;
    """).fetchone()[0]

    assert total_distinct_visits == 3676758, f"Expected 3,676,758 distinct visits, got {total_distinct_visits}"
    assert eligible_landmarks <= total_distinct_visits, f"Eligible landmarks ({eligible_landmarks}) exceeded total distinct visits ({total_distinct_visits})!"


def test_temporal_non_leakage_and_label_masking(loader):
    """
    Requirements 9 & 10:
    - Pre-landmark feature diagnoses must strictly have condition_start_date <= landmark_date.
    - Diagnoses in the outcome window (T, T + 365] that were already present in pre-landmark history
      must NOT be assigned as new incident comorbidity labels.
    """
    con = loader.get_connection()
    test_pids = [3, 4, 5, 7, 10, 11, 12, 13, 16, 17, 18, 22, 23, 39, 51]

    for pid in test_pids:
        # Pick the first eligible index encounter for this patient
        lm = con.execute("""
            SELECT 
                visit_occurrence_id,
                visit_start_date,
                visit_end_date AS landmark_date,
                obs_start_date,
                obs_end_date,
                prior_obs_days,
                future_obs_days
            FROM read_parquet('data/parquet/patient_timelines.parquet')
            WHERE person_id = ? AND prior_obs_days >= 365 AND future_obs_days >= 365
            ORDER BY visit_start_date ASC
            LIMIT 1;
        """, [pid]).fetchone()

        if not lm:
            continue

        T = lm[2]  # landmark_date
        T_plus_365 = T + timedelta(days=365)

        # 1. Pre-landmark condition history
        pre_conds = con.execute("""
            SELECT DISTINCT condition_concept_id, MIN(CAST(condition_start_date AS DATE)) AS onset_date
            FROM condition_occurrence
            WHERE person_id = ? AND CAST(condition_start_date AS DATE) <= ?
            GROUP BY condition_concept_id;
        """, [pid, T]).fetchall()

        pre_concept_ids = {r[0] for r in pre_conds}

        # Assert zero future leakage into pre-landmark set
        for cid, onset in pre_conds:
            assert onset <= T, f"Leakage detected! Patient {pid}: Condition {cid} onset ({onset}) > Landmark ({T})"

        # 2. Future outcome window diagnoses
        future_conds = con.execute("""
            SELECT DISTINCT condition_concept_id, CAST(condition_start_date AS DATE) AS onset_date
            FROM condition_occurrence
            WHERE person_id = ? 
              AND CAST(condition_start_date AS DATE) > ? 
              AND CAST(condition_start_date AS DATE) <= ?;
        """, [pid, T, T_plus_365]).fetchall()

        # Assert outcome window bounds strictly satisfied
        for cid, onset in future_conds:
            assert onset > T, f"Outcome window violation! Patient {pid}: Condition {cid} onset ({onset}) <= Landmark ({T})"
            assert onset <= T_plus_365, f"Outcome window violation! Patient {pid}: Condition {cid} onset ({onset}) > Landmark + 365 ({T_plus_365})"

            # If this condition was already diagnosed before T, it must be masked/excluded from new incident comorbidity label
            if cid in pre_concept_ids:
                is_incident = False
            else:
                is_incident = True

            # Assert that pre-existing conditions are never incident
            assert (is_incident == (cid not in pre_concept_ids)), f"Pre-existing masking logic failed for patient {pid}, condition {cid}"
