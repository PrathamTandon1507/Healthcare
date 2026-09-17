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


# Comprehensive Taxonomy: (Clinical Name, Clinical Category, Is Chronic Comorbidity Target)
CONDITION_METADATA = {
    # Cardiometabolic & Endocrine
    316866: ("Essential Hypertension", "Cardiometabolic", True),
    201826: ("Type 2 Diabetes Mellitus", "Cardiometabolic", True),
    4311629: ("Prediabetes", "Cardiometabolic", True),
    432867: ("Hyperlipidemia", "Cardiometabolic", True),
    4120314: ("Hypertriglyceridemia", "Cardiometabolic", True),
    436940: ("Metabolic Syndrome X", "Cardiometabolic", True),
    317576: ("Coronary Arteriosclerosis", "Cardiometabolic", True),
    192279: ("Congestive Heart Failure", "Cardiometabolic", True),
    4329847: ("Myocardial Infarction", "Cardiometabolic", True),
    321042: ("Cardiac Arrest", "Cardiometabolic", True),
    4214376: ("Hyperglycemia", "Cardiometabolic", True),
    83664006: ("Hypothyroidism", "Cardiometabolic", True),
    4309027: ("Hypothyroidism", "Cardiometabolic", True),
    375557: ("Hypothyroidism", "Cardiometabolic", True),
    440674: ("Gout", "Cardiometabolic", True),
    7200002: ("Alcoholism / Alcohol Dependence", "Cardiometabolic", True),
    4218106: ("Alcoholism / Alcohol Dependence", "Cardiometabolic", True),
    438130: ("Opioid Abuse / Harmful Use", "Cardiometabolic", True),
    440383: ("Atrial Fibrillation", "Cardiometabolic", True),
    
    # Diabetic Complications
    37016354: ("Neuropathy due to Type 2 Diabetes", "Diabetic Complication", True),
    43530656: ("Nonproliferative Retinopathy due to Type 2 Diabetes", "Diabetic Complication", True),
    45769905: ("Microalbuminuria due to Type 2 Diabetes", "Diabetic Complication", True),
    45770830: ("Macular Edema due to Type 2 Diabetes", "Diabetic Complication", True),
    43530685: ("Proliferative Retinopathy due to Type 2 Diabetes", "Diabetic Complication", True),
    45757499: ("Proteinuria due to Type 2 Diabetes", "Diabetic Complication", True),
    422034002: ("Retinopathy due to Type 2 Diabetes", "Diabetic Complication", True),
    4226121: ("Retinopathy due to Type 2 Diabetes", "Diabetic Complication", True),
    45763582: ("Blindness due to Type 2 Diabetes", "Diabetic Complication", True),

    # Renal & Urological Chronic
    4229440: ("Chronic Kidney Disease", "Renal", True),
    443614: ("Chronic Kidney Disease Stage 1", "Renal", True),
    443601: ("Chronic Kidney Disease Stage 1", "Renal", True),
    443597: ("Chronic Kidney Disease Stage 2", "Renal", True),
    443612: ("Chronic Kidney Disease Stage 4", "Renal", True),
    443600: ("Chronic Kidney Disease Stage 4", "Renal", True),
    443613: ("Chronic Kidney Disease Stage 5", "Renal", True),
    193782: ("End Stage Renal Disease", "Renal", True),
    197927001: ("Recurrent Urinary Tract Infection", "Renal", True),
    4056621: ("Recurrent Urinary Tract Infection", "Renal", True),

    # Neurological & Mental Health
    381316: ("Stroke (Cerebrovascular Accident)", "Neurological / Mental Health", True),
    381591: ("Stroke (Cerebrovascular Accident)", "Neurological / Mental Health", True),
    26929004: ("Alzheimer's Disease", "Neurological / Mental Health", True),
    378419: ("Alzheimer's Disease", "Neurological / Mental Health", True),
    4043241: ("Familial Alzheimer's Disease", "Neurological / Mental Health", True),
    84757009: ("Epilepsy / Seizure Disorder", "Neurological / Mental Health", True),
    380378: ("Epilepsy / Seizure Disorder", "Neurological / Mental Health", True),
    4029498: ("Seizure Disorder", "Neurological / Mental Health", True),
    4152280: ("Major Depressive Disorder", "Neurological / Mental Health", True),
    378253: ("Major Depressive Disorder", "Neurological / Mental Health", True),
    4282096: ("Major Depression, Single Episode", "Neurological / Mental Health", True),
    436676: ("Posttraumatic Stress Disorder", "Neurological / Mental Health", True),
    440086: ("Childhood ADHD", "Neurological / Mental Health", True),
    4316217: ("Fibromyalgia Syndrome", "Neurological / Mental Health", True),
    44782520: ("Chronic Paralysis due to Spinal Cord Lesion", "Neurological / Mental Health", True),

    # Chronic Respiratory & Allergic
    257012: ("Chronic Sinusitis", "Respiratory / Allergic", True),
    4283893: ("Sinusitis", "Respiratory / Allergic", True),
    438112: ("Sinusitis", "Respiratory / Allergic", True),
    258780: ("Chronic Obstructive Bronchitis (COPD)", "Respiratory / Allergic", True),
    255573: ("Chronic Obstructive Lung Disease", "Respiratory / Allergic", True),
    4051466: ("Childhood Asthma", "Respiratory / Allergic", True),
    317009: ("Asthma", "Respiratory / Allergic", True),
    4048171: ("Childhood Asthma Exacerbation / Peritonitis", "Respiratory / Allergic", True),
    40486433: ("Perennial Allergic Rhinitis", "Respiratory / Allergic", True),
    4280726: ("Seasonal Allergic Rhinitis", "Respiratory / Allergic", True),
    133834: ("Atopic Dermatitis / Eczema", "Respiratory / Allergic", True),
    4084167: ("Acute Allergic Reaction", "Respiratory / Allergic", False),

    # Musculoskeletal & Degenerative
    4079750: ("Osteoarthritis of Knee", "Musculoskeletal", True),
    4079749: ("Osteoarthritis of Hip", "Musculoskeletal", True),
    75036: ("Localized Osteoarthritis of Hand", "Musculoskeletal", True),
    80502: ("Osteoporosis", "Musculoskeletal", True),
    80809: ("Rheumatoid Arthritis", "Musculoskeletal", True),
    436096: ("Chronic Pain", "Musculoskeletal", True),
    43530652: ("Chronic Intractable Migraine", "Musculoskeletal", True),

    # Oncology & Pre-Malignant Neoplasms
    4285898: ("Polyp of Colon", "Oncology / Pre-Malignant", True),
    37017023: ("Recurrent Rectal Polyp", "Oncology / Pre-Malignant", True),
    4129902: ("Neoplasm of Prostate", "Oncology / Pre-Malignant", True),
    200970: ("Carcinoma in situ of Prostate", "Oncology / Pre-Malignant", True),
    4115276: ("Non-Small Cell Lung Cancer", "Oncology / Pre-Malignant", True),
    4310703: ("Non-Small Cell Carcinoma of Lung, Stage 1", "Oncology / Pre-Malignant", True),
    37395648: ("Small Cell Carcinoma of Lung, Stage 1", "Oncology / Pre-Malignant", True),
    4110591: ("Small Cell Carcinoma of Lung", "Oncology / Pre-Malignant", True),
    4180790: ("Malignant Neoplasm of Colon", "Oncology / Pre-Malignant", True),
    79740: ("Primary Malignant Neoplasm of Colon", "Oncology / Pre-Malignant", True),
    197500: ("Primary Malignant Neoplasm of Colon", "Oncology / Pre-Malignant", True),
    4311765: ("Secondary Malignant Neoplasm of Colon", "Oncology / Pre-Malignant", True),

    # Hematology
    439777: ("Anemia", "Hematology", True),

    # Acute / Transient Infections (Excluded from comorbidity prediction)
    40481087: ("Viral Sinusitis", "Acute Infection", False),
    260139: ("Acute Bronchitis", "Acute Infection", False),
    28060: ("Streptococcal Sore Throat", "Acute Infection", False),
    4294548: ("Acute Viral Pharyngitis", "Acute Infection", False),
    372328: ("Otitis Media", "Acute Infection", False),
    4134304: ("Acute Upper Respiratory Infection", "Acute Infection", False),
    440448: ("Appendicitis", "Acute Infection", False),
    4166224: ("Ruptured Appendix", "Acute Infection", False),
    195588: ("Cystitis (Urinary Tract Infection)", "Acute Infection", False),
    255848: ("Pneumonia", "Acute Infection", False),
    4341247: ("Protracted Diarrhea", "Acute Infection", False),
    198809: ("Acute Cholecystitis", "Acute Infection", False),
    196456: ("Gallbladder Calculus (Gallstone)", "Acute Infection", False),
    198199: ("Pyelonephritis", "Acute Infection", False),
    4008261: ("Pseudomonas Aeruginosa Infection", "Acute Infection", False),
    40489907: ("Staphylococcus Aureus Sepsis", "Acute Infection", False),
    40491961: ("Pseudomonas Sepsis", "Acute Infection", False),
    4116491: ("Infectious Process", "Acute Infection", False),

    # Acute Trauma / Injuries / Fractures / Burns (Excluded from comorbidity prediction)
    81151: ("Sprain of Ankle", "Acute Injury / Trauma", False),
    78272: ("Sprain of Wrist", "Acute Injury / Trauma", False),
    4055754: ("Fracture of Rib", "Acute Injury / Trauma", False),
    4237458: ("Fracture of Upper Limb", "Acute Injury / Trauma", False),
    4142905: ("Fracture of Clavicle", "Acute Injury / Trauma", False),
    4230399: ("Closed Fracture of Wrist", "Acute Injury / Trauma", False),
    4059173: ("Fracture of Ankle", "Acute Injury / Trauma", False),
    4156265: ("Facial Laceration", "Acute Injury / Trauma", False),
    4152936: ("Laceration of Thigh", "Acute Injury / Trauma", False),
    4113008: ("Laceration of Hand", "Acute Injury / Trauma", False),
    4155034: ("Laceration of Forearm", "Acute Injury / Trauma", False),
    4109685: ("Laceration of Foot", "Acute Injury / Trauma", False),
    378001: ("Concussion Injury", "Acute Injury / Trauma", False),
    375671: ("Concussion with Loss of Consciousness", "Acute Injury / Trauma", False),
    4001336: ("Concussion Injury of Brain", "Acute Injury / Trauma", False),
    40479422: ("Second Degree Burn", "Acute Injury / Trauma", False),
    4296204: ("First Degree Burn", "Acute Injury / Trauma", False),
    4296205: ("Second Degree Burn", "Acute Injury / Trauma", False),
    4299128: ("Third Degree Burn", "Acute Injury / Trauma", False),
    40480160: ("Burn Injury", "Acute Injury / Trauma", False),
    4149245: ("Rupture of Patellar Tendon", "Acute Injury / Trauma", False),
    4035415: ("Tear of Meniscus of Knee", "Acute Injury / Trauma", False),
    40479768: ("Injury of Anterior Cruciate Ligament", "Acute Injury / Trauma", False),
    4048695: ("Fracture of Vertebral Column", "Acute Injury / Trauma", False),
    4066995: ("Fracture of Vertebral Column with Spinal Cord Injury", "Acute Injury / Trauma", False),
    4132546: ("Traumatic Brain Injury", "Acute Injury / Trauma", False),
    4208104: ("Drug Overdose", "Acute Injury / Trauma", False),
    4262136: ("Drug Overdose / Poisoning", "Acute Injury / Trauma", False),
    4196262: ("Suicidal Deliberate Poisoning", "Acute Injury / Trauma", False),
    444362: ("Suicidal Poisoning", "Acute Injury / Trauma", False),
    4218389: ("Whiplash Injury to Neck", "Acute Injury / Trauma", False),
    4278672: ("Fracture of Forearm", "Acute Injury / Trauma", False),

    # Obstetric / Pregnancy Conditions (Excluded from comorbidity prediction)
    4217975: ("Normal Pregnancy", "Obstetric / Pregnancy", False),
    28060: ("Normal Pregnancy", "Obstetric / Pregnancy", False),
    4078393: ("Miscarriage (Spontaneous Abortion)", "Obstetric / Pregnancy", False),
    40318618: ("Complete Miscarriage", "Obstetric / Pregnancy", False),
    199076: ("Tubal Pregnancy", "Obstetric / Pregnancy", False),
    439393: ("Pre-Eclampsia", "Obstetric / Pregnancy", False),
    137613: ("Eclampsia in Pregnancy", "Obstetric / Pregnancy", False),
    4188598: ("High Risk Pregnancy", "Obstetric / Pregnancy", False),

    # Administrative / Status / Non-Disease Findings (Excluded from comorbidity prediction)
    4112343: ("Normal Body Mass Index", "Administrative / Finding", False),
    261325: ("Suspected Condition", "Administrative / Finding", False),
    313217: ("Suspected Respiratory Finding", "Administrative / Finding", False),
    4146173: ("Postoperative State", "Administrative / Finding", False),
    4166590: ("Postoperative State", "Administrative / Finding", False),
    4094814: ("Postoperative Finding", "Administrative / Finding", False),
    134438: ("Contact Dermatitis", "Administrative / Finding", False),
    4245614: ("Bleeding from Anus", "Administrative / Finding", False),
    441267: ("Cystic Fibrosis", "Administrative / Finding", False),
    4144583: ("Diabetes Mellitus due to Cystic Fibrosis", "Administrative / Finding", False),
    4021336: ("At Risk for Suicide", "Administrative / Finding", False),
    45769019: ("Female Infertility due to Cystic Fibrosis", "Administrative / Finding", False),
    319049: ("Clinical Finding", "Administrative / Finding", False),
    255891: ("Clinical Finding", "Administrative / Finding", False),
    433125: ("Clinical Finding", "Administrative / Finding", False),
    193591: ("Clinical Finding", "Administrative / Finding", False)
}

# The exact curated K = 41 chronic comorbidity prediction target concepts
# (Clinical comorbidity taxonomy with >= 100 incident positive events in Cohort A)
CURATED_41_TARGET_CONCEPTS: List[int] = [
    75036, 79740, 80502, 192279, 200970, 201826, 257012, 258780, 316866, 317576,
    321042, 378419, 380378, 381316, 432867, 436096, 436940, 439777, 440086, 443614,
    4029498, 4043241, 4051466, 4079749, 4079750, 4110591, 4115276, 4120314, 4129902, 4180790,
    4214376, 4226121, 4229440, 4283893, 4285898, 4310703, 4311629, 37016354, 37017023, 37395648, 43530652
]
TARGET_41_DISEASES: List[int] = sorted(CURATED_41_TARGET_CONCEPTS)


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
        cid = d["condition_concept_id"]
        meta = CONDITION_METADATA.get(cid, (get_condition_name(cid, d["sample_source_value"]), "Other", False))
        d["condition_name"] = meta[0]
        d["category"] = meta[1]
        d["is_comorbidity_target"] = meta[2]
        results.append(d)

    return results


def select_target_disease_space(
    incidence_results: List[Dict[str, Any]],
    min_positive_landmarks: int = 100,
    min_positive_patients: int = 50,
    filter_comorbidities_only: bool = True
) -> List[Dict[str, Any]]:
    """
    Selects the target disease space K based on BOTH:
    1. Empirical statistical incidence (>= min_positive_landmarks and >= min_positive_patients)
    2. Clinical suitability for future comorbidity prediction (filtering acute infections, trauma, obstetrics)
    """
    selected = []
    for r in incidence_results:
        if r["incident_positive_landmarks"] >= min_positive_landmarks and r["unique_incident_patients"] >= min_positive_patients:
            if filter_comorbidities_only:
                if r.get("is_comorbidity_target", True):
                    selected.append(r)
            else:
                selected.append(r)
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
