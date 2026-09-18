"""
Package: src.inference
Phase 17: Inference Pipeline and Serving Module.

Provides standard entry points for real-time and batch comorbidity risk prediction,
feature encoding, already-diagnosed condition masking, and explainability generation.
"""

from src.inference.predict import (
    PatientInput,
    PredictionItem,
    PatientPredictionResult,
    build_feature_vector_from_patient_input,
    predict_patient_comorbidity_risk,
    batch_predict_patient_comorbidity_risk,
    resolve_condition_identifiers,
    DISEASE_NAME_TO_CID,
    CID_TO_DISEASE_NAME,
    CID_TO_CATEGORY
)

__all__ = [
    "PatientInput",
    "PredictionItem",
    "PatientPredictionResult",
    "build_feature_vector_from_patient_input",
    "predict_patient_comorbidity_risk",
    "batch_predict_patient_comorbidity_risk",
    "resolve_condition_identifiers",
    "DISEASE_NAME_TO_CID",
    "CID_TO_DISEASE_NAME",
    "CID_TO_CATEGORY"
]
