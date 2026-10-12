"""
Module: src/features/pipeline.py
Phase 4: ML Feature Engineering Pipeline.

Constructs rich, leakage-free feature vectors for each candidate landmark.
All features are derived strictly from data recorded on or before the landmark date T (condition_start_date <= T).
Every feature is compatible with real-time reconstruction from a standard patient intake form (e.g. Streamlit UI).

Features constructed:
1. Demographic features (raw age, age decade one-hot indicators, sex, race, ethnicity).
2. Multi-hot pre-landmark indicators for the K=41 target comorbidity diseases.
3. Multi-hot pre-landmark indicators for high-value background conditions.
4. Comorbidity burden & utilization indices (total chronic condition count, prior observation span, prior visit frequency).
5. High-value clinical interaction terms (e.g. diabetes & hypertension, metabolic triad, CVD & CKD).
6. Network feature interface placeholder integration.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional


ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.data.labels import CONDITION_METADATA
from src.features.network_interface import get_network_feature_names, NETWORK_FEATURE_NAMES


# Identifiers & Metadata (excluded from ML inputs, used for indexing/splitting)
IDENTIFIER_COLUMNS: List[str] = [
    "person_id",
    "landmark_id",
    "visit_occurrence_id",
    "visit_concept_id",
    "is_inpatient_or_ed",
    "landmark_date",
    "future_observation_complete"
]

# Demographic feature predictors (16)
DEMOGRAPHIC_FEATURE_COLUMNS: List[str] = [
    "age_at_landmark",
    "age_lt_30",
    "age_30_39",
    "age_40_49",
    "age_50_59",
    "age_60_69",
    "age_70_79",
    "age_gte_80",
    "gender_male",
    "gender_female",
    "race_white",
    "race_black",
    "race_asian",
    "race_other",
    "ethnicity_hispanic",
    "ethnicity_non_hispanic"
]

# Longitudinal burden & utilization predictors (2)
BURDEN_FEATURE_COLUMNS: List[str] = [
    "total_prior_condition_count",
    "prior_obs_years"
]

# Clinical multi-disease interaction terms (5)
INTERACTION_FEATURE_COLUMNS: List[str] = [
    "interaction_diabetes_and_hypertension",
    "interaction_hypertension_and_lipid",
    "interaction_metabolic_triad",
    "interaction_cvd_and_ckd",
    "interaction_copd_and_cvd"
]

# Network placeholder columns (8, excluded from Phase 6 baseline models)
NETWORK_FEATURE_COLUMNS: List[str] = NETWORK_FEATURE_NAMES


# High-prevalence background conditions (informative predictors that are not prediction targets, 17)
BACKGROUND_CONDITION_CONCEPTS: Dict[int, str] = {
    4112343: "bg_normal_bmi",
    40481087: "bg_viral_sinusitis",
    260139: "bg_acute_bronchitis",
    28060: "bg_strep_or_pregnancy",
    4217975: "bg_normal_pregnancy",
    4078393: "bg_miscarriage",
    372328: "bg_otitis_media",
    4294548: "bg_viral_pharyngitis",
    440448: "bg_appendicitis",
    195588: "bg_cystitis_uti",
    440674: "bg_gout",
    7200002: "bg_alcohol_dependence",
    438130: "bg_opioid_use",
    133834: "bg_atopic_dermatitis_eczema",
    261325: "bg_suspected_condition",
    313217: "bg_suspected_respiratory_finding",
    4146173: "bg_postoperative_state"
}


def get_baseline_feature_columns(target_concepts: List[int]) -> List[str]:
    """
    Returns the exact list of 81 baseline ML feature predictors for Phase 6 modeling.
    Explicitly excludes identifier/metadata columns and all network placeholder columns.
    """
    hist_cols = [f"has_hist_{cid}" for cid in target_concepts]
    bg_cols = list(BACKGROUND_CONDITION_CONCEPTS.values())
    return DEMOGRAPHIC_FEATURE_COLUMNS + BURDEN_FEATURE_COLUMNS + hist_cols + bg_cols + INTERACTION_FEATURE_COLUMNS


def build_feature_sql(target_concepts: List[int]) -> str:
    """
    Generates vectorized SQL expressions for demographic, multi-hot, comorbidity burden,
    and clinical interaction features from prediction_landmarks tables.
    """
    # 1. Multi-hot target history indicators: has_hist_<cid>
    target_hist_exprs = [
        f"CASE WHEN list_contains(pre_landmark_condition_ids, {cid}) THEN 1 ELSE 0 END AS has_hist_{cid}"
        for cid in target_concepts
    ]

    # 2. Multi-hot background condition indicators
    bg_exprs = [
        f"CASE WHEN list_contains(pre_landmark_condition_ids, {cid}) THEN 1 ELSE 0 END AS {col_name}"
        for cid, col_name in BACKGROUND_CONDITION_CONCEPTS.items()
    ]

    # 3. Clinical Interaction Terms
    # Diabetes / Prediabetes / Hyperglycemia
    dm_list = "201826, 4311629, 4214376"
    # Hypertension
    htn_list = "316866"
    # Dyslipidemia
    lipid_list = "432867, 4120314, 436940"
    # Cardiovascular
    cvd_list = "317576, 192279, 381316, 321042"
    # Chronic Kidney Disease
    ckd_list = "4229440, 443614"
    # Chronic Respiratory
    resp_list = "258780, 257012, 4051466, 4283893"

    interactions = [
        # Diabetes + Hypertension
        f"""
        CASE WHEN (list_contains(pre_landmark_condition_ids, 201826) OR list_contains(pre_landmark_condition_ids, 4311629) OR list_contains(pre_landmark_condition_ids, 4214376))
              AND list_contains(pre_landmark_condition_ids, 316866) THEN 1 ELSE 0 END AS interaction_diabetes_and_hypertension
        """,
        # Hypertension + Hyperlipidemia
        f"""
        CASE WHEN list_contains(pre_landmark_condition_ids, 316866)
              AND (list_contains(pre_landmark_condition_ids, 432867) OR list_contains(pre_landmark_condition_ids, 4120314)) THEN 1 ELSE 0 END AS interaction_hypertension_and_lipid
        """,
        # Metabolic Triad (HTN + DM/Prediabetes + Lipid/Metabolic Syndrome)
        f"""
        CASE WHEN list_contains(pre_landmark_condition_ids, 316866)
              AND (list_contains(pre_landmark_condition_ids, 201826) OR list_contains(pre_landmark_condition_ids, 4311629))
              AND (list_contains(pre_landmark_condition_ids, 432867) OR list_contains(pre_landmark_condition_ids, 4120314) OR list_contains(pre_landmark_condition_ids, 436940)) THEN 1 ELSE 0 END AS interaction_metabolic_triad
        """,
        # Cardiovascular + CKD
        f"""
        CASE WHEN (list_contains(pre_landmark_condition_ids, 317576) OR list_contains(pre_landmark_condition_ids, 192279) OR list_contains(pre_landmark_condition_ids, 381316) OR list_contains(pre_landmark_condition_ids, 321042))
              AND (list_contains(pre_landmark_condition_ids, 4229440) OR list_contains(pre_landmark_condition_ids, 443614)) THEN 1 ELSE 0 END AS interaction_cvd_and_ckd
        """,
        # COPD / Asthma + CVD
        f"""
        CASE WHEN (list_contains(pre_landmark_condition_ids, 258780) OR list_contains(pre_landmark_condition_ids, 4051466))
              AND (list_contains(pre_landmark_condition_ids, 317576) OR list_contains(pre_landmark_condition_ids, 192279) OR list_contains(pre_landmark_condition_ids, 316866)) THEN 1 ELSE 0 END AS interaction_copd_and_cvd
        """
    ]

    all_custom_exprs = target_hist_exprs + bg_exprs + interactions
    return ",\n            ".join(all_custom_exprs)


def extract_feature_matrix(
    con: Any,
    target_concepts: List[int],

    input_table_or_parquet: str,
    output_parquet: str,
    is_inpatient_ed_cohort: bool = True
) -> str:
    """
    Extracts the structured feature matrix from prediction landmark data and writes to Parquet.
    """
    print(f"Extracting ML feature matrix from {input_table_or_parquet} -> {output_parquet}...")
    
    custom_cols_sql = build_feature_sql(target_concepts)
    
    table_source = input_table_or_parquet
    if input_table_or_parquet.endswith(".parquet"):
        clean_in = input_table_or_parquet.replace("\\", "/")
        table_source = f"read_parquet('{clean_in}')"

    query = f"""
        CREATE OR REPLACE TEMP TABLE extracted_features_temp AS
        SELECT 
            -- Entity Identifiers (Excluded from ML model inputs, preserved for joins / split mapping)
            person_id,
            landmark_id,
            visit_occurrence_id,
            visit_concept_id,
            is_inpatient_or_ed,
            landmark_date,
            future_observation_complete,
            
            -- 1. Demographic Features
            age_at_landmark,
            CASE WHEN age_at_landmark < 30 THEN 1 ELSE 0 END AS age_lt_30,
            CASE WHEN age_at_landmark >= 30 AND age_at_landmark < 40 THEN 1 ELSE 0 END AS age_30_39,
            CASE WHEN age_at_landmark >= 40 AND age_at_landmark < 50 THEN 1 ELSE 0 END AS age_40_49,
            CASE WHEN age_at_landmark >= 50 AND age_at_landmark < 60 THEN 1 ELSE 0 END AS age_50_59,
            CASE WHEN age_at_landmark >= 60 AND age_at_landmark < 70 THEN 1 ELSE 0 END AS age_60_69,
            CASE WHEN age_at_landmark >= 70 AND age_at_landmark < 80 THEN 1 ELSE 0 END AS age_70_79,
            CASE WHEN age_at_landmark >= 80 THEN 1 ELSE 0 END AS age_gte_80,
            
            CASE WHEN gender_concept_id = 8507 OR gender_source_value = 'M' THEN 1 ELSE 0 END AS gender_male,
            CASE WHEN gender_concept_id = 8532 OR gender_source_value = 'F' THEN 1 ELSE 0 END AS gender_female,
            
            CASE WHEN race_source_value = 'white' THEN 1 ELSE 0 END AS race_white,
            CASE WHEN race_source_value = 'black' THEN 1 ELSE 0 END AS race_black,
            CASE WHEN race_source_value = 'asian' THEN 1 ELSE 0 END AS race_asian,
            CASE WHEN race_source_value NOT IN ('white', 'black', 'asian') OR race_source_value IS NULL THEN 1 ELSE 0 END AS race_other,
            
            CASE WHEN ethnicity_source_value = 'hispanic' THEN 1 ELSE 0 END AS ethnicity_hispanic,
            CASE WHEN ethnicity_source_value != 'hispanic' OR ethnicity_source_value IS NULL THEN 1 ELSE 0 END AS ethnicity_non_hispanic,

            -- 2. Longitudinal Burden & Prior Utilization Indices
            existing_diagnosis_count AS total_prior_condition_count,
            ROUND(prior_obs_days / 365.25, 2) AS prior_obs_years,
            
            -- 3. Pre-Landmark Target Histories, Background Comorbidities, & Interaction Terms
            {custom_cols_sql},
            
            -- 4. Network Interface Feature Placeholders (Standard Fixed Contract)
            0.0::DOUBLE AS net_max_relative_risk,
            0.0::DOUBLE AS net_mean_relative_risk,
            0.0::DOUBLE AS net_n_significant_edges,
            -1.0::DOUBLE AS net_shortest_path_length,
            0.0::DOUBLE AS net_personalized_pagerank,
            0.0::DOUBLE AS net_target_degree_centrality,
            0.0::DOUBLE AS net_target_community_overlap,
            0.0::DOUBLE AS network_features_available

        FROM {table_source};
    """
    con.execute(query)

    os.makedirs(os.path.dirname(os.path.abspath(output_parquet)), exist_ok=True)
    clean_out = output_parquet.replace("\\", "/")
    con.execute(f"COPY extracted_features_temp TO '{clean_out}' (FORMAT PARQUET, COMPRESSION ZSTD);")
    size_mb = os.path.getsize(output_parquet) / 1024 / 1024
    print(f"Feature matrix successfully created: {output_parquet} ({size_mb:.2f} MB)")
    
    return output_parquet
