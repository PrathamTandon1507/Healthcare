"""
Phase 3: Landmark Selection Module.
Constructs deterministic patient landmarks anchored at index encounter end dates.
Enforces Phase 2 eligibility criteria:
- Sufficient prior observation (>= 365 days)
- >= 1 condition diagnosis recorded on or before landmark date T
- Annotates complete future observation coverage (>= H days) vs. censored landmarks.
Constructs both Cohort A (Inpatient/ED) and Cohort B (General Encounters).
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
import duckdb

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.data.loader import OMOPDataLoader
from src.data.timeline import build_patient_timelines, get_visit_name


def select_landmarks(
    source_dir: str = "synthea100k",
    parquet_dir: str = "data/parquet",
    horizon_days: int = 365,
    min_prior_obs_days: int = 365,
    min_prior_conditions: int = 1
) -> duckdb.DuckDBPyConnection:
    """
    Constructs the eligible landmark views in DuckDB from deduplicated patient timelines.
    """
    # Ensure patient timelines parquet exists
    build_patient_timelines(source_dir=source_dir, parquet_dir=parquet_dir)
    
    loader = OMOPDataLoader(source_dir=source_dir, parquet_dir=parquet_dir)
    con = loader.get_connection()

    print(f"Extracting candidate landmarks (horizon H={horizon_days}d, prior_obs>={min_prior_obs_days}d)...")

    # 1. Base candidate encounters from patient_timelines
    # In OMOP, landmark time T is the visit_end_date of the index encounter.
    # A landmark ID is deterministically formed as: {person_id}_{visit_occurrence_id}_{visit_end_date}
    con.execute(f"""
        CREATE OR REPLACE TEMP VIEW all_candidate_landmarks AS
        SELECT 
            person_id,
            visit_occurrence_id,
            CONCAT(CAST(person_id AS VARCHAR), '_', CAST(visit_occurrence_id AS VARCHAR), '_', CAST(visit_end_date AS VARCHAR)) AS landmark_id,
            visit_concept_id,
            visit_start_date,
            visit_end_date AS landmark_date,
            visit_duration_days,
            age_at_visit AS age_at_landmark,
            gender_concept_id,
            gender_source_value,
            year_of_birth,
            birth_datetime,
            race_source_value,
            ethnicity_source_value,
            obs_start_date AS observation_start,
            obs_end_date AS observation_end,
            prior_obs_days,
            future_obs_days,
            visit_sequence_num,
            -- Future outcome window bounds
            (visit_end_date + INTERVAL '1 day') AS future_window_start,
            (visit_end_date + INTERVAL '{horizon_days} days') AS future_window_end,
            -- Future observation completeness flag (1 if future_obs_days >= horizon_days, else 0 = censored)
            CASE WHEN future_obs_days >= {horizon_days} THEN 1 ELSE 0 END AS future_observation_complete,
            -- Cohort classification
            CASE 
                WHEN visit_concept_id = 9201 THEN 'inpatient'
                WHEN visit_concept_id = 9203 THEN 'emergency'
                ELSE 'outpatient_other'
            END AS visit_category,
            CASE 
                WHEN visit_concept_id IN (9201, 9203) THEN 1 
                ELSE 0 
            END AS is_inpatient_or_ed
        FROM read_parquet('data/parquet/patient_timelines.parquet');
    """)

    # 2. Count distinct historical conditions on or before landmark date T
    con.execute("""
        CREATE OR REPLACE TEMP VIEW landmark_pre_condition_counts AS
        SELECT 
            l.landmark_id,
            COUNT(DISTINCT c.condition_concept_id) AS existing_diagnosis_count
        FROM all_candidate_landmarks l
        LEFT JOIN (
            SELECT person_id, condition_occurrence_id, ANY_VALUE(condition_concept_id) AS condition_concept_id, MIN(CAST(condition_start_date AS DATE)) AS condition_start_date
            FROM condition_occurrence
            GROUP BY person_id, condition_occurrence_id
        ) c ON l.person_id = c.person_id AND c.condition_start_date <= l.landmark_date
        GROUP BY l.landmark_id;
    """)

    # 3. Assemble annotated eligible landmarks view
    con.execute(f"""
        CREATE OR REPLACE TEMP VIEW eligible_landmarks_view AS
        SELECT 
            l.*,
            COALESCE(pcc.existing_diagnosis_count, 0) AS existing_diagnosis_count
        FROM all_candidate_landmarks l
        JOIN landmark_pre_condition_counts pcc ON l.landmark_id = pcc.landmark_id
        WHERE l.prior_obs_days >= {min_prior_obs_days}
          AND COALESCE(pcc.existing_diagnosis_count, 0) >= {min_prior_conditions};
    """)

    # 4. Cohort A (Inpatient / ED) and Cohort B (General) views
    con.execute("""
        CREATE OR REPLACE TEMP VIEW cohort_a_inpatient_ed AS
        SELECT *
        FROM eligible_landmarks_view
        WHERE is_inpatient_or_ed = 1;
    """)

    con.execute("""
        CREATE OR REPLACE TEMP VIEW cohort_b_general AS
        SELECT *
        FROM eligible_landmarks_view;
    """)

    return con


def get_cohort_characterization_stats(con: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
    """
    Computes summary characterization metrics for Cohort A (Inpatient/ED) and Cohort B (General).
    """
    stats = {}

    for cohort_name, table_view in [("Cohort_A_Inpatient_ED", "cohort_a_inpatient_ed"), ("Cohort_B_General", "cohort_b_general")]:
        overview = con.execute(f"""
            SELECT 
                COUNT(*) AS total_eligible_landmarks,
                COUNT(DISTINCT person_id) AS unique_patients,
                COUNT(DISTINCT visit_occurrence_id) AS unique_visits,
                COUNT(CASE WHEN future_observation_complete = 1 THEN 1 END) AS full_future_obs_landmarks,
                COUNT(CASE WHEN future_observation_complete = 0 THEN 1 END) AS censored_landmarks,
                AVG(prior_obs_days) / 365.25 AS mean_prior_obs_years,
                MEDIAN(prior_obs_days) / 365.25 AS median_prior_obs_years,
                AVG(future_obs_days) / 365.25 AS mean_future_obs_years,
                MEDIAN(future_obs_days) / 365.25 AS median_future_obs_years,
                AVG(age_at_landmark) AS mean_age,
                MEDIAN(age_at_landmark) AS median_age,
                AVG(existing_diagnosis_count) AS mean_existing_diagnoses,
                MEDIAN(existing_diagnosis_count) AS median_existing_diagnoses,
                MIN(landmark_date) AS earliest_landmark,
                MAX(landmark_date) AS latest_landmark
            FROM {table_view};
        """).df().iloc[0].to_dict() if False else None

        # DuckDB native query to dict
        rel = con.execute(f"""
            SELECT 
                COUNT(*) AS total_eligible_landmarks,
                COUNT(DISTINCT person_id) AS unique_patients,
                COUNT(DISTINCT visit_occurrence_id) AS unique_visits,
                COUNT(CASE WHEN future_observation_complete = 1 THEN 1 END) AS full_future_obs_landmarks,
                COUNT(CASE WHEN future_observation_complete = 0 THEN 1 END) AS censored_landmarks,
                AVG(prior_obs_days) / 365.25 AS mean_prior_obs_years,
                MEDIAN(prior_obs_days) / 365.25 AS median_prior_obs_years,
                AVG(future_obs_days) / 365.25 AS mean_future_obs_years,
                MEDIAN(future_obs_days) / 365.25 AS median_future_obs_years,
                AVG(age_at_landmark) AS mean_age,
                MEDIAN(age_at_landmark) AS median_age,
                AVG(existing_diagnosis_count) AS mean_existing_diagnoses,
                MEDIAN(existing_diagnosis_count) AS median_existing_diagnoses,
                MIN(landmark_date) AS earliest_landmark,
                MAX(landmark_date) AS latest_landmark
            FROM {table_view};
        """)
        cols = [desc[0] for desc in rel.description]
        overview = dict(zip(cols, rel.fetchone()))

        # Distribution of landmarks per patient
        multiplicity = con.execute(f"""
            WITH p_lm AS (
                SELECT person_id, COUNT(*) AS n_landmarks
                FROM {table_view}
                GROUP BY person_id
            )
            SELECT 
                COUNT(CASE WHEN n_landmarks = 1 THEN 1 END) AS patients_with_1_landmark,
                COUNT(CASE WHEN n_landmarks > 1 THEN 1 END) AS patients_with_gt_1_landmarks,
                MIN(n_landmarks) AS min_landmarks_per_patient,
                MAX(n_landmarks) AS max_landmarks_per_patient,
                AVG(n_landmarks) AS mean_landmarks_per_patient,
                MEDIAN(n_landmarks) AS median_landmarks_per_patient,
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY n_landmarks) AS p25_landmarks_per_patient,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY n_landmarks) AS p75_landmarks_per_patient,
                PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY n_landmarks) AS p90_landmarks_per_patient
            FROM p_lm;
        """)
        m_cols = [desc[0] for desc in multiplicity.description]
        multiplicity_dict = dict(zip(m_cols, multiplicity.fetchone()))

        stats[cohort_name] = {
            "overview": {k: round(float(v), 2) if isinstance(v, (float, int)) and not str(k).startswith("earliest") and not str(k).startswith("latest") else str(v) for k, v in overview.items()},
            "multiplicity": {k: round(float(v), 2) if isinstance(v, float) else int(v) for k, v in multiplicity_dict.items()}
        }

    return stats


if __name__ == "__main__":
    con = select_landmarks()
    stats = get_cohort_characterization_stats(con)
    print("Landmark selection complete. Statistics:")
    print(stats)
