# Phase 4 Feature Dictionary & Specification Catalog

*Generated At:* 2026-09-18T02:22:50.755184  
*Source Dataset:* `data/parquet/features_inpatient_ed.parquet`  
*Total Extracted Feature Rows:* **325,259**  
*Total Columns:* **96** (7 Identifiers/Meta + 89 ML Feature Predictors)  

---

## 1. Feature Design Principles & Inference Compatibility

In strict alignment with `COMORBIDITY_ENSEMBLE_ML_PLAN.md` (Section 2), all features adhere to three core guarantees:
1. **Strict Temporal Non-Leakage**: All features are derived strictly from longitudinal observations with `condition_start_date <= landmark_date`. No future encounters, procedures, or post-index lab values enter the feature matrix.
2. **Inference Form Reconstructability**: Every feature can be populated in real-time from a simple clinician intake form (e.g. Streamlit UI) with basic demographics, multi-select pre-existing conditions, and utilization checkboxes.
3. **Stable Network Graph Contract**: A modular fixed schema contract integrates graph-derived relative risks and PageRank scores (`network_interface.py`), operating seamlessly in stub mode during initial model building.

---

## 2. Comprehensive Feature Specification Table

| # | Feature Column Name | Data Type | Feature Group | Description / Clinical Meaning | Streamlit Intake Source |
|---|---|---|---|---|---|
| `1` | **`person_id`** | `BIGINT` | Identifier / Split Mapping | Entity tracking key / observation window completeness flag (excluded from direct model weights) | OMOP Encounter Identity |
| `2` | **`landmark_id`** | `VARCHAR` | Identifier / Split Mapping | Entity tracking key / observation window completeness flag (excluded from direct model weights) | OMOP Encounter Identity |
| `3` | **`visit_occurrence_id`** | `BIGINT` | Identifier / Split Mapping | Entity tracking key / observation window completeness flag (excluded from direct model weights) | OMOP Encounter Identity |
| `4` | **`visit_concept_id`** | `BIGINT` | Identifier / Split Mapping | Entity tracking key / observation window completeness flag (excluded from direct model weights) | OMOP Encounter Identity |
| `5` | **`is_inpatient_or_ed`** | `INTEGER` | Identifier / Split Mapping | Entity tracking key / observation window completeness flag (excluded from direct model weights) | OMOP Encounter Identity |
| `6` | **`landmark_date`** | `DATE` | Identifier / Split Mapping | Entity tracking key / observation window completeness flag (excluded from direct model weights) | OMOP Encounter Identity |
| `7` | **`future_observation_complete`** | `INTEGER` | Identifier / Split Mapping | Entity tracking key / observation window completeness flag (excluded from direct model weights) | OMOP Encounter Identity |
| `8` | **`age_at_landmark`** | `BIGINT` | Demographics | Continuous age at landmark or one-hot decade bin indicator | Direct Age / Birth Date Input |
| `9` | **`age_lt_30`** | `INTEGER` | Demographics | Continuous age at landmark or one-hot decade bin indicator | Direct Age / Birth Date Input |
| `10` | **`age_30_39`** | `INTEGER` | Demographics | Continuous age at landmark or one-hot decade bin indicator | Direct Age / Birth Date Input |
| `11` | **`age_40_49`** | `INTEGER` | Demographics | Continuous age at landmark or one-hot decade bin indicator | Direct Age / Birth Date Input |
| `12` | **`age_50_59`** | `INTEGER` | Demographics | Continuous age at landmark or one-hot decade bin indicator | Direct Age / Birth Date Input |
| `13` | **`age_60_69`** | `INTEGER` | Demographics | Continuous age at landmark or one-hot decade bin indicator | Direct Age / Birth Date Input |
| `14` | **`age_70_79`** | `INTEGER` | Demographics | Continuous age at landmark or one-hot decade bin indicator | Direct Age / Birth Date Input |
| `15` | **`age_gte_80`** | `INTEGER` | Demographics | Continuous age at landmark or one-hot decade bin indicator | Direct Age / Birth Date Input |
| `16` | **`gender_male`** | `INTEGER` | Demographics | Binary biological sex indicator | Sex Dropdown |
| `17` | **`gender_female`** | `INTEGER` | Demographics | Binary biological sex indicator | Sex Dropdown |
| `18` | **`race_white`** | `INTEGER` | Demographics | Categorical race/ethnicity indicator | Demographic Form Field |
| `19` | **`race_black`** | `INTEGER` | Demographics | Categorical race/ethnicity indicator | Demographic Form Field |
| `20` | **`race_asian`** | `INTEGER` | Demographics | Categorical race/ethnicity indicator | Demographic Form Field |
| `21` | **`race_other`** | `INTEGER` | Demographics | Categorical race/ethnicity indicator | Demographic Form Field |
| `22` | **`ethnicity_hispanic`** | `INTEGER` | Demographics | Categorical race/ethnicity indicator | Demographic Form Field |
| `23` | **`ethnicity_non_hispanic`** | `INTEGER` | Demographics | Categorical race/ethnicity indicator | Demographic Form Field |
| `24` | **`total_prior_condition_count`** | `BIGINT` | Longitudinal Burden | Aggregate prior chronic disease count or years of longitudinal history | Derived from Checked Conditions |
| `25` | **`prior_obs_years`** | `DOUBLE` | Longitudinal Burden | Aggregate prior chronic disease count or years of longitudinal history | Derived from Checked Conditions |
| `26` | **`has_hist_43530652`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Chronic Intractable Migraine at or before index encounter | Multi-select Condition Checkbox |
| `27` | **`has_hist_436096`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Chronic Pain at or before index encounter | Multi-select Condition Checkbox |
| `28` | **`has_hist_439777`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Anemia at or before index encounter | Multi-select Condition Checkbox |
| `29` | **`has_hist_378419`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Alzheimer's Disease at or before index encounter | Multi-select Condition Checkbox |
| `30` | **`has_hist_4310703`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Non-Small Cell Carcinoma of Lung, Stage 1 at or before index encounter | Multi-select Condition Checkbox |
| `31` | **`has_hist_4285898`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Polyp of Colon at or before index encounter | Multi-select Condition Checkbox |
| `32` | **`has_hist_4115276`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Non-Small Cell Lung Cancer at or before index encounter | Multi-select Condition Checkbox |
| `33` | **`has_hist_4311629`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Prediabetes at or before index encounter | Multi-select Condition Checkbox |
| `34` | **`has_hist_4229440`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Chronic Kidney Disease at or before index encounter | Multi-select Condition Checkbox |
| `35` | **`has_hist_257012`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Chronic Sinusitis at or before index encounter | Multi-select Condition Checkbox |
| `36` | **`has_hist_4283893`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Sinusitis at or before index encounter | Multi-select Condition Checkbox |
| `37` | **`has_hist_4129902`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Neoplasm of Prostate at or before index encounter | Multi-select Condition Checkbox |
| `38` | **`has_hist_317576`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Coronary Arteriosclerosis at or before index encounter | Multi-select Condition Checkbox |
| `39` | **`has_hist_432867`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Hyperlipidemia at or before index encounter | Multi-select Condition Checkbox |
| `40` | **`has_hist_316866`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Essential Hypertension at or before index encounter | Multi-select Condition Checkbox |
| `41` | **`has_hist_200970`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Carcinoma in situ of Prostate at or before index encounter | Multi-select Condition Checkbox |
| `42` | **`has_hist_80502`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Osteoporosis at or before index encounter | Multi-select Condition Checkbox |
| `43` | **`has_hist_381316`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Stroke (Cerebrovascular Accident) at or before index encounter | Multi-select Condition Checkbox |
| `44` | **`has_hist_37017023`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Recurrent Rectal Polyp at or before index encounter | Multi-select Condition Checkbox |
| `45` | **`has_hist_4079750`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Osteoarthritis of Knee at or before index encounter | Multi-select Condition Checkbox |
| `46` | **`has_hist_436940`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Metabolic Syndrome X at or before index encounter | Multi-select Condition Checkbox |
| `47` | **`has_hist_4120314`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Hypertriglyceridemia at or before index encounter | Multi-select Condition Checkbox |
| `48` | **`has_hist_4214376`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Hyperglycemia at or before index encounter | Multi-select Condition Checkbox |
| `49` | **`has_hist_37395648`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Small Cell Carcinoma of Lung, Stage 1 at or before index encounter | Multi-select Condition Checkbox |
| `50` | **`has_hist_4110591`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Small Cell Carcinoma of Lung at or before index encounter | Multi-select Condition Checkbox |
| `51` | **`has_hist_201826`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Type 2 Diabetes Mellitus at or before index encounter | Multi-select Condition Checkbox |
| `52` | **`has_hist_4043241`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Familial Alzheimer's Disease at or before index encounter | Multi-select Condition Checkbox |
| `53` | **`has_hist_380378`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Epilepsy / Seizure Disorder at or before index encounter | Multi-select Condition Checkbox |
| `54` | **`has_hist_192279`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Congestive Heart Failure at or before index encounter | Multi-select Condition Checkbox |
| `55` | **`has_hist_443614`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Chronic Kidney Disease Stage 1 at or before index encounter | Multi-select Condition Checkbox |
| `56` | **`has_hist_258780`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Chronic Obstructive Bronchitis (COPD) at or before index encounter | Multi-select Condition Checkbox |
| `57` | **`has_hist_4180790`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Malignant Neoplasm of Colon at or before index encounter | Multi-select Condition Checkbox |
| `58` | **`has_hist_79740`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Primary Malignant Neoplasm of Colon at or before index encounter | Multi-select Condition Checkbox |
| `59` | **`has_hist_37016354`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Neuropathy due to Type 2 Diabetes at or before index encounter | Multi-select Condition Checkbox |
| `60` | **`has_hist_4226121`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Retinopathy due to Type 2 Diabetes at or before index encounter | Multi-select Condition Checkbox |
| `61` | **`has_hist_75036`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Localized Osteoarthritis of Hand at or before index encounter | Multi-select Condition Checkbox |
| `62` | **`has_hist_4029498`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Seizure Disorder at or before index encounter | Multi-select Condition Checkbox |
| `63` | **`has_hist_4079749`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Osteoarthritis of Hip at or before index encounter | Multi-select Condition Checkbox |
| `64` | **`has_hist_321042`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Cardiac Arrest at or before index encounter | Multi-select Condition Checkbox |
| `65` | **`has_hist_4051466`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Childhood Asthma at or before index encounter | Multi-select Condition Checkbox |
| `66` | **`has_hist_440086`** | `INTEGER` | Pre-Landmark Target History | Binary indicator: Patient already has Childhood ADHD at or before index encounter | Multi-select Condition Checkbox |
| `67` | **`bg_normal_bmi`** | `INTEGER` | Background Comorbidity | Binary indicator: Pre-landmark presence of high-prevalence background condition | Multi-select Condition Checkbox |
| `68` | **`bg_viral_sinusitis`** | `INTEGER` | Background Comorbidity | Binary indicator: Pre-landmark presence of high-prevalence background condition | Multi-select Condition Checkbox |
| `69` | **`bg_acute_bronchitis`** | `INTEGER` | Background Comorbidity | Binary indicator: Pre-landmark presence of high-prevalence background condition | Multi-select Condition Checkbox |
| `70` | **`bg_strep_or_pregnancy`** | `INTEGER` | Background Comorbidity | Binary indicator: Pre-landmark presence of high-prevalence background condition | Multi-select Condition Checkbox |
| `71` | **`bg_normal_pregnancy`** | `INTEGER` | Background Comorbidity | Binary indicator: Pre-landmark presence of high-prevalence background condition | Multi-select Condition Checkbox |
| `72` | **`bg_miscarriage`** | `INTEGER` | Background Comorbidity | Binary indicator: Pre-landmark presence of high-prevalence background condition | Multi-select Condition Checkbox |
| `73` | **`bg_otitis_media`** | `INTEGER` | Background Comorbidity | Binary indicator: Pre-landmark presence of high-prevalence background condition | Multi-select Condition Checkbox |
| `74` | **`bg_viral_pharyngitis`** | `INTEGER` | Background Comorbidity | Binary indicator: Pre-landmark presence of high-prevalence background condition | Multi-select Condition Checkbox |
| `75` | **`bg_appendicitis`** | `INTEGER` | Background Comorbidity | Binary indicator: Pre-landmark presence of high-prevalence background condition | Multi-select Condition Checkbox |
| `76` | **`bg_cystitis_uti`** | `INTEGER` | Background Comorbidity | Binary indicator: Pre-landmark presence of high-prevalence background condition | Multi-select Condition Checkbox |
| `77` | **`bg_gout`** | `INTEGER` | Background Comorbidity | Binary indicator: Pre-landmark presence of high-prevalence background condition | Multi-select Condition Checkbox |
| `78` | **`bg_alcohol_dependence`** | `INTEGER` | Background Comorbidity | Binary indicator: Pre-landmark presence of high-prevalence background condition | Multi-select Condition Checkbox |
| `79` | **`bg_opioid_use`** | `INTEGER` | Background Comorbidity | Binary indicator: Pre-landmark presence of high-prevalence background condition | Multi-select Condition Checkbox |
| `80` | **`bg_atopic_dermatitis_eczema`** | `INTEGER` | Background Comorbidity | Binary indicator: Pre-landmark presence of high-prevalence background condition | Multi-select Condition Checkbox |
| `81` | **`bg_suspected_condition`** | `INTEGER` | Background Comorbidity | Binary indicator: Pre-landmark presence of high-prevalence background condition | Multi-select Condition Checkbox |
| `82` | **`bg_suspected_respiratory_finding`** | `INTEGER` | Background Comorbidity | Binary indicator: Pre-landmark presence of high-prevalence background condition | Multi-select Condition Checkbox |
| `83` | **`bg_postoperative_state`** | `INTEGER` | Background Comorbidity | Binary indicator: Pre-landmark presence of high-prevalence background condition | Multi-select Condition Checkbox |
| `84` | **`interaction_diabetes_and_hypertension`** | `INTEGER` | Clinical Interaction | Binary interaction term: Concurrent presence of high-risk comorbidity combination | Derived from Checked Conditions |
| `85` | **`interaction_hypertension_and_lipid`** | `INTEGER` | Clinical Interaction | Binary interaction term: Concurrent presence of high-risk comorbidity combination | Derived from Checked Conditions |
| `86` | **`interaction_metabolic_triad`** | `INTEGER` | Clinical Interaction | Binary interaction term: Concurrent presence of high-risk comorbidity combination | Derived from Checked Conditions |
| `87` | **`interaction_cvd_and_ckd`** | `INTEGER` | Clinical Interaction | Binary interaction term: Concurrent presence of high-risk comorbidity combination | Derived from Checked Conditions |
| `88` | **`interaction_copd_and_cvd`** | `INTEGER` | Clinical Interaction | Binary interaction term: Concurrent presence of high-risk comorbidity combination | Derived from Checked Conditions |
| `89` | **`net_max_relative_risk`** | `DOUBLE` | Disease Network Graph | Comorbidity graph relative risk, PageRank, or path length feature | Network Module Contract |
| `90` | **`net_mean_relative_risk`** | `DOUBLE` | Disease Network Graph | Comorbidity graph relative risk, PageRank, or path length feature | Network Module Contract |
| `91` | **`net_n_significant_edges`** | `DOUBLE` | Disease Network Graph | Comorbidity graph relative risk, PageRank, or path length feature | Network Module Contract |
| `92` | **`net_shortest_path_length`** | `DOUBLE` | Disease Network Graph | Comorbidity graph relative risk, PageRank, or path length feature | Network Module Contract |
| `93` | **`net_personalized_pagerank`** | `DOUBLE` | Disease Network Graph | Comorbidity graph relative risk, PageRank, or path length feature | Network Module Contract |
| `94` | **`net_target_degree_centrality`** | `DOUBLE` | Disease Network Graph | Comorbidity graph relative risk, PageRank, or path length feature | Network Module Contract |
| `95` | **`net_target_community_overlap`** | `DOUBLE` | Disease Network Graph | Comorbidity graph relative risk, PageRank, or path length feature | Network Module Contract |
| `96` | **`network_features_available`** | `DOUBLE` | Disease Network Graph | Comorbidity graph relative risk, PageRank, or path length feature | Network Module Contract |