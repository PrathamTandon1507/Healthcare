"""
Phase 5: Train / Validation / Test Splitting Module.
Implements the hybrid patient-level + temporal splitting strategy defined in Section 6:
1. Patient-level unit of splitting: every landmark for a patient belongs to exactly one split.
2. Temporal holdout test split: prospective window (e.g. >= 2016-01-01) for temporal generalization evaluation.
3. Majority-side patient assignment with minority-side row dropping to avoid cross-boundary leakage.
4. Historical patient-level random split (Train ~70%, Validation ~30%) using deterministic hashing/seed.
5. Support for both Cohort A (Inpatient/ED) and Cohort B (General Encounters).
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import duckdb

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def assign_patient_splits(
    con: duckdb.DuckDBPyConnection,
    input_table_or_path: str,
    temporal_cutoff_date: str = "2016-01-01",
    train_ratio: float = 0.70,
    random_seed: int = 42
) -> str:
    """
    Computes patient-level split assignments and creates a filtered landmark view in DuckDB.
    
    Args:
        con: DuckDB connection.
        input_table_or_path: Path to input parquet or name of DuckDB table/view.
        temporal_cutoff_date: ISO date string for temporal test boundary.
        train_ratio: Fraction of historical pre-cutoff patients assigned to train (remainder to val).
        random_seed: Deterministic random seed for hashing.
        
    Returns:
        Name of the created DuckDB view containing split assignments.
    """
    train_threshold = int(train_ratio * 100)
    
    # 1. Evaluate per-patient landmark distribution relative to cutoff
    con.execute(f"""
        CREATE OR REPLACE TEMP VIEW _pt_landmark_counts AS
        SELECT 
            person_id,
            count(*) AS total_landmarks,
            count(CASE WHEN landmark_date < '{temporal_cutoff_date}'::DATE THEN 1 END) AS pre_cutoff_landmarks,
            count(CASE WHEN landmark_date >= '{temporal_cutoff_date}'::DATE THEN 1 END) AS post_cutoff_landmarks,
            min(landmark_date) AS min_landmark_date,
            max(landmark_date) AS max_landmark_date
        FROM '{input_table_or_path}'
        GROUP BY person_id
    """)

    # 2. Assign each patient to exactly ONE split (Test if post > pre, else Train/Val based on hash)
    con.execute(f"""
        CREATE OR REPLACE TEMP VIEW _pt_split_assignments AS
        SELECT 
            person_id,
            total_landmarks,
            pre_cutoff_landmarks,
            post_cutoff_landmarks,
            min_landmark_date,
            max_landmark_date,
            CASE 
                WHEN post_cutoff_landmarks > pre_cutoff_landmarks THEN 'test'
                WHEN (abs(hash(CONCAT(CAST(person_id AS VARCHAR), '_split_seed_{random_seed}'))) % 100) < {train_threshold} THEN 'train'
                ELSE 'val'
            END AS split
        FROM _pt_landmark_counts
    """)

    # 3. Create filtered landmark-level view respecting majority-side rule (dropping minority rows)
    view_name = "split_assigned_landmarks"
    con.execute(f"""
        CREATE OR REPLACE TEMP VIEW {view_name} AS
        SELECT 
            l.landmark_id,
            l.person_id,
            l.landmark_date,
            s.split,
            s.total_landmarks AS patient_total_landmarks,
            s.pre_cutoff_landmarks AS patient_pre_cutoff_landmarks,
            s.post_cutoff_landmarks AS patient_post_cutoff_landmarks,
            l.* EXCLUDE (landmark_id, person_id, landmark_date)
        FROM '{input_table_or_path}' l
        JOIN _pt_split_assignments s ON l.person_id = s.person_id
        WHERE (s.split = 'test' AND l.landmark_date >= '{temporal_cutoff_date}'::DATE)
           OR (s.split IN ('train', 'val') AND l.landmark_date < '{temporal_cutoff_date}'::DATE)
    """)

    return view_name


def generate_splits_dataset(
    input_parquet: str,
    output_parquet: str,
    temporal_cutoff_date: str = "2016-01-01",
    train_ratio: float = 0.70,
    random_seed: int = 42
) -> Dict[str, Any]:
    """
    Executes split generation and writes the split-assigned dataset to parquet.
    """
    os.makedirs(os.path.dirname(output_parquet), exist_ok=True)
    con = duckdb.connect()

    print(f"Generating splits for {input_parquet}...")
    view_name = assign_patient_splits(
        con=con,
        input_table_or_path=input_parquet,
        temporal_cutoff_date=temporal_cutoff_date,
        train_ratio=train_ratio,
        random_seed=random_seed
    )

    # Write split table to parquet
    con.execute(f"""
        COPY (SELECT * FROM {view_name} ORDER BY landmark_date, person_id) 
        TO '{output_parquet}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)
    print(f"Saved split dataset to {output_parquet}")

    # Gather split statistics
    stats = con.execute(f"""
        SELECT 
            split,
            count(DISTINCT person_id) AS n_patients,
            count(*) AS n_landmarks,
            min(landmark_date) AS min_landmark_date,
            max(landmark_date) AS max_landmark_date
        FROM '{output_parquet}'
        GROUP BY split
        ORDER BY split
    """).fetchall()

    total_pts = con.execute(f"SELECT count(DISTINCT person_id) FROM '{input_parquet}'").fetchone()[0]
    total_lms = con.execute(f"SELECT count(*) FROM '{input_parquet}'").fetchone()[0]
    retained_lms = con.execute(f"SELECT count(*) FROM '{output_parquet}'").fetchone()[0]

    summary = {
        "input_parquet": input_parquet,
        "output_parquet": output_parquet,
        "temporal_cutoff_date": temporal_cutoff_date,
        "train_ratio": train_ratio,
        "random_seed": random_seed,
        "raw_total_patients": total_pts,
        "raw_total_landmarks": total_lms,
        "retained_landmarks": retained_lms,
        "dropped_minority_landmarks": total_lms - retained_lms,
        "splits": {
            row[0]: {
                "patients": row[1],
                "landmarks": row[2],
                "min_date": str(row[3]),
                "max_date": str(row[4])
            }
            for row in stats
        }
    }

    return summary


def profile_split_characteristics(
    split_parquet: str,
    target_columns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Profiles class balance, patient demographic distributions, and landmark counts across splits.
    """
    con = duckdb.connect()

    if target_columns is None:
        cols = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM '{split_parquet}'").fetchall()]
        target_columns = sorted([c for c in cols if c.startswith("target_")])

    # 1. Overall split counts
    split_counts = con.execute(f"""
        SELECT 
            split,
            count(DISTINCT person_id) AS n_patients,
            count(*) AS n_landmarks,
            min(landmark_date) AS min_landmark_date,
            max(landmark_date) AS max_landmark_date,
            avg(age_at_landmark) AS mean_age,
            sum(CASE WHEN gender_concept_id = 8507 THEN 1 ELSE 0 END) AS n_male_lm,
            sum(CASE WHEN gender_concept_id = 8532 THEN 1 ELSE 0 END) AS n_female_lm
        FROM '{split_parquet}'
        GROUP BY split
        ORDER BY split
    """).fetchall()

    splits_summary = {}
    for r in split_counts:
        splits_summary[r[0]] = {
            "n_patients": r[1],
            "n_landmarks": r[2],
            "min_date": str(r[3]),
            "max_date": str(r[4]),
            "mean_age": round(float(r[5]), 2) if r[5] is not None else None,
            "male_landmarks": r[6],
            "female_landmarks": r[7]
        }

    # 2. Target incidence and imbalance per split
    target_stats = {}
    for tgt in target_columns:
        res = con.execute(f"""
            SELECT 
                split,
                count(*) AS total_lm,
                sum({tgt}) AS pos_lm
            FROM '{split_parquet}'
            GROUP BY split
            ORDER BY split
        """).fetchall()
        
        target_stats[tgt] = {
            r[0]: {
                "total": r[1],
                "positive": int(r[2]) if r[2] is not None else 0,
                "prevalence_pct": round(float(r[2] / r[1] * 100), 4) if r[1] > 0 and r[2] is not None else 0.0
            }
            for r in res
        }

    return {
        "split_parquet": split_parquet,
        "splits_summary": splits_summary,
        "target_stats": target_stats
    }
