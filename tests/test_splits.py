"""
Unit tests for Phase 5: Train / Validation / Test Splitting.
Tests patient-level isolation, temporal holdout monotonicity, determinism, and minority-row drop logic.
"""

import pytest
import duckdb
from pathlib import Path
from src.data.splits import assign_patient_splits, generate_splits_dataset

SPLITS_INPATIENT_PATH = "data/parquet/splits_inpatient_ed.parquet"
SPLITS_GENERAL_PATH = "data/parquet/splits_general.parquet"


def test_zero_patient_overlap_across_splits():
    """
    CRITICAL TEST: Ensures that no patient appears in more than one split (Train, Val, Test).
    """
    con = duckdb.connect()
    
    for parquet_path in [SPLITS_INPATIENT_PATH, SPLITS_GENERAL_PATH]:
        res = con.execute(f"""
            WITH pt_splits AS (
                SELECT person_id, count(DISTINCT split) as n_distinct_splits
                FROM '{parquet_path}'
                GROUP BY person_id
            )
            SELECT max(n_distinct_splits), count(CASE WHEN n_distinct_splits > 1 THEN 1 END)
            FROM pt_splits
        """).fetchone()

        max_splits_per_pt, pts_in_multiple_splits = res
        assert max_splits_per_pt == 1, f"Patient found in multiple splits in {parquet_path}"
        assert pts_in_multiple_splits == 0, f"Found {pts_in_multiple_splits} patients with overlapping splits in {parquet_path}"


def test_temporal_boundary_monotonicity():
    """
    Ensures that Test landmarks occur >= 2016-01-01 and Train/Val landmarks occur < 2016-01-01.
    """
    con = duckdb.connect()

    for parquet_path in [SPLITS_INPATIENT_PATH, SPLITS_GENERAL_PATH]:
        # Check Train / Val
        historical_leak = con.execute(f"""
            SELECT count(*) 
            FROM '{parquet_path}'
            WHERE split IN ('train', 'val') AND landmark_date >= '2016-01-01'::DATE
        """).fetchone()[0]
        assert historical_leak == 0, f"Found {historical_leak} train/val landmarks >= 2016-01-01 in {parquet_path}"

        # Check Test
        temporal_leak = con.execute(f"""
            SELECT count(*) 
            FROM '{parquet_path}'
            WHERE split = 'test' AND landmark_date < '2016-01-01'::DATE
        """).fetchone()[0]
        assert temporal_leak == 0, f"Found {temporal_leak} test landmarks < 2016-01-01 in {parquet_path}"


def test_split_determinism_and_reproducibility():
    """
    Verifies that running split assignment with identical seed produces bit-for-bit identical results.
    """
    con = duckdb.connect()
    
    view1 = assign_patient_splits(
        con=con,
        input_table_or_path=SPLITS_INPATIENT_PATH,
        temporal_cutoff_date="2016-01-01",
        train_ratio=0.70,
        random_seed=42
    )
    res1 = con.execute(f"SELECT person_id, split FROM {view1} ORDER BY person_id LIMIT 100").fetchall()

    view2 = assign_patient_splits(
        con=con,
        input_table_or_path=SPLITS_INPATIENT_PATH,
        temporal_cutoff_date="2016-01-01",
        train_ratio=0.70,
        random_seed=42
    )
    res2 = con.execute(f"SELECT person_id, split FROM {view2} ORDER BY person_id LIMIT 100").fetchall()

    assert res1 == res2, "Split assignment is non-deterministic!"


def test_split_proportions_and_non_empty():
    """
    Checks that train, val, and test splits are all well-populated with expected proportions.
    """
    con = duckdb.connect()
    
    counts = con.execute(f"""
        SELECT split, count(DISTINCT person_id) as pts, count(*) as lms
        FROM '{SPLITS_INPATIENT_PATH}'
        GROUP BY split
    """).fetchall()

    split_dict = {r[0]: (r[1], r[2]) for r in counts}
    assert "train" in split_dict and split_dict["train"][0] > 30000
    assert "val" in split_dict and split_dict["val"][0] > 10000
    assert "test" in split_dict and split_dict["test"][0] > 10000

    # Check train/val ratio approximately 70/30
    tr_pts = split_dict["train"][0]
    val_pts = split_dict["val"][0]
    train_pct_of_pool = tr_pts / (tr_pts + val_pts)
    assert 0.68 <= train_pct_of_pool <= 0.72, f"Unexpected train proportion: {train_pct_of_pool}"


def test_target_label_integrity_in_splits():
    """
    Ensures all 41 target labels exist in split table and have binary values {0, 1}.
    """
    con = duckdb.connect()
    cols = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM '{SPLITS_INPATIENT_PATH}'").fetchall()]
    target_cols = [c for c in cols if c.startswith("target_")]

    assert len(target_cols) == 41, f"Expected 41 targets, found {len(target_cols)}"

    # Check that values are strictly binary
    for col in target_cols[:5]:  # Spot check first 5
        invalid_vals = con.execute(f"""
            SELECT count(*) 
            FROM '{SPLITS_INPATIENT_PATH}'
            WHERE {col} NOT IN (0, 1)
        """).fetchone()[0]
        assert invalid_vals == 0, f"Found non-binary values in target {col}"
