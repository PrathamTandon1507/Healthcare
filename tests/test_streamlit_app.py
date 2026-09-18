"""
Unit test for Phase 18: Streamlit App Integration.
Verifies archetype loading, condition option mapping, and end-to-end headless app compatibility.
"""

import pytest
from streamlit_app.pages.patient_assessment import (
    CLINICAL_ARCHETYPES,
    get_cached_release_bundle
)
from streamlit_app.disease_metadata.registry import CONDITION_REGISTRY
from src.inference.predict import (
    PatientInput,
    predict_patient_comorbidity_risk
)


def test_archetypes_and_condition_options():
    """Verifies that all predefined patient archetypes and condition mappings are valid."""
    archetypes = {k: v for k, v in CLINICAL_ARCHETYPES.items() if v is not None}
    assert len(archetypes) >= 4
    for name, data in archetypes.items():
        assert "age" in data
        assert "gender" in data
        assert "conditions" in data
        assert isinstance(data["conditions"], list)

    assert len(CONDITION_REGISTRY) >= 41 + 17  # 41 targets + 17 background conditions
    for cid, info in CONDITION_REGISTRY.items():
        assert isinstance(cid, int)
        assert len(info.canonical_term) > 0


def test_archetype_inference_end_to_end():
    """Verifies that running prediction on every clinical archetype runs cleanly and adheres to Section 1.5."""
    bundle = get_cached_release_bundle()
    assert bundle.is_loaded

    archetypes = {k: v for k, v in CLINICAL_ARCHETYPES.items() if v is not None}
    for arch_name, arch in archetypes.items():
        p_input = PatientInput(
            age=float(arch["age"]),
            gender=str(arch["gender"]),
            race=str(arch.get("race", "white")),
            ethnicity=str(arch.get("ethnicity", "non_hispanic")),
            current_condition_ids=arch["conditions"] + arch.get("bg_conditions", []),
            prior_obs_years=float(arch.get("prior_obs_years", 3.0))
        )

        result = predict_patient_comorbidity_risk(
            patient_input=p_input,
            bundle=bundle,
            top_n=3,
            threshold_strategy="f1_optimal",
            include_explanations=True,
            mask_existing_conditions=True
        )

        assert len(result.top_ranked_predictions) <= 3
        # Invariant: No diagnosed condition is in candidate predictions
        existing_cids = {c["concept_id"] for c in result.already_diagnosed_conditions}
        for cand in result.all_candidate_predictions:
            assert cand.concept_id not in existing_cids
