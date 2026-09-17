"""
Script to generate human-readable patient timelines for manual clinical verification.
Selects 15 diverse patients across different clinical and utilization trajectories.
Outputs reports/sample_patient_timelines.md with formatted concept and source codes.
"""

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.data.loader import OMOPDataLoader
from src.data.timeline import build_patient_timelines, get_visit_name, get_condition_name


def generate_sample_timelines(output_md_path: str = "reports/sample_patient_timelines.md", n_patients: int = 15):
    # Ensure parquet timelines are built
    build_patient_timelines()
    
    loader = OMOPDataLoader()
    con = loader.get_connection()

    sample_query = f"""
        WITH patient_metrics AS (
            SELECT 
                person_id,
                gender_source_value,
                race_source_value,
                year_of_birth,
                COUNT(*) AS total_visits,
                COUNT(CASE WHEN visit_concept_id = 9201 THEN 1 END) AS n_inpatient,
                COUNT(CASE WHEN visit_concept_id = 9203 THEN 1 END) AS n_ed,
                SUM(n_visit_conditions) AS total_condition_events,
                DATEDIFF('year', MIN(visit_start_date), MAX(visit_end_date)) AS longitudinal_years
            FROM read_parquet('data/parquet/patient_timelines.parquet')
            GROUP BY 1, 2, 3, 4
        ),
        ranked AS (
            -- 5 high morbidity patients with inpatient visits
            (SELECT person_id, 'High Morbidity / Inpatient Trajectory' AS cohort_stratum FROM patient_metrics WHERE n_inpatient >= 2 AND total_condition_events >= 5 ORDER BY person_id LIMIT 5)
            UNION ALL
            -- 5 ED & outpatient chronic disease patients
            (SELECT person_id, 'Chronic / Emergency Follow-up' AS cohort_stratum FROM patient_metrics WHERE n_ed >= 2 AND n_inpatient = 0 AND total_condition_events >= 3 ORDER BY person_id LIMIT 5)
            UNION ALL
            -- 5 routine outpatient / low comorbidity patients
            (SELECT person_id, 'Outpatient / Low Morbidity' AS cohort_stratum FROM patient_metrics WHERE total_condition_events BETWEEN 1 AND 2 AND total_visits BETWEEN 5 AND 20 ORDER BY person_id LIMIT 5)
        )
        SELECT DISTINCT person_id, cohort_stratum FROM ranked LIMIT {n_patients};
    """
    sample_patients = loader.query_dicts(sample_query)

    md = []
    md.append("# Sample Patient Longitudinal Timelines (Manual Verification)")
    md.append("\n*Generated for clinical and data integrity verification against raw Synthea OMOP records.*  ")
    md.append(f"*Total Sampled Patients:* {len(sample_patients)}\n")
    md.append("---\n")

    for i, p_info in enumerate(sample_patients, 1):
        pid = p_info["person_id"]
        stratum = p_info["cohort_stratum"]

        # Fetch timeline records
        records = loader.query_dicts("""
            SELECT *
            FROM read_parquet('data/parquet/patient_timelines.parquet')
            WHERE person_id = ?
            ORDER BY visit_sequence_num ASC;
        """, [pid])

        if not records:
            continue

        first = records[0]
        last = records[-1]
        n_visits = len(records)
        all_conds = set()
        for r in records:
            for cid in r["visit_condition_ids"]:
                all_conds.add(cid)

        md.append(f"## Patient #{i} (ID: `{pid}`) — *{stratum}*")
        md.append(f"- **Demographics:** Sex: `{first['gender_source_value']}`, Race: `{first['race_source_value']}`, Birth Year: `{first['year_of_birth']}`")
        md.append(f"- **Observation Period Span:** `{first['obs_start_date']}` to `{first['obs_end_date']}` ({round(first['future_obs_days']/365.25 + first['prior_obs_days']/365.25, 1)} years)")
        md.append(f"- **Timeline Summary:** {n_visits} total distinct visits, {len(all_conds)} unique conditions recorded from `{first['visit_start_date']}` to `{last['visit_end_date']}`\n")
        
        md.append("| # | Visit Date | Visit Type | Age | Duration | Conditions Diagnosed at Encounter |")
        md.append("|---|---|---|---|---|---|")

        display_records = records
        truncated = False
        if len(records) > 25:
            display_records = records[:12] + records[-12:]
            truncated = True

        for idx, r in enumerate(display_records):
            if truncated and idx == 12:
                md.append(f"| ... | *[{len(records) - 24} intermediate routine encounters omitted]* | ... | ... | ... | ... |")

            v_name = get_visit_name(r["visit_concept_id"])
            dur = f"{r['visit_duration_days']}d" if r['visit_duration_days'] > 1 else "1d"
            
            # Format conditions with clean name, concept_id, and source code
            cond_strs = []
            for cid, csrc in zip(r["visit_condition_ids"], r["visit_condition_sources"]):
                c_name = get_condition_name(cid, csrc)
                cond_strs.append(f"• **{c_name}** (concept_id: `{cid}`, code: `{csrc}`)")
            
            cond_display = "<br>".join(cond_strs) if cond_strs else "—"
            md.append(f"| {r['visit_sequence_num']} | `{r['visit_start_date']}` | **{v_name}** | {r['age_at_visit']}y | {dur} | {cond_display} |")

        md.append("\n---\n")

    os.makedirs(os.path.dirname(os.path.abspath(output_md_path)), exist_ok=True)
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"Generated sample timelines for {len(sample_patients)} patients: {output_md_path}")


if __name__ == "__main__":
    generate_sample_timelines()
