"""
Module: streamlit_app.disease_metadata.registry
Phase 18 UI Redesign: Structured Clinical Disease & Metadata Layer.

Implements Section 6.5 of UI_REDESIGN_PLAN.md:
- Structured lookup keyed by OMOP concept ID.
- Canonical medical terminology (exact, non-simplified).
- Clinically verified 1-sentence plain-language explanation for patients and clinicians.
- Clinical category classification.
- Indicator whether the condition is an incident prediction target (K=41) or background history feature (17).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class ConditionInfo:
    concept_id: int
    canonical_term: str
    plain_language_explanation: str
    category: str
    is_target: bool
    is_background: bool
    icd10_hint: Optional[str] = None


# Clinical Category Grouping List
CLINICAL_CATEGORIES: List[str] = [
    "Cardiometabolic",
    "Respiratory / Allergic",
    "Musculoskeletal",
    "Oncology / Pre-Malignant",
    "Neurological / Mental Health",
    "Renal & Urological",
    "Diabetic Complication",
    "Hematology",
    "Background History"
]

# Clinical Registry of all 41 Target Comorbidities and 17 Background Conditions
CONDITION_REGISTRY: Dict[int, ConditionInfo] = {
    # -------------------------------------------------------------------------
    # 1. CARDIOMETABOLIC & VASCULAR (Target 41)
    # -------------------------------------------------------------------------
    201826: ConditionInfo(
        concept_id=201826,
        canonical_term="Type 2 Diabetes Mellitus",
        plain_language_explanation="A chronic metabolic disorder where the body cannot effectively use or produce enough insulin to regulate blood glucose.",
        category="Cardiometabolic",
        is_target=True,
        is_background=False,
        icd10_hint="E11"
    ),
    316866: ConditionInfo(
        concept_id=316866,
        canonical_term="Essential Hypertension",
        plain_language_explanation="Persistently elevated blood pressure in the arteries that increases the workload on the heart and blood vessels.",
        category="Cardiometabolic",
        is_target=True,
        is_background=False,
        icd10_hint="I10"
    ),
    432867: ConditionInfo(
        concept_id=432867,
        canonical_term="Hyperlipidemia",
        plain_language_explanation="Abnormally high levels of lipids (fats and cholesterol) in the blood, predisposing to arterial plaque buildup.",
        category="Cardiometabolic",
        is_target=True,
        is_background=False,
        icd10_hint="E78.5"
    ),
    4120314: ConditionInfo(
        concept_id=4120314,
        canonical_term="Hypertriglyceridemia",
        plain_language_explanation="An elevated concentration of triglycerides in the bloodstream associated with increased cardiovascular risk.",
        category="Cardiometabolic",
        is_target=True,
        is_background=False,
        icd10_hint="E78.1"
    ),
    4311629: ConditionInfo(
        concept_id=4311629,
        canonical_term="Prediabetes",
        plain_language_explanation="Blood glucose levels that are elevated above normal but not yet high enough for a diagnosis of type 2 diabetes.",
        category="Cardiometabolic",
        is_target=True,
        is_background=False,
        icd10_hint="R73.03"
    ),
    436940: ConditionInfo(
        concept_id=436940,
        canonical_term="Metabolic Syndrome X",
        plain_language_explanation="A cluster of co-occurring conditions (obesity, high blood pressure, elevated blood sugar, and abnormal cholesterol) that heighten heart disease risk.",
        category="Cardiometabolic",
        is_target=True,
        is_background=False,
        icd10_hint="E88.81"
    ),
    317576: ConditionInfo(
        concept_id=317576,
        canonical_term="Coronary Arteriosclerosis",
        plain_language_explanation="Hardening and narrowing of the coronary arteries supplying oxygen-rich blood to the heart muscle.",
        category="Cardiometabolic",
        is_target=True,
        is_background=False,
        icd10_hint="I25.1"
    ),
    192279: ConditionInfo(
        concept_id=192279,
        canonical_term="Congestive Heart Failure",
        plain_language_explanation="A chronic, progressive condition in which the heart muscle cannot pump sufficient blood to meet the body's metabolic requirements.",
        category="Cardiometabolic",
        is_target=True,
        is_background=False,
        icd10_hint="I50.9"
    ),
    321042: ConditionInfo(
        concept_id=321042,
        canonical_term="Cardiac Arrest",
        plain_language_explanation="A sudden, abrupt cessation of cardiac mechanical activity causing loss of effective blood circulation.",
        category="Cardiometabolic",
        is_target=True,
        is_background=False,
        icd10_hint="I46.9"
    ),
    4214376: ConditionInfo(
        concept_id=4214376,
        canonical_term="Hyperglycemia",
        plain_language_explanation="Elevated concentration of glucose circulating in the blood plasma.",
        category="Cardiometabolic",
        is_target=True,
        is_background=False,
        icd10_hint="R73.9"
    ),

    # -------------------------------------------------------------------------
    # 2. DIABETIC COMPLICATIONS (Target 41)
    # -------------------------------------------------------------------------
    37016354: ConditionInfo(
        concept_id=37016354,
        canonical_term="Neuropathy due to Type 2 Diabetes",
        plain_language_explanation="Peripheral nerve damage caused by chronic high blood sugar, leading to numbness, tingling, or pain in the extremities.",
        category="Diabetic Complication",
        is_target=True,
        is_background=False,
        icd10_hint="E11.40"
    ),
    4226121: ConditionInfo(
        concept_id=4226121,
        canonical_term="Retinopathy due to Type 2 Diabetes",
        plain_language_explanation="Damage to the microvascular blood vessels of the retina resulting from chronic hyperglycemia.",
        category="Diabetic Complication",
        is_target=True,
        is_background=False,
        icd10_hint="E11.31"
    ),

    # -------------------------------------------------------------------------
    # 3. RENAL & UROLOGICAL CHRONIC (Target 41)
    # -------------------------------------------------------------------------
    4229440: ConditionInfo(
        concept_id=4229440,
        canonical_term="Chronic Kidney Disease",
        plain_language_explanation="Gradual, progressive loss of renal function over months or years, impairing waste filtration.",
        category="Renal & Urological",
        is_target=True,
        is_background=False,
        icd10_hint="N18.9"
    ),
    443614: ConditionInfo(
        concept_id=443614,
        canonical_term="Chronic Kidney Disease Stage 1",
        plain_language_explanation="Early-stage kidney damage with normal or near-normal glomerular filtration rate (GFR >= 90 mL/min).",
        category="Renal & Urological",
        is_target=True,
        is_background=False,
        icd10_hint="N18.1"
    ),

    # -------------------------------------------------------------------------
    # 4. NEUROLOGICAL & MENTAL HEALTH (Target 41)
    # -------------------------------------------------------------------------
    381316: ConditionInfo(
        concept_id=381316,
        canonical_term="Stroke (Cerebrovascular Accident)",
        plain_language_explanation="Sudden neurological impairment resulting from interrupted cerebral blood flow or acute intracranial hemorrhage.",
        category="Neurological / Mental Health",
        is_target=True,
        is_background=False,
        icd10_hint="I63.9"
    ),
    378419: ConditionInfo(
        concept_id=378419,
        canonical_term="Alzheimer's Disease",
        plain_language_explanation="A progressive neurodegenerative brain disease causing memory loss, cognitive decline, and behavioral changes.",
        category="Neurological / Mental Health",
        is_target=True,
        is_background=False,
        icd10_hint="G30.9"
    ),
    4043241: ConditionInfo(
        concept_id=4043241,
        canonical_term="Familial Alzheimer's Disease",
        plain_language_explanation="An early-onset, genetically linked hereditary variant of Alzheimer\'s neurodegenerative disease.",
        category="Neurological / Mental Health",
        is_target=True,
        is_background=False,
        icd10_hint="G30.0"
    ),
    380378: ConditionInfo(
        concept_id=380378,
        canonical_term="Epilepsy / Seizure Disorder",
        plain_language_explanation="A neurological condition characterized by recurrent, unprovoked surges of electrical activity in the brain.",
        category="Neurological / Mental Health",
        is_target=True,
        is_background=False,
        icd10_hint="G40.9"
    ),
    4029498: ConditionInfo(
        concept_id=4029498,
        canonical_term="Seizure Disorder",
        plain_language_explanation="A chronic neurological condition predisposing to spontaneous, repeated paroxysmal seizures.",
        category="Neurological / Mental Health",
        is_target=True,
        is_background=False,
        icd10_hint="G40.8"
    ),
    440086: ConditionInfo(
        concept_id=440086,
        canonical_term="Childhood ADHD",
        plain_language_explanation="A neurodevelopmental condition marked by persistent patterns of inattention, hyperactivity, and impulsivity.",
        category="Neurological / Mental Health",
        is_target=True,
        is_background=False,
        icd10_hint="F90.0"
    ),

    # -------------------------------------------------------------------------
    # 5. RESPIRATORY & ALLERGIC (Target 41)
    # -------------------------------------------------------------------------
    258780: ConditionInfo(
        concept_id=258780,
        canonical_term="Chronic Obstructive Bronchitis (COPD)",
        plain_language_explanation="A progressive lung disease that causes chronic airflow limitation, shortness of breath, and productive cough.",
        category="Respiratory / Allergic",
        is_target=True,
        is_background=False,
        icd10_hint="J44.9"
    ),
    4051466: ConditionInfo(
        concept_id=4051466,
        canonical_term="Childhood Asthma",
        plain_language_explanation="A chronic inflammatory airway condition characterized by variable wheezing, coughing, and bronchial hyperreactivity.",
        category="Respiratory / Allergic",
        is_target=True,
        is_background=False,
        icd10_hint="J45.20"
    ),
    257012: ConditionInfo(
        concept_id=257012,
        canonical_term="Chronic Sinusitis",
        plain_language_explanation="Persistent inflammation and swelling of the paranasal sinus passages lasting twelve weeks or longer.",
        category="Respiratory / Allergic",
        is_target=True,
        is_background=False,
        icd10_hint="J32.9"
    ),
    4283893: ConditionInfo(
        concept_id=4283893,
        canonical_term="Sinusitis",
        plain_language_explanation="Inflammation of the mucosal lining of the paranasal sinuses causing nasal congestion and facial pain.",
        category="Respiratory / Allergic",
        is_target=True,
        is_background=False,
        icd10_hint="J01.9"
    ),

    # -------------------------------------------------------------------------
    # 6. MUSCULOSKELETAL & DEGENERATIVE (Target 41)
    # -------------------------------------------------------------------------
    75036: ConditionInfo(
        concept_id=75036,
        canonical_term="Localized Osteoarthritis of Hand",
        plain_language_explanation="Degenerative joint disease of the finger joints leading to cartilage breakdown, joint stiffness, and chronic pain.",
        category="Musculoskeletal",
        is_target=True,
        is_background=False,
        icd10_hint="M19.04"
    ),
    4079749: ConditionInfo(
        concept_id=4079749,
        canonical_term="Osteoarthritis of Hip",
        plain_language_explanation="Wear and breakdown of protective cartilage in the hip joint causing groin stiffness and walking difficulty.",
        category="Musculoskeletal",
        is_target=True,
        is_background=False,
        icd10_hint="M16.9"
    ),
    4079750: ConditionInfo(
        concept_id=4079750,
        canonical_term="Osteoarthritis of Knee",
        plain_language_explanation="Chronic wear-and-tear degradation of the knee joint cartilage resulting in pain, swelling, and reduced mobility.",
        category="Musculoskeletal",
        is_target=True,
        is_background=False,
        icd10_hint="M17.9"
    ),
    80502: ConditionInfo(
        concept_id=80502,
        canonical_term="Osteoporosis",
        plain_language_explanation="A bone-weakening disease characterized by decreased bone mass and architectural deterioration, predisposing to fractures.",
        category="Musculoskeletal",
        is_target=True,
        is_background=False,
        icd10_hint="M81.0"
    ),
    436096: ConditionInfo(
        concept_id=436096,
        canonical_term="Chronic Pain",
        plain_language_explanation="Persistent or recurrent discomfort that extends beyond typical tissue healing time (greater than three months).",
        category="Musculoskeletal",
        is_target=True,
        is_background=False,
        icd10_hint="G89.4"
    ),
    43530652: ConditionInfo(
        concept_id=43530652,
        canonical_term="Chronic Intractable Migraine",
        plain_language_explanation="Severe, debilitating headache episodes occurring fifteen or more days per month that do not respond to standard acute therapies.",
        category="Musculoskeletal",
        is_target=True,
        is_background=False,
        icd10_hint="G43.919"
    ),

    # -------------------------------------------------------------------------
    # 7. ONCOLOGY & PRE-MALIGNANT (Target 41)
    # -------------------------------------------------------------------------
    4285898: ConditionInfo(
        concept_id=4285898,
        canonical_term="Polyp of Colon",
        plain_language_explanation="A benign mucosal growth projecting from the inner lining of the large intestine with potential pre-cancerous transformation.",
        category="Oncology / Pre-Malignant",
        is_target=True,
        is_background=False,
        icd10_hint="D12.6"
    ),
    37017023: ConditionInfo(
        concept_id=37017023,
        canonical_term="Recurrent Rectal Polyp",
        plain_language_explanation="Repeated formation of mucosal adenomas within the rectal vault requiring longitudinal endoscopic surveillance.",
        category="Oncology / Pre-Malignant",
        is_target=True,
        is_background=False,
        icd10_hint="K62.1"
    ),
    4129902: ConditionInfo(
        concept_id=4129902,
        canonical_term="Neoplasm of Prostate",
        plain_language_explanation="An abnormal proliferative growth of prostatic gland tissue requiring diagnostic characterization.",
        category="Oncology / Pre-Malignant",
        is_target=True,
        is_background=False,
        icd10_hint="D40.0"
    ),
    200970: ConditionInfo(
        concept_id=200970,
        canonical_term="Carcinoma in situ of Prostate",
        plain_language_explanation="Localized high-grade pre-invasive neoplastic cellular changes confined to the prostatic epithelium.",
        category="Oncology / Pre-Malignant",
        is_target=True,
        is_background=False,
        icd10_hint="D07.5"
    ),
    4115276: ConditionInfo(
        concept_id=4115276,
        canonical_term="Non-Small Cell Lung Cancer",
        plain_language_explanation="The most common histological classification of malignant epithelial lung tumors, including adenocarcinoma and squamous carcinoma.",
        category="Oncology / Pre-Malignant",
        is_target=True,
        is_background=False,
        icd10_hint="C34.90"
    ),
    4310703: ConditionInfo(
        concept_id=4310703,
        canonical_term="Non-Small Cell Carcinoma of Lung, Stage 1",
        plain_language_explanation="Early-stage primary lung malignancy strictly localized to the lung parenchyma without lymph node involvement.",
        category="Oncology / Pre-Malignant",
        is_target=True,
        is_background=False,
        icd10_hint="C34.91"
    ),
    4110591: ConditionInfo(
        concept_id=4110591,
        canonical_term="Small Cell Carcinoma of Lung",
        plain_language_explanation="An aggressive neuroendocrine lung tumor strongly associated with heavy tobacco exposure that grows and disseminates rapidly.",
        category="Oncology / Pre-Malignant",
        is_target=True,
        is_background=False,
        icd10_hint="C34.92"
    ),
    37395648: ConditionInfo(
        concept_id=37395648,
        canonical_term="Small Cell Carcinoma of Lung, Stage 1",
        plain_language_explanation="Very early localized small-cell neuroendocrine malignancy confined to a single hemithorax.",
        category="Oncology / Pre-Malignant",
        is_target=True,
        is_background=False,
        icd10_hint="C34.93"
    ),
    4180790: ConditionInfo(
        concept_id=4180790,
        canonical_term="Malignant Neoplasm of Colon",
        plain_language_explanation="Cancerous adenocarcinoma originating from the mucosal epithelial lining of the large bowel.",
        category="Oncology / Pre-Malignant",
        is_target=True,
        is_background=False,
        icd10_hint="C18.9"
    ),
    79740: ConditionInfo(
        concept_id=79740,
        canonical_term="Primary Malignant Neoplasm of Colon",
        plain_language_explanation="Primary invasive malignant epithelial tumor of the colon.",
        category="Oncology / Pre-Malignant",
        is_target=True,
        is_background=False,
        icd10_hint="C18.0"
    ),

    # -------------------------------------------------------------------------
    # 8. HEMATOLOGY (Target 41)
    # -------------------------------------------------------------------------
    439777: ConditionInfo(
        concept_id=439777,
        canonical_term="Anemia",
        plain_language_explanation="A clinical deficiency in the number of red blood cells or concentration of hemoglobin, diminishing systemic oxygenation.",
        category="Hematology",
        is_target=True,
        is_background=False,
        icd10_hint="D64.9"
    ),

    # -------------------------------------------------------------------------
    # 9. BACKGROUND CLINICAL HISTORY (17 Informative History Features)
    # -------------------------------------------------------------------------
    4112343: ConditionInfo(
        concept_id=4112343,
        canonical_term="Normal Body Mass Index",
        plain_language_explanation="Documented body mass index within the healthy clinical range (18.5 - 24.9 kg/m2).",
        category="Background History",
        is_target=False,
        is_background=True,
        icd10_hint="Z68.2"
    ),
    40481087: ConditionInfo(
        concept_id=40481087,
        canonical_term="Viral Sinusitis",
        plain_language_explanation="Self-limiting acute viral upper respiratory infection of the nasal and sinus passages.",
        category="Background History",
        is_target=False,
        is_background=True,
        icd10_hint="J01.90"
    ),
    260139: ConditionInfo(
        concept_id=260139,
        canonical_term="Acute Bronchitis",
        plain_language_explanation="Short-term inflammatory condition of the bronchial passages usually resolving within 2 to 3 weeks.",
        category="Background History",
        is_target=False,
        is_background=True,
        icd10_hint="J20.9"
    ),
    28060: ConditionInfo(
        concept_id=28060,
        canonical_term="Streptococcal Pharyngitis / Normal Pregnancy History",
        plain_language_explanation="Prior documented history of streptococcal throat infection or obstetric episode.",
        category="Background History",
        is_target=False,
        is_background=True,
        icd10_hint="J02.0"
    ),
    4217975: ConditionInfo(
        concept_id=4217975,
        canonical_term="Normal Pregnancy",
        plain_language_explanation="Prior documented full-term uncomplicated pregnancy in historical record.",
        category="Background History",
        is_target=False,
        is_background=True,
        icd10_hint="Z34.9"
    ),
    4078393: ConditionInfo(
        concept_id=4078393,
        canonical_term="Miscarriage (Spontaneous Abortion)",
        plain_language_explanation="Historical spontaneous loss of pregnancy prior to 20 weeks gestational age.",
        category="Background History",
        is_target=False,
        is_background=True,
        icd10_hint="O03.9"
    ),
    372328: ConditionInfo(
        concept_id=372328,
        canonical_term="Otitis Media",
        plain_language_explanation="Documented episode of middle ear infection and inflammation.",
        category="Background History",
        is_target=False,
        is_background=True,
        icd10_hint="H66.90"
    ),
    4294548: ConditionInfo(
        concept_id=4294548,
        canonical_term="Acute Viral Pharyngitis",
        plain_language_explanation="Acute inflammatory infection of the pharynx resulting in sore throat.",
        category="Background History",
        is_target=False,
        is_background=True,
        icd10_hint="J02.9"
    ),
    440448: ConditionInfo(
        concept_id=440448,
        canonical_term="Appendicitis",
        plain_language_explanation="Acute inflammation of the vermiform appendix requiring medical evaluation or surgical resection.",
        category="Background History",
        is_target=False,
        is_background=True,
        icd10_hint="K35.80"
    ),
    195588: ConditionInfo(
        concept_id=195588,
        canonical_term="Cystitis (Urinary Tract Infection)",
        plain_language_explanation="Prior episode of bacterial infection of the bladder and lower urinary tract.",
        category="Background History",
        is_target=False,
        is_background=True,
        icd10_hint="N30.0"
    ),
    440674: ConditionInfo(
        concept_id=440674,
        canonical_term="Gout",
        plain_language_explanation="Recurrent inflammatory arthritis caused by monosodium urate crystal deposition in joints.",
        category="Background History",
        is_target=False,
        is_background=True,
        icd10_hint="M10.9"
    ),
    7200002: ConditionInfo(
        concept_id=7200002,
        canonical_term="Alcoholism / Alcohol Dependence",
        plain_language_explanation="Documented history of chronic alcohol use disorder with physiological dependence.",
        category="Background History",
        is_target=False,
        is_background=True,
        icd10_hint="F10.2"
    ),
    438130: ConditionInfo(
        concept_id=438130,
        canonical_term="Opioid Abuse / Harmful Use",
        plain_language_explanation="Documented pattern of problematic opioid consumption causing clinical impairment.",
        category="Background History",
        is_target=False,
        is_background=True,
        icd10_hint="F11.1"
    ),
    133834: ConditionInfo(
        concept_id=133834,
        canonical_term="Atopic Dermatitis / Eczema",
        plain_language_explanation="Chronic pruritic inflammatory skin disorder frequently associated with allergic diathesis.",
        category="Background History",
        is_target=False,
        is_background=True,
        icd10_hint="L20.9"
    ),
    261325: ConditionInfo(
        concept_id=261325,
        canonical_term="Suspected Condition Finding",
        plain_language_explanation="Clinical evaluation or provisional observation documented during a prior outpatient encounter.",
        category="Background History",
        is_target=False,
        is_background=True,
        icd10_hint="R69"
    ),
    313217: ConditionInfo(
        concept_id=313217,
        canonical_term="Suspected Respiratory Finding",
        plain_language_explanation="Provisional respiratory sign or symptom recorded during an emergency or inpatient evaluation.",
        category="Background History",
        is_target=False,
        is_background=True,
        icd10_hint="R09.8"
    ),
    4146173: ConditionInfo(
        concept_id=4146173,
        canonical_term="Postoperative State",
        plain_language_explanation="Clinical follow-up or recovery status following surgical intervention.",
        category="Background History",
        is_target=False,
        is_background=True,
        icd10_hint="Z98.89"
    )
}

# Common shortcut conditions for 1-click clinical intake selection
COMMON_INTAKE_SHORTCUTS: List[int] = [
    316866,   # Essential Hypertension
    201826,   # Type 2 Diabetes Mellitus
    432867,   # Hyperlipidemia
    4311629,  # Prediabetes
    4051466,  # Childhood Asthma
    75036,    # Localized Osteoarthritis of Hand
    257012,   # Chronic Sinusitis
    43530652  # Chronic Intractable Migraine
]


def get_condition_info(concept_id: int) -> ConditionInfo:
    """Returns ConditionInfo dataclass for concept ID, with safe fallback."""
    if concept_id in CONDITION_REGISTRY:
        return CONDITION_REGISTRY[concept_id]
    return ConditionInfo(
        concept_id=concept_id,
        canonical_term=f"Condition {concept_id}",
        plain_language_explanation="Clinical condition documented in longitudinal electronic health records.",
        category="General",
        is_target=False,
        is_background=False
    )


def search_conditions(
    query: Optional[str] = None,
    category: Optional[str] = None,
    target_only: bool = False
) -> List[ConditionInfo]:
    """Filters clinical condition registry by text substring and/or clinical category."""
    results = list(CONDITION_REGISTRY.values())
    
    if target_only:
        results = [c for c in results if c.is_target]
        
    if category and category != "All Categories":
        results = [c for c in results if c.category.lower() == category.lower()]
        
    if query:
        q = query.strip().lower()
        results = [
            c for c in results
            if q in c.canonical_term.lower() or q in c.plain_language_explanation.lower() or q in str(c.concept_id)
        ]
        
    return results
