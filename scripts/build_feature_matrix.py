"""
Script: scripts/build_feature_matrix.py
Phase 4: ML Feature Matrix Builder and Feature Dictionary Generator.

Executes:
1. Feature extraction on Cohort A (Inpatient/ED: 325,259 rows) -> data/parquet/features_inpatient_ed.parquet
2. Feature extraction on Cohort B (General: 3,364,928 rows) -> data/parquet/features_general.parquet
3. Target relationship EDA execution -> reports/target_imbalance_and_correlation_eda.md
4. Generates comprehensive feature catalog: reports/feature_dictionary.md
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import duckdb

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.data.labels import CONDITION_METADATA
from src.features.pipeline import extract_feature_matrix, BACKGROUND_CONDITION_CONCEPTS
from src.features.network_interface import get_network_feature_names
from scripts.analyze_target_relationships import analyze_target_imbalance_and_relationships


def generate_feature_dictionary_report(
    feature_parquet_path: str = "data/parquet/features_inpatient_ed.parquet",
    output_report_path: str = "reports/feature_dictionary.md"
):
    print(f"Generating feature dictionary report from {feature_parquet_path}...")
    con = duckdb.connect()
    clean_p = feature_parquet_path.replace("\\", "/")
    
    schema = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{clean_p}')").fetchall()
    row_count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{clean_p}')").fetchone()[0]

    md = []
    md.append("# Phase 4 Feature Dictionary & Specification Catalog")
    md.append(f"\n*Generated At:* {datetime.now().isoformat()}  ")
    md.append(f"*Source Dataset:* `{feature_parquet_path}`  ")
    md.append(f"*Total Extracted Feature Rows:* **{row_count:,}**  ")
    md.append(f"*Total Columns:* **{len(schema)}** (7 Identifiers/Meta + {len(schema)-7} ML Feature Predictors)  \n")
    md.append("---\n")

    md.append("## 1. Feature Design Principles & Inference Compatibility\n")
    md.append("In strict alignment with `COMORBIDITY_ENSEMBLE_ML_PLAN.md` (Section 2), all features adhere to three core guarantees:")
    md.append("1. **Strict Temporal Non-Leakage**: All features are derived strictly from longitudinal observations with `condition_start_date <= landmark_date`. No future encounters, procedures, or post-index lab values enter the feature matrix.")
    md.append("2. **Inference Form Reconstructability**: Every feature can be populated in real-time from a simple clinician intake form (e.g. Streamlit UI) with basic demographics, multi-select pre-existing conditions, and utilization checkboxes.")
    md.append("3. **Stable Network Graph Contract**: A modular fixed schema contract integrates graph-derived relative risks and PageRank scores (`network_interface.py`), operating seamlessly in stub mode during initial model building.\n")

    md.append("---\n")
    md.append("## 2. Comprehensive Feature Specification Table\n")
    md.append("| # | Feature Column Name | Data Type | Feature Group | Description / Clinical Meaning | Streamlit Intake Source |")
    md.append("|---|---|---|---|---|---|")

    for idx, (col_name, col_type, null_str, key_str, def_val, extra) in enumerate(schema, 1):
        if col_name in ["person_id", "landmark_id", "visit_occurrence_id", "visit_concept_id", "is_inpatient_or_ed", "landmark_date", "future_observation_complete"]:
            group = "Identifier / Split Mapping"
            desc = "Entity tracking key / observation window completeness flag (excluded from direct model weights)"
            source = "OMOP Encounter Identity"
        elif col_name.startswith("age_"):
            group = "Demographics"
            desc = "Continuous age at landmark or one-hot decade bin indicator"
            source = "Direct Age / Birth Date Input"
        elif col_name.startswith("gender_"):
            group = "Demographics"
            desc = "Binary biological sex indicator"
            source = "Sex Dropdown"
        elif col_name.startswith("race_") or col_name.startswith("ethnicity_"):
            group = "Demographics"
            desc = "Categorical race/ethnicity indicator"
            source = "Demographic Form Field"
        elif col_name in ["total_prior_condition_count", "prior_obs_years"]:
            group = "Longitudinal Burden"
            desc = "Aggregate prior chronic disease count or years of longitudinal history"
            source = "Derived from Checked Conditions"
        elif col_name.startswith("has_hist_"):
            cid = int(col_name.replace("has_hist_", ""))
            meta = CONDITION_METADATA.get(cid, ("Unknown", "Other", True))
            group = "Pre-Landmark Target History"
            desc = f"Binary indicator: Patient already has {meta[0]} at or before index encounter"
            source = "Multi-select Condition Checkbox"
        elif col_name.startswith("bg_"):
            group = "Background Comorbidity"
            desc = "Binary indicator: Pre-landmark presence of high-prevalence background condition"
            source = "Multi-select Condition Checkbox"
        elif col_name.startswith("interaction_"):
            group = "Clinical Interaction"
            desc = "Binary interaction term: Concurrent presence of high-risk comorbidity combination"
            source = "Derived from Checked Conditions"
        elif col_name.startswith("net_") or col_name == "network_features_available":
            group = "Disease Network Graph"
            desc = "Comorbidity graph relative risk, PageRank, or path length feature"
            source = "Network Module Contract"
        else:
            group = "Other"
            desc = "Clinical feature predictor"
            source = "Intake Form"

        md.append(f"| `{idx}` | **`{col_name}`** | `{col_type}` | {group} | {desc} | {source} |")

    os.makedirs(os.path.dirname(os.path.abspath(output_report_path)), exist_ok=True)
    with open(output_report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"Feature dictionary report successfully generated: {output_report_path}")


def main():
    print("Executing Phase 4: Feature Matrix Construction & Target Dissection EDA...")
    con = duckdb.connect()

    # 1. Identify Curated Target Concepts from Inpatient/ED Parquet
    inpatient_parquet = "data/parquet/prediction_landmarks_inpatient_ed.parquet"
    general_parquet = "data/parquet/prediction_landmarks.parquet"

    schema = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{inpatient_parquet}')").fetchall()
    target_cols = [r[0] for r in schema if r[0].startswith("target_")]
    target_cids = [int(col.replace("target_", "")) for col in target_cols]
    print(f"Constructing feature pipelines for {len(target_cids)} curated target diseases...")

    # 2. Extract Feature Matrix for Cohort A (Inpatient / ED)
    out_feat_inpatient = "data/parquet/features_inpatient_ed.parquet"
    extract_feature_matrix(
        con=con,
        target_concepts=target_cids,
        input_table_or_parquet=inpatient_parquet,
        output_parquet=out_feat_inpatient,
        is_inpatient_ed_cohort=True
    )

    # 3. Extract Feature Matrix for Cohort B (General Encounters)
    out_feat_general = "data/parquet/features_general.parquet"
    extract_feature_matrix(
        con=con,
        target_concepts=target_cids,
        input_table_or_parquet=general_parquet,
        output_parquet=out_feat_general,
        is_inpatient_ed_cohort=False
    )

    # 4. Execute Target Relationship & Imbalance EDA
    analyze_target_imbalance_and_relationships(
        parquet_path=inpatient_parquet,
        output_report_path="reports/target_imbalance_and_correlation_eda.md"
    )

    # 5. Generate Feature Dictionary Report
    generate_feature_dictionary_report(
        feature_parquet_path=out_feat_inpatient,
        output_report_path="reports/feature_dictionary.md"
    )

    print("Phase 4 Feature Engineering & Target Dissection execution complete!")


if __name__ == "__main__":
    main()
