"""
Phase 3: Outcome Label Construction Module.
Computes future incident comorbidity labels for candidate landmarks.
Enforces core clinical prediction requirements:
1. Feature state at T contains ONLY diagnoses with condition_start_date <= T.
2. Outcome window is strictly (T, T + H] (default H = 365 days).
3. Pre-existing conditions present on or before T are masked (cannot be positive labels).
4. Newly diagnosed conditions in (T, T + H] receive label = 1.
5. Incomplete future observation is tracked via future_observation_complete flag.
6. Analyzes empirical incidence across all candidate condition concepts to select target space K.
Uses high-performance vectorized DuckDB list functions.
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

from src.data.loader import OMOPDataLoader
from src.data.landmarks import select_landmarks
from src.data.timeline import get_condition_name, get_visit_name


def analyze_disease_incidence(
    con: duckdb.DuckDBPyConnection,
    cohort_view: str = "cohort_a_inpatient_ed",
    horizon_days: int = 365
) -> List[Dict[str, Any]]:
    """
    Computes incidence statistics for all condition concepts observed in the landmark cohort.
    For each candidate condition concept:
    - total_cohort_landmarks
    - pre_existing_landmarks (where condition was already present at T -> excluded from target)
    - at_risk_landmarks (total - pre_existing)
    - incident_positive_landmarks (new onset in (T, T + H] and NOT pre-existing)
    - incident_rate_pct (incident_positives / at_risk * 100)
    - unique_positive_patients
    """
    print(f"Computing disease incidence across {cohort_view} (H={horizon_days}d)...")

    # Step 1: Base deduplicated conditions
    con.execute("""
        CREATE OR REPLACE TEMP VIEW dedup_cond_base AS
        SELECT 
            person_id,
            condition_occurrence_id,
            ANY_VALUE(condition_concept_id) AS condition_concept_id,
            ANY_VALUE(condition_source_value) AS condition_source_value,
            MIN(CAST(condition_start_date AS DATE)) AS condition_start_date
        FROM condition_occurrence
        GROUP BY person_id, condition_occurrence_id;
    """)

    # Step 2: Compute incident counts per concept in DuckDB using full-observation landmarks
    incidence_query = f"""
        WITH target_landmarks AS (
            SELECT 
                person_id,
                visit_occurrence_id,
                landmark_id,
                landmark_date,
                future_window_start,
                future_window_end
            FROM {cohort_view}
            WHERE future_observation_complete = 1
        ),
        landmark_pre_conditions AS (
            SELECT 
                l.person_id,
                l.visit_occurrence_id,
                c.condition_concept_id
            FROM target_landmarks l
            JOIN dedup_cond_base c 
                ON l.person_id = c.person_id 
                AND c.condition_start_date <= l.landmark_date
            GROUP BY l.person_id, l.visit_occurrence_id, c.condition_concept_id
        ),
        landmark_future_conditions AS (
            SELECT 
                l.person_id,
                l.visit_occurrence_id,
                c.condition_concept_id
            FROM target_landmarks l
            JOIN dedup_cond_base c 
                ON l.person_id = c.person_id 
                AND c.condition_start_date > l.landmark_date 
                AND c.condition_start_date <= l.future_window_end
            GROUP BY l.person_id, l.visit_occurrence_id, c.condition_concept_id
        ),
        concept_summary AS (
            SELECT 
                fc.condition_concept_id,
                COUNT(*) AS raw_future_event_count,
                -- Incident positive: appears in future window AND NOT in pre-landmark history
                COUNT(CASE WHEN pc.condition_concept_id IS NULL THEN 1 END) AS incident_positive_landmarks,
                COUNT(DISTINCT CASE WHEN pc.condition_concept_id IS NULL THEN fc.person_id END) AS unique_incident_positive_patients
            FROM landmark_future_conditions fc
            LEFT JOIN landmark_pre_conditions pc 
                ON fc.person_id = pc.person_id 
                AND fc.visit_occurrence_id = pc.visit_occurrence_id 
                AND fc.condition_concept_id = pc.condition_concept_id
            GROUP BY fc.condition_concept_id
        ),
        pre_summary AS (
            SELECT 
                pc.condition_concept_id,
                COUNT(*) AS pre_existing_landmarks
            FROM landmark_pre_conditions pc
            GROUP BY pc.condition_concept_id
        )
        SELECT 
            c.condition_concept_id,
            ANY_VALUE(c.condition_source_value) AS sample_source_value,
            (SELECT COUNT(*) FROM target_landmarks) AS total_landmarks_evaluated,
            COALESCE(ps.pre_existing_landmarks, 0) AS pre_existing_landmarks,
            ((SELECT COUNT(*) FROM target_landmarks) - COALESCE(ps.pre_existing_landmarks, 0)) AS at_risk_landmarks,
            COALESCE(cs.incident_positive_landmarks, 0) AS incident_positive_landmarks,
            COALESCE(cs.unique_incident_positive_patients, 0) AS unique_incident_patients,
            ROUND(COALESCE(cs.incident_positive_landmarks, 0) * 100.0 / NULLIF(((SELECT COUNT(*) FROM target_landmarks) - COALESCE(ps.pre_existing_landmarks, 0)), 0), 3) AS incidence_rate_pct,
            ROUND(COALESCE(cs.incident_positive_landmarks, 0) * 100.0 / (SELECT COUNT(*) FROM target_landmarks), 3) AS population_positive_rate_pct
        FROM dedup_cond_base c
        LEFT JOIN concept_summary cs ON c.condition_concept_id = cs.condition_concept_id
        LEFT JOIN pre_summary ps ON c.condition_concept_id = ps.condition_concept_id
        WHERE c.condition_concept_id != 0
        GROUP BY c.condition_concept_id, cs.incident_positive_landmarks, cs.unique_incident_positive_patients, ps.pre_existing_landmarks
        ORDER BY incident_positive_landmarks DESC, unique_incident_patients DESC;
    """

    rel = con.execute(incidence_query)
    cols = [desc[0] for desc in rel.description]
    rows = rel.fetchall()

    results = []
    for r in rows:
        d = dict(zip(cols, r))
        d["condition_name"] = get_condition_name(d["condition_concept_id"], d["sample_source_value"])
        results.append(d)

    return results


def select_target_disease_space(
    incidence_results: List[Dict[str, Any]],
    min_positive_landmarks: int = 100,
    min_positive_patients: int = 50
) -> List[Dict[str, Any]]:
    """
    Selects the target disease space K based on empirical positive counts.
    """
    selected = [
        r for r in incidence_results
        if r["incident_positive_landmarks"] >= min_positive_landmarks
        and r["unique_incident_patients"] >= min_positive_patients
    ]
    return selected


def build_prediction_label_table(
    con: duckdb.DuckDBPyConnection,
    target_concepts: List[int],
    cohort_view: str = "cohort_b_general",
    output_table_name: str = "prediction_landmarks_table",
    output_parquet: Optional[str] = "data/parquet/prediction_landmarks.parquet"
) -> str:
    """
    Builds the complete prediction-label dataset with target_<concept_id> columns.
    Enforces multi-label binarization:
    - target_<concept_id> = 1 IF diagnosed in (T, T + H] AND NOT diagnosed on or before T.
    - target_<concept_id> = 0 IF not diagnosed in (T, T + H] OR already diagnosed on or before T.
    """
    print(f"Building prediction label table with {len(target_concepts)} target disease columns on {cohort_view}...")

    # Build vectorized list_contains expressions for each target disease
    target_col_exprs = []
    for cid in target_concepts:
        col_name = f"target_{cid}"
        expr = f"""
            CASE 
                WHEN list_contains(ca.fut_cond_ids, {cid}) AND NOT list_contains(ca.pre_cond_ids, {cid}) THEN 1 
                ELSE 0 
            END AS {col_name}
        """
        target_col_exprs.append(expr)

    # 1. Aggregate pre-landmark conditions and future outcome conditions using integer composite keys
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE landmark_condition_aggregates AS
        WITH l_pre AS (
            SELECT 
                l.person_id,
                l.visit_occurrence_id,
                LIST(DISTINCT c.condition_concept_id) FILTER (WHERE c.condition_concept_id IS NOT NULL AND c.condition_concept_id != 0) AS pre_cond_ids
            FROM {cohort_view} l
            JOIN dedup_cond_base c 
                ON l.person_id = c.person_id AND c.condition_start_date <= l.landmark_date
            GROUP BY l.person_id, l.visit_occurrence_id
        ),
        l_fut AS (
            SELECT 
                l.person_id,
                l.visit_occurrence_id,
                LIST(DISTINCT c.condition_concept_id) FILTER (WHERE c.condition_concept_id IS NOT NULL AND c.condition_concept_id != 0) AS fut_cond_ids
            FROM {cohort_view} l
            JOIN dedup_cond_base c 
                ON l.person_id = c.person_id 
                AND c.condition_start_date > l.landmark_date 
                AND c.condition_start_date <= l.future_window_end
            GROUP BY l.person_id, l.visit_occurrence_id
        )
        SELECT 
            l.person_id,
            l.visit_occurrence_id,
            COALESCE(p.pre_cond_ids, []) AS pre_cond_ids,
            COALESCE(f.fut_cond_ids, []) AS fut_cond_ids
        FROM {cohort_view} l
        LEFT JOIN l_pre p ON l.person_id = p.person_id AND l.visit_occurrence_id = p.visit_occurrence_id
        LEFT JOIN l_fut f ON l.person_id = f.person_id AND l.visit_occurrence_id = f.visit_occurrence_id;
    """)

    # 2. Materialize prediction table
    select_sql = f"""
        CREATE OR REPLACE TEMP TABLE {output_table_name} AS
        SELECT 
            l.person_id,
            l.landmark_id,
            l.visit_occurrence_id,
            l.visit_concept_id,
            l.visit_category,
            l.is_inpatient_or_ed,
            l.landmark_date,
            l.observation_start,
            l.observation_end,
            l.age_at_landmark,
            l.gender_concept_id,
            l.gender_source_value,
            l.race_source_value,
            l.ethnicity_source_value,
            l.prior_obs_days,
            l.future_obs_days,
            l.future_window_start,
            l.future_window_end,
            l.future_observation_complete,
            l.existing_diagnosis_count,
            ca.pre_cond_ids AS pre_landmark_condition_ids,
            ca.fut_cond_ids AS future_window_condition_ids,
            {', '.join(target_col_exprs)}
        FROM {cohort_view} l
        JOIN landmark_condition_aggregates ca 
            ON l.person_id = ca.person_id AND l.visit_occurrence_id = ca.visit_occurrence_id;
    """
    con.execute(select_sql)

    if output_parquet:
        os.makedirs(os.path.dirname(os.path.abspath(output_parquet)), exist_ok=True)
        clean_out = output_parquet.replace("\\", "/")
        print(f"Exporting prediction landmarks dataset to Parquet: {output_parquet}...")
        con.execute(f"COPY {output_table_name} TO '{clean_out}' (FORMAT PARQUET, COMPRESSION ZSTD);")
        size_mb = os.path.getsize(output_parquet) / 1024 / 1024
        print(f"Dataset successfully created ({size_mb:.2f} MB)")

    return output_parquet or output_table_name


if __name__ == "__main__":
    con = select_landmarks()
    incidence = analyze_disease_incidence(con, "cohort_a_inpatient_ed")
    selected_targets = select_target_disease_space(incidence, min_positive_landmarks=100)
    print(f"Evaluated {len(incidence)} candidate conditions. Selected {len(selected_targets)} targets at threshold >= 100.")
    print("Top 10 targets:")
    for t in selected_targets[:10]:
        print(f"  {t['condition_name']} (ID: {t['condition_concept_id']}): {t['incident_positive_landmarks']:,} positive landmarks ({t['unique_incident_patients']:,} patients, rate: {t['incidence_rate_pct']}%)")
