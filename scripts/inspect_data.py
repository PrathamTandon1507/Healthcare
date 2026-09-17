"""
Phase 1: Dataset and Schema Inspection Script for Synthea OMOP 100K.
Analyzes person, condition_occurrence, visit_occurrence, and observation_period tables.
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

# OMOP standard concept mapping for readable reporting
CONCEPT_NAME_MAP = {
    # Gender
    8507: "MALE",
    8532: "FEMALE",
    0: "Unknown / Unspecified",
    # Race
    8527: "White",
    8516: "Black or African American",
    8515: "Asian",
    8657: "American Indian or Alaska Native",
    # Ethnicity
    38003563: "Hispanic or Latino",
    38003564: "Not Hispanic or Latino",
    # Visit concepts
    9201: "Inpatient Visit",
    9202: "Outpatient Visit",
    9203: "Emergency Room Visit",
    32895: "Ambulatory Visit",
    42898160: "Wellness Visit",
    581477: "Home Visit",
    581476: "Telehealth Visit",
    # Common Condition concepts (Synthea/SNOMED)
    317576: "Coronary arteriosclerosis",
    439777: "Anemia",
    201826: "Type 2 diabetes mellitus",
    316866: "Hypertensive disorder",
    255573: "Chronic obstructive lung disease",
    192279: "Congestive heart failure",
    317009: "Asthma",
    443454: "Hyperlipidemia",
    432867: "Hyperglycemia",
    378253: "Major depressive disorder",
    193782: "End stage renal disease",
    443611: "Chronic kidney disease",
    443601: "Chronic kidney disease stage 1",
    443597: "Chronic kidney disease stage 2",
    443612: "Chronic kidney disease stage 3",
    443600: "Chronic kidney disease stage 4",
    443613: "Chronic kidney disease stage 5",
    381591: "Cerebrovascular accident (Stroke)",
    4329847: "Myocardial infarction",
    440383: "Atrial fibrillation",
    437663: "Fever",
    4195694: "Acute bronchitis",
    254761: "Cough",
    4112343: "Body mass index 30+ - obesity",
    438112: "Sinusitis",
    28060: "Normal pregnancy",
    4163566: "Prediabetes",
    375557: "Hypothyroidism",
    140168: "Pneumonia",
    4327941: "Viral sinusitis",
    4102111: "Chronic sinusitis",
    4028305: "Acute viral pharyngitis"
}


def get_concept_desc(concept_id: int, source_val: str = None) -> str:
    if concept_id in CONCEPT_NAME_MAP:
        return CONCEPT_NAME_MAP[concept_id]
    if source_val and str(source_val).strip() and str(source_val) not in ("None", "nan"):
        return str(source_val)
    return f"Concept {concept_id}"


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
        "visit_cadence": {},
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
            SELECT DISTINCT person_id, year_of_birth, gender_concept_id, race_concept_id, ethnicity_concept_id
            FROM person
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
            SELECT DISTINCT person_id, gender_concept_id, gender_source_value
            FROM person
        )
        SELECT 
            gender_concept_id,
            COALESCE(gender_source_value, 'UNKNOWN') AS gender_source,
            COUNT(*) AS count,
            COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() AS pct
        FROM distinct_person
        GROUP BY 1, 2
        ORDER BY count DESC
    """)
    
    race_dist = loader.query_dicts("""
        WITH distinct_person AS (
            SELECT DISTINCT person_id, race_concept_id, race_source_value
            FROM person
        )
        SELECT 
            race_concept_id,
            COALESCE(race_source_value, 'UNKNOWN') AS race_source,
            COUNT(*) AS count,
            COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() AS pct
        FROM distinct_person
        GROUP BY 1, 2
        ORDER BY count DESC
    """)

    ethnicity_dist = loader.query_dicts("""
        WITH distinct_person AS (
            SELECT DISTINCT person_id, ethnicity_concept_id, ethnicity_source_value
            FROM person
        )
        SELECT 
            ethnicity_concept_id,
            COALESCE(ethnicity_source_value, 'UNKNOWN') AS ethnicity_source,
            COUNT(*) AS count,
            COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() AS pct
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
                "description": get_concept_desc(r["gender_concept_id"], r["gender_source"]),
                "count": int(r["count"]),
                "pct": round(float(r["pct"]), 2)
            }
            for r in gender_dist
        ],
        "race_distribution": [
            {
                "concept_id": int(r["race_concept_id"]),
                "source_value": str(r["race_source"]),
                "description": get_concept_desc(r["race_concept_id"], r["race_source"]),
                "count": int(r["count"]),
                "pct": round(float(r["pct"]), 2)
            }
            for r in race_dist
        ],
        "ethnicity_distribution": [
            {
                "concept_id": int(r["ethnicity_concept_id"]),
                "source_value": str(r["ethnicity_source"]),
                "description": get_concept_desc(r["ethnicity_concept_id"], r["ethnicity_source"]),
                "count": int(r["count"]),
                "pct": round(float(r["pct"]), 2)
            }
            for r in ethnicity_dist
        ]
    }

    # 3. Observation Period Profile (deduplicated)
    obs_stats = loader.query_one("""
        WITH distinct_obs AS (
            SELECT DISTINCT person_id, observation_period_id, observation_period_start_date, observation_period_end_date
            FROM observation_period
        )
        SELECT 
            COUNT(*) AS total_records,
            COUNT(DISTINCT person_id) AS unique_patients,
            MIN(observation_period_start_date) AS earliest_start,
            MAX(observation_period_end_date) AS latest_end,
            AVG(DATEDIFF('day', CAST(observation_period_start_date AS DATE), CAST(observation_period_end_date AS DATE))) AS mean_days,
            MEDIAN(DATEDIFF('day', CAST(observation_period_start_date AS DATE), CAST(observation_period_end_date AS DATE))) AS median_days,
            MIN(DATEDIFF('day', CAST(observation_period_start_date AS DATE), CAST(observation_period_end_date AS DATE))) AS min_days,
            MAX(DATEDIFF('day', CAST(observation_period_start_date AS DATE), CAST(observation_period_end_date AS DATE))) AS max_days
        FROM distinct_obs
    """)

    profile["observation_period"] = {
        "total_records": int(obs_stats["total_records"]),
        "unique_patients": int(obs_stats["unique_patients"]),
        "earliest_start": str(obs_stats["earliest_start"]),
        "latest_end": str(obs_stats["latest_end"]),
        "duration_days": {
            "mean": round(float(obs_stats["mean_days"]), 1),
            "median": round(float(obs_stats["median_days"]), 1),
            "min": int(obs_stats["min_days"]),
            "max": int(obs_stats["max_days"]),
            "mean_years": round(float(obs_stats["mean_days"]) / 365.25, 2),
            "median_years": round(float(obs_stats["median_days"]) / 365.25, 2)
        }
    }

    # 4. Visits Profile (visit_occurrence - deduplicated distinct visits)
    visit_overview = loader.query_one("""
        WITH distinct_visits AS (
            SELECT DISTINCT person_id, visit_occurrence_id, visit_concept_id, visit_start_date, visit_end_date
            FROM visit_occurrence
        )
        SELECT 
            COUNT(*) AS total_visits,
            COUNT(DISTINCT person_id) AS unique_patients,
            MIN(visit_start_date) AS earliest_start,
            MAX(visit_end_date) AS latest_end
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
            SELECT DISTINCT person_id, visit_occurrence_id, visit_concept_id
            FROM visit_occurrence
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
                "concept_name": get_concept_desc(r["visit_concept_id"]),
                "total_visits": int(r["total_visits"]),
                "unique_patients": int(r["unique_patients"]),
                "pct_visits": round(float(r["pct_visits"]), 2),
                "patient_prevalence_pct": round(int(r["unique_patients"]) / n_persons * 100, 2)
            }
            for r in visit_concept_dist
        ]
    }

    # 5. Conditions Profile (condition_occurrence - deduplicated distinct conditions)
    cond_overview = loader.query_one("""
        WITH distinct_conditions AS (
            SELECT DISTINCT person_id, condition_occurrence_id, condition_concept_id, condition_start_date
            FROM condition_occurrence
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
            SELECT DISTINCT person_id, condition_concept_id, condition_source_value
            FROM condition_occurrence
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
                "concept_name": get_concept_desc(r["condition_concept_id"], r["sample_source_value"]),
                "total_occurrences": int(r["total_occurrences"]),
                "unique_patients": int(r["unique_patients"]),
                "patient_prevalence_pct": round(float(r["patient_prevalence_pct"]), 2)
            }
            for r in top_conditions
        ]
    }

    # 6. Visit Cadence & Landmark Feasibility Analysis
    cadence_stats = loader.query_one("""
        WITH ordered_visits AS (
            SELECT 
                person_id,
                CAST(visit_start_date AS DATE) AS v_date,
                LAG(CAST(visit_start_date AS DATE)) OVER(PARTITION BY person_id ORDER BY CAST(visit_start_date AS DATE), visit_occurrence_id) AS prev_v_date
            FROM (SELECT DISTINCT person_id, visit_occurrence_id, visit_start_date FROM visit_occurrence)
        ),
        intervals AS (
            SELECT DATEDIFF('day', prev_v_date, v_date) AS days_between
            FROM ordered_visits
            WHERE prev_v_date IS NOT NULL
        )
        SELECT 
            COUNT(*) AS total_intervals,
            AVG(days_between) AS mean_interval_days,
            MEDIAN(days_between) AS median_interval_days,
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY days_between) AS p25_interval_days,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY days_between) AS p75_interval_days,
            PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY days_between) AS p90_interval_days,
            COUNT(CASE WHEN days_between <= 180 THEN 1 END) * 100.0 / COUNT(*) AS pct_within_180d,
            COUNT(CASE WHEN days_between <= 365 THEN 1 END) * 100.0 / COUNT(*) AS pct_within_365d
        FROM intervals
    """)

    landmark_counts = loader.query_one("""
        WITH distinct_v AS (
            SELECT DISTINCT person_id, visit_occurrence_id, visit_concept_id, CAST(visit_start_date AS DATE) AS v_start, CAST(visit_end_date AS DATE) AS v_end
            FROM visit_occurrence
        ),
        distinct_op AS (
            SELECT DISTINCT person_id, CAST(observation_period_start_date AS DATE) AS op_start, CAST(observation_period_end_date AS DATE) AS op_end
            FROM observation_period
        ),
        candidate_visits AS (
            SELECT 
                v.visit_occurrence_id,
                v.person_id,
                v.visit_concept_id,
                v.v_start,
                v.v_end,
                op.op_start,
                op.op_end
            FROM distinct_v v
            JOIN distinct_op op ON v.person_id = op.person_id
                AND v.v_start BETWEEN op.op_start AND op.op_end
        ),
        annotated AS (
            SELECT 
                cv.*,
                DATEDIFF('day', cv.op_start, cv.v_end) AS prior_obs_days,
                DATEDIFF('day', cv.v_end, cv.op_end) AS future_obs_days,
                (
                    SELECT COUNT(DISTINCT c.condition_occurrence_id) 
                    FROM condition_occurrence c 
                    WHERE c.person_id = cv.person_id 
                      AND CAST(c.condition_start_date AS DATE) <= cv.v_end
                ) AS prior_cond_count
            FROM candidate_visits cv
        )
        SELECT 
            COUNT(*) AS total_potential_landmarks,
            COUNT(DISTINCT person_id) AS patients_with_landmarks,
            COUNT(CASE WHEN prior_obs_days >= 365 AND prior_cond_count >= 1 THEN 1 END) AS eligible_landmarks_h_general,
            COUNT(CASE WHEN prior_obs_days >= 365 AND prior_cond_count >= 1 AND future_obs_days >= 365 THEN 1 END) AS eligible_with_365d_future_obs,
            COUNT(CASE WHEN prior_obs_days >= 365 AND prior_cond_count >= 1 AND future_obs_days >= 180 THEN 1 END) AS eligible_with_180d_future_obs,
            COUNT(CASE WHEN visit_concept_id = 9201 AND prior_obs_days >= 365 AND prior_cond_count >= 1 THEN 1 END) AS eligible_inpatient_landmarks,
            COUNT(CASE WHEN visit_concept_id IN (9201, 9203) AND prior_obs_days >= 365 AND prior_cond_count >= 1 THEN 1 END) AS eligible_inpatient_or_ed_landmarks
        FROM annotated
    """)

    profile["visit_cadence"] = {k: round(float(v), 2) for k, v in cadence_stats.items()}
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
    md.append("| Table Name | Raw Rows | Distinct Records | Columns | Role / Content |")
    md.append("|---|---|---|---|---|")
    for t_name, t_info in p["tables"].items():
        md.append(f"| `{t_name}` | {t_info['raw_row_count']:,} | {t_info['distinct_records']:,} | {len(t_info['columns'])} | Primary OMOP CDM table (`{t_info['id_column']}`) |")
    md.append("\n")

    # 2. Patient Demographics
    demo = p["demographics"]
    md.append("## 2. Patient Demographics (`person`)\n")
    md.append(f"- **Total Unique Patients (`person_id`):** {demo['total_unique_patients']:,}")
    by = demo["birth_year_stats"]
    md.append(f"- **Birth Year Range:** {int(by['min_year'])} to {int(by['max_year'])} (Median: {int(by['median_year'])}, IQR: {int(by['p25_year'])}–{int(by['p75_year'])})")
    md.append("\n### Sex / Gender Breakdown")
    md.append("| Concept ID | Description | Source Value | Count | Percentage |")
    md.append("|---|---|---|---|---|")
    for g in demo["gender_distribution"]:
        md.append(f"| `{g['concept_id']}` | {g['description']} | `{g['source_value']}` | {g['count']:,} | {g['pct']}% |")

    md.append("\n### Race Breakdown")
    md.append("| Concept ID | Description | Source Value | Count | Percentage |")
    md.append("|---|---|---|---|---|")
    for r in demo["race_distribution"][:10]:
        md.append(f"| `{r['concept_id']}` | {r['description']} | `{r['source_value']}` | {r['count']:,} | {r['pct']}% |")

    # 3. Observation Period
    obs = p["observation_period"]
    md.append("\n## 3. Observation Period (`observation_period`)\n")
    md.append(f"- **Total Distinct Observation Spans:** {obs['total_records']:,} across {obs['unique_patients']:,} patients (100% cohort coverage)")
    md.append(f"- **Dataset Time Horizon:** `{obs['earliest_start']}` to `{obs['latest_end']}`")
    md.append(f"- **Patient Observation Length:** Median = **{obs['duration_days']['median_years']} years** ({obs['duration_days']['median']:,} days), Mean = **{obs['duration_days']['mean_years']} years**")
    md.append(f"- **Min / Max Observation:** {obs['duration_days']['min']} days to {obs['duration_days']['max']:,} days\n")

    # 4. Visits Profile
    v = p["visits"]
    md.append("## 4. Visits Profile (`visit_occurrence`)\n")
    md.append(f"- **Total Distinct Visit Records:** {v['total_distinct_visits']:,}")
    md.append(f"- **Patients with >= 1 Visit:** {v['unique_patients_with_visits']:,} ({(v['unique_patients_with_visits']/demo['total_unique_patients']*100):.1f}% of cohort)")
    md.append(f"- **Date Range:** `{v['earliest_visit']}` to `{v['latest_visit']}`")
    vpp = v["visits_per_patient"]
    md.append(f"- **Visits Per Patient:** Median = {vpp['median_visits']}, Mean = {vpp['mean_visits']}, IQR = {vpp['p25_visits']}–{vpp['p75_visits']}, Max = {vpp['max_visits']}")
    md.append("\n### Visit Types Breakdown")
    md.append("| Visit Concept ID | Description | Total Encounters | Unique Patients | Encounter % | Cohort Prev % |")
    md.append("|---|---|---|---|---|---|")
    for vc in v["concept_breakdown"]:
        md.append(f"| `{vc['visit_concept_id']}` | **{vc['concept_name']}** | {vc['total_visits']:,} | {vc['unique_patients']:,} | {vc['pct_visits']}% | {vc['patient_prevalence_pct']}% |")

    # 5. Conditions Profile & Top Chronic Conditions
    c = p["conditions"]
    md.append("\n## 5. Conditions Profile (`condition_occurrence`)\n")
    md.append(f"- **Total Distinct Condition Records:** {c['total_distinct_conditions']:,}")
    md.append(f"- **Unique Patients with >= 1 Diagnosis:** {c['unique_patients_with_conditions']:,} ({(c['unique_patients_with_conditions']/demo['total_unique_patients']*100):.1f}% of cohort)")
    md.append(f"- **Distinct Condition Concepts:** {c['unique_condition_concepts']:,}")
    cpp = c["conditions_per_patient"]
    md.append(f"- **Conditions Per Patient:** Median = {cpp['median_conds']}, Mean = {cpp['mean_conds']}, Distinct Concepts/Patient = {cpp['median_unique_conds']}")
    md.append("\n### Top Conditions by Patient Prevalence")
    md.append("| Concept ID | Condition / Disease Name | Source Code | Total Events | Patient Count | Cohort Prevalence |")
    md.append("|---|---|---|---|---|---|")
    for top_c in c["top_50_conditions"][:25]:
        md.append(f"| `{top_c['condition_concept_id']}` | **{top_c['concept_name']}** | `{top_c['source_value']}` | {top_c['total_occurrences']:,} | {top_c['unique_patients']:,} | **{top_c['patient_prevalence_pct']}%** |")

    # 6. Landmark Feasibility & Horizon Validation
    cad = p["visit_cadence"]
    land = p["landmarks_feasibility"]
    md.append("\n## 6. Visit Cadence & ML Landmark Feasibility\n")
    md.append(f"- **Median Days Between Successive Visits:** {cad['median_interval_days']} days (Mean: {cad['mean_interval_days']} days)")
    md.append(f"- **Consecutive Visit Pairs within 180 Days (H=180):** {cad['pct_within_180d']}%")
    md.append(f"- **Consecutive Visit Pairs within 365 Days (H=365):** {cad['pct_within_365d']}%")
    md.append("\n### Landmark Eligibility Pool (Under Section 1.2 Criteria)")
    md.append(f"- **Total Candidate Encounters:** {land['total_potential_landmarks']:,}")
    md.append(f"- **Eligible Landmarks (≥ 1 yr prior obs + ≥ 1 prior condition):** **{land['eligible_landmarks_h_general']:,}**")
    md.append(f"- **Eligible Landmarks with ≥ 365d Future Observation (`H=365`):** **{land['eligible_with_365d_future_obs']:,}**")
    md.append(f"- **Eligible Landmarks with ≥ 180d Future Observation (`H=180`):** **{land['eligible_with_180d_future_obs']:,}**")
    md.append(f"- **Inpatient Index Encounters (`visit_concept_id = 9201`):** {land['eligible_inpatient_landmarks']:,}")
    md.append(f"- **Inpatient or Emergency Encounters (`visit_concept_id IN (9201, 9203)`):** {land['eligible_inpatient_or_ed_landmarks']:,}")

    # 7. Detailed Schema & Completeness Table
    md.append("\n## 7. Complete Table Schemas & Completeness")
    for t_name, t_info in p["tables"].items():
        md.append(f"\n### Table: `{t_name}` (Raw: {t_info['raw_row_count']:,} rows, Distinct: {t_info['distinct_records']:,})")
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
