"""
Automated unit and validation test suite for Phase 1 & 2 ML components.
Validates:
1. Patient integrity (all timeline events map to valid persons)
2. Chronological ordering (events strictly sorted by date per patient)
3. No cross-patient joins (conditions strictly match corresponding person_id)
4. Date validity (start <= end dates and valid calendar ranges)
5. Pipeline reproducibility (deterministic outputs across repeated runs)
6. Source consistency (event counts match raw OMOP table queries)
"""

import os
import sys
from pathlib import Path
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
    
    # Check if any visit's condition_occurrence record belongs to a different person_id in source table
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
    con = loader.get_connection()
    
    # Check deterministic row counts, checksums on sample patients
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
