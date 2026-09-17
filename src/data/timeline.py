"""
Phase 2: Patient Timeline Construction Module.
Builds chronological, queryable per-patient timelines from OMOP tables using DuckDB.
Aggregates visit records, concurrent and cumulative conditions, and observation coverage.
Deduplicates entities strictly by their OMOP entity keys.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import duckdb

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.data.loader import OMOPDataLoader, get_db


# Human-friendly descriptions for visit concepts
VISIT_NAME_MAP = {
    9201: "Inpatient Visit",
    9202: "Outpatient Visit",
    9203: "Emergency Room Visit",
    32895: "Ambulatory Visit",
    42898160: "Wellness Visit",
    581477: "Home Visit",
    581476: "Telehealth Visit"
}

# Comprehensive SNOMED / OMOP condition vocabulary mapping for Synthea 100K
CONDITION_NAME_MAP = {
    # OMOP Concept IDs
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
    4028305: "Acute viral pharyngitis",
    40481087: "Viral sinusitis",
    260139: "Acute bronchitis",
    4311629: "Prediabetes",
    257012: "Chronic sinusitis",
    4217975: "Normal pregnancy",
    4078393: "Miscarriage (Spontaneous abortion)",
    372328: "Otitis media",
    81151: "Sprain of ankle",
    4285898: "Polyp of colon",
    4120314: "Hypertriglyceridemia",
    436940: "Metabolic syndrome X",
    378001: "Concussion injury",
    4294548: "Acute viral pharyngitis",
    381316: "Stroke (Cerebrovascular accident)",
    4283893: "Sinusitis",
    4214376: "Hyperglycemia",
    4079750: "Osteoarthritis of knee",
    4229440: "Chronic kidney disease",
    80502: "Osteoporosis",
    440448: "Appendicitis",
    4051466: "Childhood asthma",
    4048171: "Childhood asthma exacerbation",
    4166224: "Ruptured appendix",
    4230399: "Closed fracture of wrist",
    40479422: "Second degree burn",
    4055754: "Fracture of rib",
    4142905: "Fracture of clavicle",
    440086: "Childhood ADHD",
    4237458: "Fracture of upper limb",
    78272: "Sprain of wrist",
    4134304: "Acute upper respiratory infection",
    4299128: "Third degree burn",
    261325: "Suspected condition"
}

# SNOMED Source Code Map
SOURCE_CODE_MAP = {
    444814009: "Viral sinusitis",
    162864005: "Suspected respiratory finding",
    195662009: "Normal body mass index",
    10509002: "Acute bronchitis",
    15777000: "Prediabetes",
    271737000: "Anemia",
    38341003: "Hypertensive disorder",
    40055000: "Chronic sinusitis",
    72892002: "Normal pregnancy",
    19169002: "Miscarriage",
    43878008: "Streptococcal sore throat",
    408512008: "Body mass index 30+ - obesity",
    65363002: "Otitis media",
    55822004: "Hyperlipidemia",
    44465007: "Sprain of ankle",
    68496003: "Polyp of colon",
    44054006: "Type 2 diabetes mellitus",
    302870006: "Hypertriglyceridemia",
    237602007: "Metabolic syndrome X",
    53741008: "Coronary arteriosclerosis",
    62106007: "Concussion injury",
    75498004: "Acute viral pharyngitis",
    230690007: "Stroke (Cerebrovascular accident)",
    36971009: "Sinusitis",
    80394007: "Hyperglycemia",
    239873007: "Osteoarthritis of knee",
    88805009: "Chronic kidney disease",
    64859006: "Osteoporosis",
    74400008: "Appendicitis",
    428251008: "Postoperative state",
    47693006: "Ruptured appendix",
    232353008: "Peritonitis",
    233678006: "Childhood asthma",
    359817006: "Closed fracture of wrist",
    444448004: "Second degree burn",
    196416002: "Fracture of rib",
    33737001: "Fracture of clavicle",
    192127007: "Childhood attention deficit hyperactivity disorder",
    58150001: "Fracture of upper limb",
    70704007: "Sprain of wrist",
    263102004: "Acute upper respiratory infection",
    403192003: "Third degree burn",
    87433001: "Suspected condition"
}


def get_visit_name(concept_id: int) -> str:
    return VISIT_NAME_MAP.get(concept_id, f"Visit (concept_id: {concept_id})")


def get_condition_name(concept_id: int, source_val: Any = None) -> str:
    # Check source code mapping first if available
    try:
        if source_val is not None:
            s_int = int(source_val)
            if s_int in SOURCE_CODE_MAP:
                return SOURCE_CODE_MAP[s_int]
    except (ValueError, TypeError):
        pass

    if concept_id in CONDITION_NAME_MAP:
        return CONDITION_NAME_MAP[concept_id]

    if source_val and str(source_val).strip() and str(source_val) not in ("None", "nan", "0"):
        return f"Condition (source_code: {source_val})"
    return f"Condition (concept_id: {concept_id})"


def build_patient_timelines(
    source_dir: str = "synthea100k",
    parquet_dir: str = "data/parquet",
    output_parquet: Optional[str] = "data/parquet/patient_timelines.parquet",
    force_rebuild: bool = False
) -> str:
    """
    Constructs a chronological, deduplicated patient timeline table in DuckDB and caches it to Parquet.
    """
    if output_parquet and os.path.exists(output_parquet) and not force_rebuild:
        return output_parquet

    loader = OMOPDataLoader(source_dir=source_dir, parquet_dir=parquet_dir)
    con = loader.get_connection()

    print("Building deduplicated views in DuckDB...")

    # 1. Deduplicate by entity primary keys
    con.execute("""
        CREATE OR REPLACE TEMP VIEW dedup_person AS
        SELECT 
            person_id,
            ANY_VALUE(gender_concept_id) AS gender_concept_id,
            ANY_VALUE(year_of_birth) AS year_of_birth,
            ANY_VALUE(birth_datetime) AS birth_datetime,
            ANY_VALUE(race_concept_id) AS race_concept_id,
            ANY_VALUE(ethnicity_concept_id) AS ethnicity_concept_id,
            COALESCE(ANY_VALUE(gender_source_value), 'UNKNOWN') AS gender_source_value,
            COALESCE(ANY_VALUE(race_source_value), 'UNKNOWN') AS race_source_value,
            COALESCE(ANY_VALUE(ethnicity_source_value), 'UNKNOWN') AS ethnicity_source_value
        FROM person
        GROUP BY person_id;
    """)

    con.execute("""
        CREATE OR REPLACE TEMP VIEW dedup_obs_period AS
        SELECT 
            person_id,
            MIN(CAST(observation_period_start_date AS DATE)) AS obs_start_date,
            MAX(CAST(observation_period_end_date AS DATE)) AS obs_end_date
        FROM observation_period
        GROUP BY person_id;
    """)

    con.execute("""
        CREATE OR REPLACE TEMP VIEW dedup_visit AS
        SELECT 
            person_id,
            visit_occurrence_id,
            ANY_VALUE(visit_concept_id) AS visit_concept_id,
            MIN(CAST(visit_start_date AS DATE)) AS visit_start_date,
            MAX(CAST(visit_end_date AS DATE)) AS visit_end_date,
            ANY_VALUE(visit_type_concept_id) AS visit_type_concept_id
        FROM visit_occurrence
        GROUP BY person_id, visit_occurrence_id;
    """)

    con.execute("""
        CREATE OR REPLACE TEMP VIEW dedup_condition AS
        SELECT 
            person_id,
            condition_occurrence_id,
            ANY_VALUE(condition_concept_id) AS condition_concept_id,
            MIN(CAST(condition_start_date AS DATE)) AS condition_start_date,
            MAX(CAST(condition_end_date AS DATE)) AS condition_end_date,
            ANY_VALUE(visit_occurrence_id) AS visit_occurrence_id,
            ANY_VALUE(condition_source_value) AS condition_source_value
        FROM condition_occurrence
        GROUP BY person_id, condition_occurrence_id;
    """)

    print("Aggregating conditions by visit using equi-join...")
    # 2. Equi-join on visit_occurrence_id
    con.execute("""
        CREATE OR REPLACE TEMP VIEW visit_conditions AS
        SELECT 
            v.person_id,
            v.visit_occurrence_id,
            LIST(DISTINCT c.condition_concept_id) FILTER (WHERE c.condition_concept_id IS NOT NULL) AS visit_condition_ids,
            LIST(DISTINCT c.condition_source_value) FILTER (WHERE c.condition_source_value IS NOT NULL) AS visit_condition_sources,
            COUNT(DISTINCT c.condition_concept_id) AS n_visit_conditions
        FROM dedup_visit v
        LEFT JOIN dedup_condition c 
            ON v.visit_occurrence_id = c.visit_occurrence_id
        GROUP BY v.person_id, v.visit_occurrence_id;
    """)

    print("Assembling chronological timeline per patient...")
    # 3. Assemble chronological timeline table
    con.execute("""
        CREATE OR REPLACE TEMP TABLE patient_timeline_table AS
        SELECT 
            v.person_id,
            p.gender_concept_id,
            p.gender_source_value,
            p.year_of_birth,
            p.birth_datetime,
            p.race_source_value,
            p.ethnicity_source_value,
            op.obs_start_date,
            op.obs_end_date,
            v.visit_occurrence_id,
            v.visit_concept_id,
            v.visit_start_date,
            v.visit_end_date,
            DATEDIFF('day', v.visit_start_date, v.visit_end_date) + 1 AS visit_duration_days,
            -- Age in years at the time of the visit
            DATEDIFF('year', CAST(p.birth_datetime AS DATE), v.visit_start_date) AS age_at_visit,
            -- Observation coverage relative to this visit
            DATEDIFF('day', op.obs_start_date, v.visit_start_date) AS prior_obs_days,
            DATEDIFF('day', v.visit_end_date, op.obs_end_date) AS future_obs_days,
            -- Chronological visit sequence index for this patient
            ROW_NUMBER() OVER(
                PARTITION BY v.person_id 
                ORDER BY v.visit_start_date, v.visit_end_date, v.visit_occurrence_id
            ) AS visit_sequence_num,
            -- Visit-level conditions
            COALESCE(vc.visit_condition_ids, []) AS visit_condition_ids,
            COALESCE(vc.visit_condition_sources, []) AS visit_condition_sources,
            COALESCE(vc.n_visit_conditions, 0) AS n_visit_conditions
        FROM dedup_visit v
        JOIN dedup_person p ON v.person_id = p.person_id
        JOIN dedup_obs_period op ON v.person_id = op.person_id
        LEFT JOIN visit_conditions vc 
            ON v.person_id = vc.person_id AND v.visit_occurrence_id = vc.visit_occurrence_id
        ORDER BY v.person_id, v.visit_start_date, v.visit_end_date, v.visit_occurrence_id;
    """)

    if output_parquet:
        os.makedirs(os.path.dirname(os.path.abspath(output_parquet)), exist_ok=True)
        clean_out = output_parquet.replace("\\", "/")
        print(f"Exporting patient timelines to Parquet: {output_parquet}...")
        con.execute(f"COPY patient_timeline_table TO '{clean_out}' (FORMAT PARQUET, COMPRESSION ZSTD);")
        size_mb = os.path.getsize(output_parquet) / 1024 / 1024
        print(f"Patient timeline Parquet created successfully ({size_mb:.2f} MB)")

    return output_parquet or "patient_timeline_table"


def get_patient_timeline(
    person_id: int,
    source_dir: str = "synthea100k",
    parquet_dir: str = "data/parquet"
) -> List[Dict[str, Any]]:
    """
    Retrieves the full chronological timeline for a specific patient.
    """
    loader = OMOPDataLoader(source_dir=source_dir, parquet_dir=parquet_dir)
    con = loader.get_connection()
    
    # Ensure timeline table or view exists
    build_patient_timelines(source_dir=source_dir, parquet_dir=parquet_dir)
    
    sql = """
        SELECT *
        FROM read_parquet('data/parquet/patient_timelines.parquet')
        WHERE person_id = ?
        ORDER BY visit_sequence_num ASC;
    """
    rel = con.execute(sql, [person_id])
    cols = [desc[0] for desc in rel.description]
    rows = rel.fetchall()
    return [dict(zip(cols, row)) for row in rows]


if __name__ == "__main__":
    out_path = build_patient_timelines(force_rebuild=True)
    print("Timeline construction complete at:", out_path)
