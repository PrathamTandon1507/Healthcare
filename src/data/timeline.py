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
    # Cardiometabolic & Endocrine
    316866: "Essential Hypertension",
    201826: "Type 2 Diabetes Mellitus",
    4311629: "Prediabetes",
    432867: "Hyperlipidemia",
    4120314: "Hypertriglyceridemia",
    436940: "Metabolic Syndrome X",
    317576: "Coronary Arteriosclerosis",
    192279: "Congestive Heart Failure",
    4329847: "Myocardial Infarction",
    321042: "Cardiac Arrest",
    4214376: "Hyperglycemia",
    83664006: "Hypothyroidism",
    4309027: "Hypothyroidism",
    375557: "Hypothyroidism",
    440674: "Gout",
    7200002: "Alcoholism / Alcohol Dependence",
    4218106: "Alcoholism / Alcohol Dependence",
    438130: "Opioid Abuse / Harmful Use",
    440383: "Atrial Fibrillation",
    
    # Diabetic Complications
    37016354: "Neuropathy due to Type 2 Diabetes",
    43530656: "Nonproliferative Retinopathy due to Type 2 Diabetes",
    45769905: "Microalbuminuria due to Type 2 Diabetes",
    45770830: "Macular Edema due to Type 2 Diabetes",
    43530685: "Proliferative Retinopathy due to Type 2 Diabetes",
    45757499: "Proteinuria due to Type 2 Diabetes",
    422034002: "Retinopathy due to Type 2 Diabetes",
    4226121: "Retinopathy due to Type 2 Diabetes",
    45763582: "Blindness due to Type 2 Diabetes",

    # Renal & Urological Chronic
    4229440: "Chronic Kidney Disease",
    443614: "Chronic Kidney Disease Stage 1",
    443601: "Chronic Kidney Disease Stage 1",
    443597: "Chronic Kidney Disease Stage 2",
    443612: "Chronic Kidney Disease Stage 4",
    443600: "Chronic Kidney Disease Stage 4",
    443613: "Chronic Kidney Disease Stage 5",
    193782: "End Stage Renal Disease",
    197927001: "Recurrent Urinary Tract Infection",
    4056621: "Recurrent Urinary Tract Infection",

    # Neurological & Mental Health
    381316: "Stroke (Cerebrovascular Accident)",
    381591: "Stroke (Cerebrovascular Accident)",
    26929004: "Alzheimer's Disease",
    378419: "Alzheimer's Disease",
    4043241: "Familial Alzheimer's Disease",
    84757009: "Epilepsy / Seizure Disorder",
    380378: "Epilepsy / Seizure Disorder",
    4029498: "Seizure Disorder",
    4152280: "Major Depressive Disorder",
    378253: "Major Depressive Disorder",
    4282096: "Major Depression, Single Episode",
    436676: "Posttraumatic Stress Disorder",
    440086: "Childhood ADHD",
    4316217: "Fibromyalgia Syndrome",
    44782520: "Chronic Paralysis due to Spinal Cord Lesion",

    # Chronic Respiratory & Allergic
    257012: "Chronic Sinusitis",
    4283893: "Sinusitis",
    438112: "Sinusitis",
    258780: "Chronic Obstructive Bronchitis (COPD)",
    255573: "Chronic Obstructive Lung Disease",
    4051466: "Childhood Asthma",
    317009: "Asthma",
    4048171: "Childhood Asthma Exacerbation / Peritonitis",
    40486433: "Perennial Allergic Rhinitis",
    4280726: "Seasonal Allergic Rhinitis",
    133834: "Atopic Dermatitis / Eczema",
    4084167: "Acute Allergic Reaction",

    # Musculoskeletal & Degenerative
    4079750: "Osteoarthritis of Knee",
    4079749: "Osteoarthritis of Hip",
    75036: "Localized Osteoarthritis of Hand",
    80502: "Osteoporosis",
    80809: "Rheumatoid Arthritis",
    436096: "Chronic Pain",
    43530652: "Chronic Intractable Migraine",

    # Oncology & Pre-Malignant Neoplasms
    4285898: "Polyp of Colon",
    37017023: "Recurrent Rectal Polyp",
    4129902: "Neoplasm of Prostate",
    200970: "Carcinoma in situ of Prostate",
    4115276: "Non-Small Cell Lung Cancer",
    4310703: "Non-Small Cell Carcinoma of Lung, Stage 1",
    37395648: "Small Cell Carcinoma of Lung, Stage 1",
    4110591: "Small Cell Carcinoma of Lung",
    4180790: "Malignant Neoplasm of Colon",
    79740: "Primary Malignant Neoplasm of Colon",
    197500: "Primary Malignant Neoplasm of Colon",
    4311765: "Secondary Malignant Neoplasm of Colon",

    # Hematology
    439777: "Anemia",

    # Acute / Transient Infections (Excluded from comorbidity target)
    40481087: "Viral Sinusitis",
    260139: "Acute Bronchitis",
    28060: "Streptococcal Sore Throat",
    4294548: "Acute Viral Pharyngitis",
    372328: "Otitis Media",
    4134304: "Acute Upper Respiratory Infection",
    440448: "Appendicitis",
    4166224: "Ruptured Appendix",
    195588: "Cystitis (Urinary Tract Infection)",
    255848: "Pneumonia",
    4341247: "Protracted Diarrhea",
    198809: "Acute Cholecystitis",
    196456: "Gallbladder Calculus (Gallstone)",
    198199: "Pyelonephritis",
    4008261: "Pseudomonas Aeruginosa Infection",
    40489907: "Staphylococcus Aureus Sepsis",
    40491961: "Pseudomonas Sepsis",
    4116491: "Infectious Process",

    # Acute Trauma / Injuries / Fractures / Burns (Excluded from comorbidity target)
    81151: "Sprain of Ankle",
    78272: "Sprain of Wrist",
    4055754: "Fracture of Rib",
    4237458: "Fracture of Upper Limb",
    4142905: "Fracture of Clavicle",
    4230399: "Closed Fracture of Wrist",
    4059173: "Fracture of Ankle",
    4156265: "Facial Laceration",
    4152936: "Laceration of Thigh",
    4113008: "Laceration of Hand",
    4155034: "Laceration of Forearm",
    4109685: "Laceration of Foot",
    378001: "Concussion Injury",
    375671: "Concussion with Loss of Consciousness",
    4001336: "Concussion Injury of Brain",
    40479422: "Second Degree Burn",
    4296204: "First Degree Burn",
    4296205: "Second Degree Burn",
    4299128: "Third Degree Burn",
    40480160: "Burn Injury",
    4149245: "Rupture of Patellar Tendon",
    4035415: "Tear of Meniscus of Knee",
    40479768: "Injury of Anterior Cruciate Ligament",
    4048695: "Fracture of Vertebral Column",
    4066995: "Fracture of Vertebral Column with Spinal Cord Injury",
    4132546: "Traumatic Brain Injury",
    4208104: "Drug Overdose",
    4262136: "Drug Overdose / Poisoning",
    4196262: "Suicidal Deliberate Poisoning",
    444362: "Suicidal Poisoning",
    4218389: "Whiplash Injury to Neck",
    4278672: "Fracture of Forearm",

    # Obstetric / Pregnancy Conditions (Excluded from comorbidity target)
    4217975: "Normal Pregnancy",
    4078393: "Miscarriage (Spontaneous Abortion)",
    40318618: "Complete Miscarriage",
    199076: "Tubal Pregnancy",
    439393: "Pre-Eclampsia",
    137613: "Eclampsia in Pregnancy",
    4188598: "High Risk Pregnancy",

    # Administrative / Status / Non-Disease Findings (Excluded from comorbidity target)
    4112343: "Normal Body Mass Index",
    261325: "Suspected Condition",
    313217: "Suspected Respiratory Finding",
    4146173: "Postoperative State",
    4166590: "Postoperative State",
    4094814: "Postoperative Finding",
    134438: "Contact Dermatitis",
    4245614: "Bleeding from Anus",
    441267: "Cystic Fibrosis",
    4144583: "Diabetes Mellitus due to Cystic Fibrosis",
    4021336: "At Risk for Suicide",
    45769019: "Female Infertility due to Cystic Fibrosis",
    319049: "Clinical Finding",
    255891: "Clinical Finding",
    433125: "Clinical Finding",
    193591: "Clinical Finding"
}

# SNOMED Source Code Map
SOURCE_CODE_MAP = {
    444814009: "Viral Sinusitis",
    162864005: "Suspected Respiratory Finding",
    195662009: "Normal Body Mass Index",
    10509002: "Acute Bronchitis",
    15777000: "Prediabetes",
    271737000: "Anemia",
    38341003: "Essential Hypertension",
    40055000: "Chronic Sinusitis",
    72892002: "Normal Pregnancy",
    19169002: "Miscarriage (Spontaneous Abortion)",
    43878008: "Streptococcal Sore Throat",
    408512008: "Body mass index 30+ - obesity",
    65363002: "Otitis Media",
    55822004: "Hyperlipidemia",
    44465007: "Sprain of Ankle",
    68496003: "Polyp of Colon",
    44054006: "Type 2 Diabetes Mellitus",
    302870006: "Hypertriglyceridemia",
    237602007: "Metabolic Syndrome X",
    53741008: "Coronary Arteriosclerosis",
    62106007: "Concussion Injury",
    75498004: "Acute Viral Pharyngitis",
    230690007: "Stroke (Cerebrovascular Accident)",
    36971009: "Sinusitis",
    80394007: "Hyperglycemia",
    239873007: "Osteoarthritis of Knee",
    88805009: "Chronic Kidney Disease",
    64859006: "Osteoporosis",
    74400008: "Appendicitis",
    428251008: "Postoperative State",
    47693006: "Ruptured Appendix",
    232353008: "Peritonitis",
    233678006: "Childhood Asthma",
    359817006: "Closed Fracture of Wrist",
    444448004: "Second Degree Burn",
    196416002: "Fracture of Rib",
    33737001: "Fracture of Clavicle",
    192127007: "Childhood ADHD",
    58150001: "Fracture of Upper Limb",
    70704007: "Sprain of Wrist",
    263102004: "Acute Upper Respiratory Infection",
    403192003: "Third Degree Burn",
    87433001: "Suspected Condition",
    124171000119105: "Chronic Intractable Migraine",
    82423001: "Chronic Pain",
    55680006: "Drug Overdose",
    39848009: "Whiplash Injury to Neck",
    65966004: "Fracture of Forearm",
    156073000: "Complete Miscarriage",
    284551006: "Laceration of Foot",
    16114001: "Fracture of Ankle",
    301011002: "Infectious Process",
    443165006: "Burn Injury",
    283371005: "Laceration of Forearm",
    284549007: "Laceration of Hand",
    370247008: "Facial Laceration",
    283385000: "Laceration of Thigh",
    403190006: "First Degree Burn",
    713197008: "Recurrent Rectal Polyp",
    38822007: "Cystitis (Urinary Tract Infection)",
    398254007: "Pre-Eclampsia",
    35999006: "Drug Overdose / Poisoning",
    314994000: "Suicidal Deliberate Poisoning",
    403191005: "Second Degree Burn",
    62564004: "Concussion with Loss of Consciousness",
    79586000: "Tubal Pregnancy",
    254637007: "Non-Small Cell Lung Cancer",
    424132000: "Non-Small Cell Carcinoma of Lung, Stage 1",
    67811000119102: "Small Cell Carcinoma of Lung, Stage 1",
    254632001: "Small Cell Carcinoma of Lung",
    92691004: "Carcinoma in situ of Prostate",
    126906006: "Neoplasm of Prostate",
    26929004: "Alzheimer's Disease",
    230265002: "Familial Alzheimer's Disease",
    84757009: "Epilepsy / Seizure Disorder",
    128613002: "Seizure Disorder",
    127013003: "Congestive Heart Failure",
    431855005: "Chronic Kidney Disease Stage 1",
    431856006: "Chronic Kidney Disease Stage 1",
    433144002: "Chronic Kidney Disease Stage 2",
    431857002: "Chronic Kidney Disease Stage 4",
    185086009: "Chronic Obstructive Bronchitis (COPD)",
    363406005: "Malignant Neoplasm of Colon",
    109838007: "Primary Malignant Neoplasm of Colon",
    93761005: "Primary Malignant Neoplasm of Colon",
    94260004: "Secondary Malignant Neoplasm of Colon",
    368581000119106: "Neuropathy due to Type 2 Diabetes",
    422034002: "Retinopathy due to Type 2 Diabetes",
    1551000119108: "Nonproliferative Retinopathy due to Type 2 Diabetes",
    90781000119102: "Microalbuminuria due to Type 2 Diabetes",
    97331000119101: "Macular Edema due to Type 2 Diabetes",
    1501000119109: "Proliferative Retinopathy due to Type 2 Diabetes",
    157141000119108: "Proteinuria due to Type 2 Diabetes",
    60951000119105: "Blindness due to Type 2 Diabetes",
    201834006: "Localized Osteoarthritis of Hand",
    239872002: "Osteoarthritis of Hip",
    410429000: "Cardiac Arrest",
    446096008: "Perennial Allergic Rhinitis",
    367498001: "Seasonal Allergic Rhinitis",
    24079001: "Atopic Dermatitis / Eczema",
    241929008: "Acute Allergic Reaction",
    74400008: "Appendicitis",
    30832001: "Rupture of Patellar Tendon",
    233604007: "Pneumonia",
    197927001: "Recurrent Urinary Tract Infection",
    7200002: "Alcoholism / Alcohol Dependence",
    90560007: "Gout",
    5602001: "Opioid Abuse / Harmful Use",
    83664006: "Hypothyroidism",
    370143000: "Major Depressive Disorder",
    36923009: "Major Depression, Single Episode",
    47505003: "Posttraumatic Stress Disorder",
    95417003: "Fibromyalgia Syndrome",
    698754002: "Chronic Paralysis due to Spinal Cord Lesion",
    69896004: "Rheumatoid Arthritis",
    65275009: "Acute Cholecystitis",
    235919008: "Gallbladder Calculus (Gallstone)",
    45816000: "Pyelonephritis",
    110030002: "Concussion Injury of Brain",
    444470001: "Injury of Anterior Cruciate Ligament",
    239720000: "Tear of Meniscus of Knee",
    15724005: "Fracture of Vertebral Column",
    1734006: "Fracture of Vertebral Column with Spinal Cord Injury",
    127295002: "Traumatic Brain Injury",
    86849004: "Suicidal Poisoning",
    198992004: "Eclampsia in Pregnancy",
    47200007: "High Risk Pregnancy",
    236077008: "Protracted Diarrhea",
    6072007: "Bleeding from Anus",
    40275004: "Contact Dermatitis",
    190905008: "Cystic Fibrosis",
    427089005: "Diabetes Mellitus due to Cystic Fibrosis",
    225444004: "At Risk for Suicide",
    707577004: "Female Infertility due to Cystic Fibrosis",
    11218009: "Pseudomonas Aeruginosa Infection",
    448417001: "Staphylococcus Aureus Sepsis",
    448813005: "Pseudomonas Sepsis"
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
