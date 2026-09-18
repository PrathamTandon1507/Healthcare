"""
Unit Tests for Phase 18 UI Redesign & Clinical Intelligence Layer.
Verifies disease metadata registry, design system tokens, session state accessors,
navigation router integrity, and end-to-end UI rendering flows.
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from src.data.labels import TARGET_41_DISEASES
from src.features.pipeline import BACKGROUND_CONDITION_CONCEPTS
from src.inference.predict import (
    PatientInput,
    predict_patient_comorbidity_risk,
    load_release_bundle
)

from streamlit_app.disease_metadata.registry import (
    CONDITION_REGISTRY,
    CLINICAL_CATEGORIES,
    COMMON_INTAKE_SHORTCUTS,
    get_condition_info,
    search_conditions,
    ConditionInfo
)
from streamlit_app.styles.tokens import (
    get_risk_tier,
    render_risk_badge_html,
    RISK_COLORS,
    COLOR_PRIMARY
)
from streamlit_app.state.session import (
    init_session_state,
    set_patient,
    set_result,
    get_patient,
    get_result,
    has_active_assessment,
    clear_assessment,
    set_selected_explanation,
    get_selected_explanation
)
from streamlit_app.navigation.router import (
    get_navigation_router,
    PAGE_OVERVIEW,
    PAGE_ASSESSMENT,
    PAGE_RESULTS,
    PAGE_EXPLAINABILITY,
    PAGE_EXPLORER,
    PAGE_NETWORK,
    PAGE_RESEARCH
)


class TestDiseaseMetadataRegistry:
    """Test suite for clinical disease ontology & plain-language translation layer."""

    def test_all_41_targets_registered(self):
        """Verify that all 41 target concept IDs are registered with valid metadata."""
        for cid in TARGET_41_DISEASES:
            assert cid in CONDITION_REGISTRY, f"Target concept ID {cid} missing from registry"
            info = CONDITION_REGISTRY[cid]
            assert info.is_target is True
            assert info.canonical_term and len(info.canonical_term.strip()) > 0
            assert info.plain_language_explanation and len(info.plain_language_explanation.strip()) > 10
            assert info.category in CLINICAL_CATEGORIES or info.category != ""

    def test_all_17_background_conditions_registered(self):
        """Verify that all 17 background conditions are registered with valid metadata."""
        for cid in BACKGROUND_CONDITION_CONCEPTS.keys():
            assert cid in CONDITION_REGISTRY, f"Background concept ID {cid} missing from registry"
            info = CONDITION_REGISTRY[cid]
            assert info.is_background is True
            assert info.canonical_term and len(info.canonical_term.strip()) > 0
            assert info.plain_language_explanation and len(info.plain_language_explanation.strip()) > 10

    def test_get_condition_info_fallback(self):
        """Verify safe fallback for unknown concept ID."""
        info = get_condition_info(999999999)
        assert isinstance(info, ConditionInfo)
        assert info.concept_id == 999999999
        assert "999999999" in info.canonical_term

    def test_search_conditions_text(self):
        """Verify substring search over terms and explanations."""
        results = search_conditions(query="diabetes")
        assert len(results) >= 1
        cids = [c.concept_id for c in results]
        assert 201826 in cids  # Type 2 Diabetes

    def test_search_conditions_category(self):
        """Verify filtering by clinical category."""
        results = search_conditions(category="Cardiometabolic")
        assert len(results) > 0
        for r in results:
            assert r.category.lower() == "cardiometabolic"

    def test_search_conditions_target_only(self):
        """Verify target_only filter."""
        results = search_conditions(target_only=True)
        assert len(results) == len(TARGET_41_DISEASES)
        for r in results:
            assert r.is_target is True


class TestDesignTokensAndBadges:
    """Test suite for design-system tokens and WCAG risk tiers."""

    def test_get_risk_tier_thresholds(self):
        """Verify probability to risk tier mapping."""
        tier, style = get_risk_tier(0.75, 0.5)
        assert tier == "High"
        assert style["label"] == "High Risk"

        tier, style = get_risk_tier(0.45, 0.5)
        assert tier == "Elevated"

        tier, style = get_risk_tier(0.20, 0.5)
        assert tier == "Moderate"

        tier, style = get_risk_tier(0.05, 0.5)
        assert tier == "Low"

    def test_render_risk_badge_html(self):
        """Verify badge HTML contains accessible text label and multiplier."""
        html = render_risk_badge_html(0.70, 0.5, multiplier=2.4)
        assert "High Risk" in html
        assert "2.4x baseline" in html
        assert "background-color" in html


class TestSessionStateAccessors:
    """Test suite for session state helpers using mock Streamlit session_state."""

    def test_session_state_lifecycle(self):
        mock_state = {}
        with patch("streamlit_app.state.session.st.session_state", mock_state):
            init_session_state()
            assert get_patient() is None
            assert get_result() is None
            assert has_active_assessment() is False

            patient = PatientInput(age=65, gender="Male", current_condition_ids=[201826])
            set_patient(patient, archetype_name="Elderly Diabetic")
            assert get_patient() == patient
            assert mock_state["current_archetype_name"] == "Elderly Diabetic"

            # Create mock result
            mock_res = MagicMock()
            set_result(mock_res)
            assert get_result() == mock_res
            assert has_active_assessment() is True

            set_selected_explanation(201826)
            assert get_selected_explanation() == 201826

            clear_assessment()
            assert get_patient() is None
            assert get_result() is None
            assert has_active_assessment() is False


class TestNavigationRouter:
    """Test suite for multi-page router assembly."""

    def test_router_structure(self):
        with patch("streamlit.navigation") as mock_nav:
            mock_nav.return_value = MagicMock()
            router = get_navigation_router()
            mock_nav.assert_called_once()
            args, kwargs = mock_nav.call_args
            structure = args[0]
            assert "Clinical Workflow" in structure
            assert "Research & Governance" in structure
            assert len(structure["Clinical Workflow"]) == 6
            assert len(structure["Research & Governance"]) == 1


class TestEndToEndPredictionDataFlow:
    """Test suite ensuring inference pipeline outputs match UI presentation requirements."""

    def test_prediction_result_structure_for_ui(self):
        """Verify patient prediction feeds all UI fields: masking, metrics, explanations."""
        bundle = load_release_bundle()
        patient = PatientInput(
            age=68,
            gender="Male",
            race="white",
            ethnicity="non_hispanic",
            current_condition_ids=[201826, 316866, 432867],  # Type 2 DM, HTN, Hyperlipidemia
            prior_obs_years=6.5
        )
        result = predict_patient_comorbidity_risk(
            patient_input=patient,
            bundle=bundle,
            top_n=5,
            threshold_strategy="f1_optimal",
            include_explanations=True,
            mask_existing_conditions=True
        )

        # 1. Verify masking of 3 existing diagnoses
        assert len(result.already_diagnosed_conditions) == 3
        masked_cids = {c["concept_id"] for c in result.already_diagnosed_conditions}
        assert 201826 in masked_cids
        assert 316866 in masked_cids
        assert 432867 in masked_cids

        # 2. Verify candidate items do not contain any masked CIDs
        for item in result.all_candidate_predictions:
            assert item.concept_id not in masked_cids

        # 3. Verify top-N length and explanation payload
        assert len(result.top_ranked_predictions) == 5
        for top_item in result.top_ranked_predictions:
            assert top_item.calibrated_risk >= 0.0
            assert top_item.calibrated_risk <= 1.0
            assert isinstance(top_item.risk_tier, str) and len(top_item.risk_tier) > 0
            assert top_item.explanation is not None

        # 4. Verify dataframe serialization
        df = result.to_dataframe(include_all=False)
        assert len(df) == 5
        assert "Rank" in df.columns
        assert "Calibrated 1-Yr Risk" in df.columns
