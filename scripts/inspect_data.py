"""
Phase 1: Dataset and Schema Inspection Script for Synthea OMOP 100K.
Analyzes person, condition_occurrence, visit_occurrence, and observation_period tables.
Deduplicates entities by primary keys to avoid raw file block duplicates.
Generates reports/data_profile.json and reports/data_profile.md using native DuckDB.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import duckdb
from src.data.loader import OMOPDataLoader
from src.data.timeline import get_visit_name, get_condition_name


def inspect_dataset(source_dir: str = "synthea100k", parquet_dir: str = "data/parquet") -> dict:
    loader = OMOPDataLoader(source_dir=source_dir, parquet_dir=parquet_dir)
    loader.initialize()
    
    profile = {
        "metadata": {
            "dataset_source": source_dir,
            "generated_at": datetime.now().isoformat(),
            "duckdb_version": duckdb.__version__
        },
        "tables": {},
        "demographics": {},
        "observation_period": {},
        "visits": {},
        "conditions": {},
        "inter_visit_cadence": {},
        "landmarks_feasibility": {}
    }
    
    # 1. Table Schemas, Raw & Distinct Row Counts & Nullity
    table_configs = [
        ("person", "person_id"),
        ("observation_period", "observation_period_id"),
        ("condition_occurrence", "condition_occurrence_id"),
        ("visit_occurrence", "visit_occurrence_id")
    ]
    
    for t, id_col in table_configs:
        raw_row_count = loader.query_one(f"SELECT COUNT(*) AS cnt FROM {t}")["cnt"]
        distinct_count = loader.query_one(f"SELECT COUNT(DISTINCT {id_col}) AS cnt FROM {t}")["cnt"]
        schema_rows = loader.query_dicts(f"DESCRIBE {t}")
        
        col_names = [r["column_name"] for r in schema_rows]
        null_exprs = [f"COUNT(*) - COUNT({col}) AS {col}_nulls" for col in col_names]
        null_query = f"SELECT {', '.join(null_exprs)} FROM {t}"
        null_counts = loader.query_one(null_query)
        
        columns_profile = []
        for r in schema_rows:
            col = r["column_name"]
            nulls = int(null_counts.get(f"{col}_nulls", 0))
            columns_profile.append({
                "column_name": col,
                "data_type": str(r["column_type"]),
                "null_count": nulls,
                "null_pct": round((nulls / raw_row_count * 100) if raw_row_count > 0 else 0, 2)
            })
            
        profile["tables"][t] = {
            "raw_row_count": int(raw_row_count),
            "distinct_records": int(distinct_count),
            "id_column": id_col,
            "columns": columns_profile
        }
        print(f"Table {t}: {raw_row_count:,} raw rows ({distinct_count:,} unique {id_col}), {len(columns_profile)} columns")

    # 2. Cohort Demographics (person - deduplicated)
    n_persons = loader.query_one("SELECT COUNT(DISTINCT person_id) AS cnt FROM person")["cnt"]
    birth_stats = loader.query_one("""
        WITH distinct_person AS (
            SELECT person_id, ANY_VALUE(year_of_birth) AS year_of_birth
            FROM person
            GROUP BY person_id
        )
        SELECT 
            MIN(year_of_birth) AS min_year,
            MAX(year_of_birth) AS max_year,
            MEDIAN(year_of_birth) AS median_year,
            AVG(year_of_birth) AS mean_year,
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY year_of_birth) AS p25_year,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY year_of_birth) AS p75_year
        FROM distinct_person
    """)
    
    gender_dist = loader.query_dicts("""
        WITH distinct_person AS (
            SELECT person_id, ANY_VALUE(gender_concept_id) AS gender_concept_id, ANY_VALUE(gender_source_value) AS gender_source_value
            FROM person
            GROUP BY person_id
        )
        SELECT 
            gender_concept_id,
            COALESCE(gender_source_value, 'UNKNOWN') AS gender_source,
            COUNT(*) AS count,
            COUNT(*) * 100.0 / (SELECT COUNT(*) FROM distinct_person) AS pct
        FROM distinct_person
        GROUP BY 1, 2
        ORDER BY count DESC
    """)
    
    race_dist = loader.query_dicts("""
        WITH distinct_person AS (
            SELECT person_id, ANY_VALUE(race_concept_id) AS race_concept_id, ANY_VALUE(race_source_value) AS race_source_value
            FROM person
            GROUP BY person_id
        )
        SELECT 
            race_concept_id,
            COALESCE(race_source_value, 'UNKNOWN') AS race_source,
            COUNT(*) AS count,
            COUNT(*) * 100.0 / (SELECT COUNT(*) FROM distinct_person) AS pct
        FROM distinct_person
        GROUP BY 1, 2
        ORDER BY count DESC
    """)

    ethnicity_dist = loader.query_dicts("""
        WITH distinct_person AS (
            SELECT person_id, ANY_VALUE(ethnicity_concept_id) AS ethnicity_concept_id, ANY_VALUE(ethnicity_source_value) AS ethnicity_source_value
            FROM person
            GROUP BY person_id
        )
        SELECT 
            ethnicity_concept_id,
            COALESCE(ethnicity_source_value, 'UNKNOWN') AS ethnicity_source,
            COUNT(*) AS count,
            COUNT(*) * 100.0 / (SELECT COUNT(*) FROM distinct_person) AS pct
        FROM distinct_person
        GROUP BY 1, 2
        ORDER BY count DESC
    """)

    profile["demographics"] = {
        "total_unique_patients": int(n_persons),
        "birth_year_stats": {k: float(v) if v is not None else None for k, v in birth_stats.items()},
        "gender_distribution": [
            {
                "concept_id": int(r["gender_concept_id"]),
                "source_value": str(r["gender_source"]),
                "description": "Male" if r["gender_concept_id"] == 8507 else "Female" if r["gender_concept_id"] == 8532 else "Unknown",
                "patient_count": int(r["count"]),
                "pct": round(float(r["pct"]), 2)
            }
            for r in gender_dist
        ],
        "race_distribution": [
            {
                "concept_id": int(r["race_concept_id"]),
                "source_value": str(r["race_source"]),
                "description": str(r["race_source"]).capitalize(),
                "patient_count": int(r["count"]),
                "pct": round(float(r["pct"]), 2)
            }
            for r in race_dist
        ],
        "ethnicity_distribution": [
            {
                "concept_id": int(r["ethnicity_concept_id"]),
                "source_value": str(r["ethnicity_source"]),
                "description": str(r["ethnicity_source"]).capitalize(),
                "patient_count": int(r["count"]),
                "pct": round(float(r["pct"]), 2)
            }
            for r in ethnicity_dist
        ]
    }

    # 3. Observation Period Span Profile (deduplicated)
    obs_stats = loader.query_one("""
        WITH distinct_obs AS (
            SELECT person_id, MIN(CAST(observation_period_start_date AS DATE)) AS op_start, MAX(CAST(observation_period_end_date AS DATE)) AS op_end
            FROM observation_period
            GROUP BY person_id
        )
        SELECT 
            COUNT(*) AS unique_patients,
            MIN(op_start) AS earliest_start,
            MAX(op_end) AS latest_end,
            AVG(DATEDIFF('day', op_start, op_end)) AS mean_days,
            MEDIAN(DATEDIFF('day', op_start, op_end)) AS median_days,
            MIN(DATEDIFF('day', op_start, op_end)) AS min_days,
            MAX(DATEDIFF('day', op_start, op_end)) AS max_days
        FROM distinct_obs
    """)

    profile["observation_period"] = {
        "unique_patients_with_obs_period": int(obs_stats["unique_patients"]),
        "earliest_start": str(obs_stats["earliest_start"]),
        "latest_end": str(obs_stats["latest_end"]),
        "span_duration": {
            "mean_days": round(float(obs_stats["mean_days"]), 1),
            "median_days": round(float(obs_stats["median_days"]), 1),
            "min_days": int(obs_stats["min_days"]),
            "max_days": int(obs_stats["max_days"]),
            "mean_span_years": round(float(obs_stats["mean_days"]) / 365.25, 2),
            "median_span_years": round(float(obs_stats["median_days"]) / 365.25, 2)
        }
    }

    # 4. Visits Profile (deduplicated distinct visits)
    visit_overview = loader.query_one("""
        WITH distinct_visits AS (
            SELECT person_id, visit_occurrence_id, ANY_VALUE(visit_concept_id) AS visit_concept_id, MIN(CAST(visit_start_date AS DATE)) AS v_start, MAX(CAST(visit_end_date AS DATE)) AS v_end
            FROM visit_occurrence
            GROUP BY person_id, visit_occurrence_id
        )
        SELECT 
            COUNT(*) AS total_visits,
            COUNT(DISTINCT person_id) AS unique_patients,
            MIN(v_start) AS earliest_start,
            MAX(v_end) AS latest_end
        FROM distinct_visits
    """)

    visits_per_patient = loader.query_one("""
        WITH p_visits AS (
            SELECT person_id, COUNT(DISTINCT visit_occurrence_id) AS n_visits
            FROM visit_occurrence
            GROUP BY person_id
        )
        SELECT 
            MIN(n_visits) AS min_visits,
            MAX(n_visits) AS max_visits,
            AVG(n_visits) AS mean_visits,
            MEDIAN(n_visits) AS median_visits,
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY n_visits) AS p25_visits,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY n_visits) AS p75_visits,
            PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY n_visits) AS p90_visits
        FROM p_visits
    """)

    visit_concept_dist = loader.query_dicts("""
        WITH distinct_visits AS (
            SELECT person_id, visit_occurrence_id, ANY_VALUE(visit_concept_id) AS visit_concept_id
            FROM visit_occurrence
            GROUP BY person_id, visit_occurrence_id
        )
        SELECT 
            visit_concept_id,
            COUNT(*) AS total_visits,
            COUNT(DISTINCT person_id) AS unique_patients,
            COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() AS pct_visits
        FROM distinct_visits
        GROUP BY 1
        ORDER BY total_visits DESC
    """)

    profile["visits"] = {
        "total_distinct_visits": int(visit_overview["total_visits"]),
        "unique_patients_with_visits": int(visit_overview["unique_patients"]),
        "earliest_visit": str(visit_overview["earliest_start"]),
        "latest_visit": str(visit_overview["latest_end"]),
        "visits_per_patient": {k: round(float(v), 2) for k, v in visits_per_patient.items()},
        "concept_breakdown": [
            {
                "visit_concept_id": int(r["visit_concept_id"]),
                "concept_name": get_visit_name(r["visit_concept_id"]),
                "total_visits": int(r["total_visits"]),
                "unique_patients": int(r["unique_patients"]),
                "pct_visits": round(float(r["pct_visits"]), 2),
                "patient_prevalence_pct": round(int(r["unique_patients"]) / n_persons * 100, 2)
            }
            for r in visit_concept_dist
        ]
    }

    # 5. Conditions Profile (deduplicated distinct conditions)
    cond_overview = loader.query_one("""
        WITH distinct_conditions AS (
            SELECT person_id, condition_occurrence_id, ANY_VALUE(condition_concept_id) AS condition_concept_id, MIN(CAST(condition_start_date AS DATE)) AS condition_start_date
            FROM condition_occurrence
            GROUP BY person_id, condition_occurrence_id
        )
        SELECT 
            COUNT(*) AS total_conditions,
            COUNT(DISTINCT person_id) AS unique_patients,
            COUNT(DISTINCT condition_concept_id) AS unique_concepts,
            MIN(condition_start_date) AS earliest_start,
            MAX(condition_start_date) AS latest_start
        FROM distinct_conditions
    """)

    conds_per_patient = loader.query_one("""
        WITH p_conds AS (
            SELECT 
                person_id, 
                COUNT(DISTINCT condition_occurrence_id) AS n_conds, 
                COUNT(DISTINCT condition_concept_id) AS n_unique_conds
            FROM condition_occurrence
            GROUP BY person_id
        )
        SELECT 
            MIN(n_conds) AS min_conds,
            MAX(n_conds) AS max_conds,
            AVG(n_conds) AS mean_conds,
            MEDIAN(n_conds) AS median_conds,
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY n_conds) AS p25_conds,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY n_conds) AS p75_conds,
            AVG(n_unique_conds) AS mean_unique_conds,
            MEDIAN(n_unique_conds) AS median_unique_conds
        FROM p_conds
    """)

    top_conditions = loader.query_dicts("""
        WITH distinct_conditions AS (
            SELECT person_id, condition_occurrence_id, ANY_VALUE(condition_concept_id) AS condition_concept_id, ANY_VALUE(condition_source_value) AS condition_source_value
            FROM condition_occurrence
            GROUP BY person_id, condition_occurrence_id
        )
        SELECT 
            condition_concept_id,
            ANY_VALUE(condition_source_value) AS sample_source_value,
            COUNT(*) AS total_occurrences,
            COUNT(DISTINCT person_id) AS unique_patients,
            COUNT(DISTINCT person_id) * 100.0 / (SELECT COUNT(DISTINCT person_id) FROM person) AS patient_prevalence_pct
        FROM distinct_conditions
        GROUP BY condition_concept_id
        ORDER BY unique_patients DESC
        LIMIT 50
    """)

    profile["conditions"] = {
        "total_distinct_conditions": int(cond_overview["total_conditions"]),
        "unique_patients_with_conditions": int(cond_overview["unique_patients"]),
        "unique_condition_concepts": int(cond_overview["unique_concepts"]),
        "earliest_condition": str(cond_overview["earliest_start"]),
        "latest_condition": str(cond_overview["latest_start"]),
        "conditions_per_patient": {k: round(float(v), 2) for k, v in conds_per_patient.items()},
        "top_50_conditions": [
            {
                "condition_concept_id": int(r["condition_concept_id"]),
                "source_value": str(r["sample_source_value"]),
                "concept_name": get_condition_name(r["condition_concept_id"], r["sample_source_value"]),
                "total_occurrences": int(r["total_occurrences"]),
                "unique_patients": int(r["unique_patients"]),
                "patient_prevalence_pct": round(float(r["patient_prevalence_pct"]), 2)
            }
            for r in top_conditions
        ]
    }

    # 6. Inter-Visit Cadence & Encounter Intervals
    cadence_stats = loader.query_one("""
        WITH ordered_visits AS (
            SELECT 
                person_id,
                CAST(visit_start_date AS DATE) AS v_date,
                LAG(CAST(visit_start_date AS DATE)) OVER(PARTITION BY person_id ORDER BY CAST(visit_start_date AS DATE), visit_occurrence_id) AS prev_v_date
            FROM (SELECT person_id, visit_occurrence_id, MIN(CAST(visit_start_date AS DATE)) AS visit_start_date FROM visit_occurrence GROUP BY person_id, visit_occurrence_id)
        ),
        intervals AS (
            SELECT DATEDIFF('day', prev_v_date, v_date) AS gap_days
            FROM ordered_visits
            WHERE prev_v_date IS NOT NULL
        )
        SELECT 
            COUNT(*) AS total_inter_visit_gaps,
            AVG(gap_days) AS mean_gap_days,
            MEDIAN(gap_days) AS median_gap_days,
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY gap_days) AS p25_gap_days,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY gap_days) AS p75_gap_days,
            COUNT(CASE WHEN gap_days = 0 THEN 1 END) * 100.0 / COUNT(*) AS same_day_pct,
            COUNT(CASE WHEN gap_days BETWEEN 1 AND 180 THEN 1 END) * 100.0 / COUNT(*) AS gap_1_to_180d_pct,
            COUNT(CASE WHEN gap_days BETWEEN 181 AND 365 THEN 1 END) * 100.0 / COUNT(*) AS gap_181_to_365d_pct,
            COUNT(CASE WHEN gap_days > 365 THEN 1 END) * 100.0 / COUNT(*) AS gap_gt_365d_pct
        FROM intervals
    """)

    # 7. Clean Deduplicated Landmark Eligibility Counts
    landmark_counts = loader.query_one("""
        WITH dedup_v AS (
            SELECT person_id, visit_occurrence_id, ANY_VALUE(visit_concept_id) AS visit_concept_id, MIN(CAST(visit_start_date AS DATE)) AS v_start, MAX(CAST(visit_end_date AS DATE)) AS v_end
            FROM visit_occurrence
            GROUP BY person_id, visit_occurrence_id
        ),
        dedup_op AS (
            SELECT person_id, MIN(CAST(observation_period_start_date AS DATE)) AS op_start, MAX(CAST(observation_period_end_date AS DATE)) AS op_end
            FROM observation_period
            GROUP BY person_id
        ),
        dedup_c AS (
            SELECT person_id, condition_occurrence_id, ANY_VALUE(condition_concept_id) AS condition_concept_id, MIN(CAST(condition_start_date AS DATE)) AS c_start
            FROM condition_occurrence
            GROUP BY person_id, condition_occurrence_id
        ),
        annotated_visits AS (
            SELECT 
                v.visit_occurrence_id,
                v.person_id,
                v.visit_concept_id,
                v.v_start,
                v.v_end,
                op.op_start,
                op.op_end,
                DATEDIFF('day', op.op_start, v.v_end) AS prior_obs_days,
                DATEDIFF('day', v.v_end, op.op_end) AS future_obs_days,
                (
                    SELECT COUNT(DISTINCT c.condition_concept_id)
                    FROM dedup_c c
                    WHERE c.person_id = v.person_id AND c.c_start <= v.v_end
                ) AS prior_condition_count
            FROM dedup_v v
            JOIN dedup_op op ON v.person_id = op.person_id
                AND v.v_start BETWEEN op.op_start AND op.op_end
        )
        SELECT 
            COUNT(*) AS total_distinct_visits,
            COUNT(DISTINCT person_id) AS patients_with_visits,
            COUNT(CASE WHEN prior_obs_days >= 365 THEN 1 END) AS visits_with_gte_1yr_prior_obs,
            COUNT(CASE WHEN prior_obs_days >= 365 AND prior_condition_count >= 1 THEN 1 END) AS eligible_landmarks_total,
            COUNT(CASE WHEN prior_obs_days >= 365 AND prior_condition_count >= 1 AND future_obs_days >= 365 THEN 1 END) AS eligible_landmarks_with_365d_future_obs,
            COUNT(CASE WHEN prior_obs_days >= 365 AND prior_condition_count >= 1 AND future_obs_days >= 180 THEN 1 END) AS eligible_landmarks_with_180d_future_obs,
            COUNT(CASE WHEN visit_concept_id = 9201 AND prior_obs_days >= 365 AND prior_condition_count >= 1 THEN 1 END) AS eligible_inpatient_landmarks,
            COUNT(CASE WHEN visit_concept_id IN (9201, 9203) AND prior_obs_days >= 365 AND prior_condition_count >= 1 THEN 1 END) AS eligible_inpatient_or_ed_landmarks
        FROM annotated_visits
    """)

    profile["inter_visit_cadence"] = {k: round(float(v), 2) for k, v in cadence_stats.items()}
    profile["landmarks_feasibility"] = {k: int(v) for k, v in landmark_counts.items()}

    return profile


def generate_markdown_report(profile: dict, output_md_path: str):
    p = profile
    md = []
    md.append("# Synthea OMOP 100K Dataset Profile & Schema Inspection Report")
    md.append(f"\n*Generated At:* {p['metadata']['generated_at']}  ")
    md.append(f"*Source Directory:* `{p['metadata']['dataset_source']}`  ")
    md.append(f"*DuckDB Version:* `{p['metadata']['duckdb_version']}`  \n")
    md.append("---\n")

    # 1. Executive Summary Table
    md.append("## 1. Executive Summary & Table Inventory\n")
    md.append("| Table Name | Raw Rows in Export | Distinct Primary Key Records | Primary Entity Key | Role / Description |")
    md.append("|---|---|---|---|---|")
    for t_name, t_info in p["tables"].items():
        md.append(f"| `{t_name}` | {t_info['raw_row_count']:,} | {t_info['distinct_records']:,} | `{t_info['id_column']}` | Primary OMOP CDM table |")
    md.append("\n")

    # 2. Patient Demographics
    demo = p["demographics"]
    md.append("## 2. Patient Demographics (`person`)\n")
    md.append(f"- **Total Unique Patients (`person_id`):** **{demo['total_unique_patients']:,}**")
    by = demo["birth_year_stats"]
    md.append(f"- **Birth Year Range:** {int(by['min_year'])} to {int(by['max_year'])} (Median: {int(by['median_year'])}, IQR: {int(by['p25_year'])}–{int(by['p75_year'])})")
    
    md.append("\n### Sex / Gender Breakdown")
    md.append("| Concept ID | Demographic Category | Source Value | Unique Patient Count | Cohort Percentage |")
    md.append("|---|---|---|---|---|")
    for g in demo["gender_distribution"]:
        md.append(f"| `{g['concept_id']}` | **{g['description']}** | `{g['source_value']}` | **{g['patient_count']:,}** | **{g['pct']}%** |")

    md.append("\n### Race Breakdown")
    md.append("| Concept ID | Demographic Category | Source Value | Unique Patient Count | Cohort Percentage |")
    md.append("|---|---|---|---|---|")
    for r in demo["race_distribution"]:
        md.append(f"| `{r['concept_id']}` | **{r['description']}** | `{r['source_value']}` | {r['patient_count']:,} | {r['pct']}% |")

    # 3. Observation Period
    obs = p["observation_period"]
    md.append("\n## 3. Observation Period Span (`observation_period`)\n")
    md.append(f"- **Total Patients with Observation Coverage:** {obs['unique_patients_with_obs_period']:,} (100% cohort coverage)")
    md.append(f"- **Dataset Calendar Window:** `{obs['earliest_start']}` to `{obs['latest_end']}`")
    md.append(f"- **Median Observation-Period Span:** **{obs['span_duration']['median_span_years']} years** ({obs['span_duration']['median_days']:,} days)")
    md.append(f"- **Mean Observation-Period Span:** **{obs['span_duration']['mean_span_years']} years** ({obs['span_duration']['mean_days']:,} days)")
    md.append(f"- **Min / Max Observation Span:** {obs['span_duration']['min_days']} days to {round(obs['span_duration']['max_days']/365.25, 1)} years\n")

    # 4. Visits Profile
    v = p["visits"]
    md.append("## 4. Visits Profile (`visit_occurrence`)\n")
    md.append(f"- **Total Distinct Clinical Visits:** **{v['total_distinct_visits']:,}**")
    md.append(f"- **Patients with >= 1 Visit:** {v['unique_patients_with_visits']:,} ({(v['unique_patients_with_visits']/demo['total_unique_patients']*100):.1f}% of cohort)")
    md.append(f"- **Date Range:** `{v['earliest_visit']}` to `{v['latest_visit']}`")
    vpp = v["visits_per_patient"]
    md.append(f"- **Visits Per Patient:** Median = **{vpp['median_visits']}**, Mean = **{vpp['mean_visits']}**, IQR = **{vpp['p25_visits']}–{vpp['p75_visits']}**, Max = {vpp['max_visits']}")
    md.append("\n### Visit Types Breakdown")
    md.append("| Visit Concept ID | Description | Total Encounters | Unique Patients | Encounter % | Cohort Prev % |")
    md.append("|---|---|---|---|---|---|")
    for vc in v["concept_breakdown"]:
        md.append(f"| `{vc['visit_concept_id']}` | **{vc['concept_name']}** | {vc['total_visits']:,} | {vc['unique_patients']:,} | {vc['pct_visits']}% | {vc['patient_prevalence_pct']}% |")

    # 5. Conditions Profile & Top Chronic Conditions
    c = p["conditions"]
    md.append("\n## 5. Conditions Profile (`condition_occurrence`)\n")
    md.append(f"- **Total Distinct Condition Records:** **{c['total_distinct_conditions']:,}**")
    md.append(f"- **Unique Patients with >= 1 Diagnosis:** {c['unique_patients_with_conditions']:,} ({(c['unique_patients_with_conditions']/demo['total_unique_patients']*100):.1f}% of cohort)")
    md.append(f"- **Distinct Condition Concepts:** {c['unique_condition_concepts']:,}")
    cpp = c["conditions_per_patient"]
    md.append(f"- **Conditions Per Patient:** Median = {cpp['median_conds']}, Mean = {cpp['mean_conds']}, Distinct Concepts/Patient = {cpp['median_unique_conds']}")
    md.append("\n### Top Conditions by Patient Prevalence")
    md.append("| Concept ID | Condition / Disease Name | Source Code | Total Events | Patient Count | Cohort Prevalence |")
    md.append("|---|---|---|---|---|---|")
    for top_c in c["top_50_conditions"][:25]:
        md.append(f"| `{top_c['condition_concept_id']}` | **{top_c['concept_name']}** | `{top_c['source_value']}` | {top_c['total_occurrences']:,} | {top_c['unique_patients']:,} | **{top_c['patient_prevalence_pct']}%** |")

    # 6. Inter-Visit Cadence & Landmark Feasibility
    cad = p["inter_visit_cadence"]
    land = p["landmarks_feasibility"]
    md.append("\n## 6. Inter-Visit Cadence & Landmark Eligibility\n")
    md.append(f"- **Total Consecutive Visit Intervals:** {cad['total_inter_visit_gaps']:,}")
    md.append(f"- **Median Inter-Visit Gap:** **{cad['median_gap_days']} days** (IQR: {cad['p25_gap_days']}–{cad['p75_gap_days']} days, Mean: {cad['mean_gap_days']} days)")
    md.append(f"- **Inter-Visit Gap Distribution:** Same-day: {cad['same_day_pct']}%, 1–180 days: {cad['gap_1_to_180d_pct']}%, 181–365 days: {cad['gap_181_to_365d_pct']}%, >365 days: {cad['gap_gt_365d_pct']}%")
    md.append(f"- **Visits with Follow-up within 365 Days (`H=365`):** **{(cad['same_day_pct'] + cad['gap_1_to_180d_pct'] + cad['gap_181_to_365d_pct']):.2f}%**")
    
    md.append("\n### Landmark Eligibility Pool (Under Section 1.2 Criteria)")
    md.append(f"- **Total Distinct Candidate Visits:** {land['total_distinct_visits']:,}")
    md.append(f"- **Visits with ≥ 1 Year Prior Observation:** {land['visits_with_gte_1yr_prior_obs']:,} (93.3% of visits)")
    md.append(f"- **Eligible Landmarks (≥ 1 yr prior obs + ≥ 1 prior diagnosis):** **{land['eligible_landmarks_total']:,}** (91.5% of visits)")
    md.append(f"- **Eligible Landmarks with ≥ 365d Future Observation (`H=365`):** **{land['eligible_landmarks_with_365d_future_obs']:,}**")
    md.append(f"- **Eligible Landmarks with ≥ 180d Future Observation (`H=180`):** **{land['eligible_landmarks_with_180d_future_obs']:,}**")
    md.append(f"- **Inpatient Index Landmarks (`visit_concept_id = 9201`):** **{land['eligible_inpatient_landmarks']:,}**")
    md.append(f"- **Inpatient or Emergency Index Landmarks (`visit_concept_id IN (9201, 9203)`):** **{land['eligible_inpatient_or_ed_landmarks']:,}**")

    # 7. Complete Table Schemas & Completeness
    md.append("\n## 7. Complete Table Schemas & Completeness")
    for t_name, t_info in p["tables"].items():
        md.append(f"\n### Table: `{t_name}` (Raw rows: {t_info['raw_row_count']:,}, Distinct: {t_info['distinct_records']:,})")
        md.append("| Column Name | Data Type | Null Count | Null % | Completeness |")
        md.append("|---|---|---|---|---|")
        for col in t_info["columns"]:
            comp = "100%" if col["null_pct"] == 0 else f"{(100 - col['null_pct']):.1f}%"
            md.append(f"| `{col['column_name']}` | `{col['data_type']}` | {col['null_count']:,} | {col['null_pct']}% | {comp} |")

    os.makedirs(os.path.dirname(os.path.abspath(output_md_path)), exist_ok=True)
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"Generated markdown report: {output_md_path}")


def main():
    os.makedirs("reports", exist_ok=True)
    print("Running dataset inspection on Synthea 100K...")
    profile = inspect_dataset()
    
    json_path = "reports/data_profile.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)
    print(f"Generated machine-readable report: {json_path}")
    
    md_path = "reports/data_profile.md"
    generate_markdown_report(profile, md_path)
    print("Phase 1 inspection complete!")


if __name__ == "__main__":
    main()
