"""
Module: streamlit_app.pages.explainability
Page 4: Explainability — Clinical Contributing Factors & Model Consensus.
"""

from typing import Optional, Dict, Any
import streamlit as st
import pandas as pd

from streamlit_app.components.page_header import render_page_header
from streamlit_app.components.medical_term import render_medical_term
from streamlit_app.components.empty_state import render_empty_assessment_state
from streamlit_app.state.session import (
    get_patient,
    get_result,
    get_selected_explanation,
    set_selected_explanation
)
from streamlit_app.disease_metadata.registry import get_condition_info
from streamlit_app.styles.tokens import render_risk_badge_html


def render():
    render_page_header(
        title="Clinical Explainability",
        subtitle="Understand why specific conditions were surfaced by the model, including clinical contributing factors and model consensus."
    )

    result = get_result()
    patient = get_patient()

    if result is None or patient is None:
        render_empty_assessment_state(
            title="No Active Patient Assessment",
            message="Please complete a patient assessment to review clinical explanations and attribution factors.",
            button_label="Start Patient Assessment"
        )
        return

    # 1. Target Condition Selector
    available_items = result.top_ranked_predictions
    if not available_items:
        st.warning("No candidate predictions available for explanation.")
        return

    selected_cid = get_selected_explanation()
    cid_list = [it.concept_id for it in available_items]
    
    # Default to first top-ranked condition if not set or invalid
    if selected_cid not in cid_list:
        selected_cid = cid_list[0]
        set_selected_explanation(selected_cid)

    selected_idx = cid_list.index(selected_cid)

    st.markdown("### Select Condition to Explain")
    
    def format_item_choice(cid: int) -> str:
        info = get_condition_info(cid)
        matching_item = next((it for it in available_items if it.concept_id == cid), None)
        risk_str = f" ({matching_item.calibrated_risk * 100:.1f}% risk — {matching_item.risk_tier})" if matching_item else ""
        return f"{info.canonical_term}{risk_str}"

    chosen_cid = st.selectbox(
        "Select comorbidity",
        options=cid_list,
        index=selected_idx,
        format_func=format_item_choice,
        label_visibility="collapsed",
        key="exp_target_selector"
    )
    
    if chosen_cid != selected_cid:
        set_selected_explanation(chosen_cid)
        selected_cid = chosen_cid

    current_item = next(it for it in available_items if it.concept_id == selected_cid)
    info = get_condition_info(selected_cid)

    st.markdown("<hr />", unsafe_allow_html=True)

    # 2. Condition Overview Box
    with st.container():
        st.markdown(
            f"""
            <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-left: 4px solid #1E3A8A; 
                        border-radius: 6px; padding: 1.25rem 1.35rem; margin-bottom: 1.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                    <div>
                        <span style="font-size: 1.2rem; font-weight: 800; color: #0F172A;">{info.canonical_term}</span>
                        <span style="color: #64748B; font-size: 0.82rem; margin-left: 8px; font-family: monospace;">OMOP: {selected_cid}</span>
                    </div>
                    <div>
                        {render_risk_badge_html(current_item.calibrated_risk, current_item.decision_threshold, current_item.relative_risk_multiplier)}
                    </div>
                </div>
                <p style="color: #334155; font-size: 0.90rem; margin: 0; line-height: 1.5;">
                    {info.plain_language_explanation}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 3. Layer 1: Plain-Language Clinical Drivers (Section 19)
    st.markdown("### Why was this condition surfaced?")
    st.markdown(
        '<p class="page-subtitle">Human-readable clinical drivers contributing toward or mitigating future risk.</p>',
        unsafe_allow_html=True
    )

    explanation_data = current_item.explanation or {}
    risk_increasing = explanation_data.get("top_risk_increasing_factors", [])
    protective = explanation_data.get("top_protective_factors", [])

    col_risk, col_prot = st.columns(2)
    with col_risk:
        st.markdown(
            """
            <div style="background-color: #FFFFFF; border: 1px solid #FCA5A5; border-top: 3px solid #DC2626; border-radius: 6px; padding: 1.15rem; height: 100%;">
                <div style="font-weight: 700; color: #991B1B; font-size: 0.95rem; margin-bottom: 0.65rem;">
                    Risk-Increasing Factors
                </div>
            """,
            unsafe_allow_html=True
        )
        if risk_increasing:
            for factor in risk_increasing:
                st.markdown(
                    f'<div style="font-size: 0.88rem; color: #1E293B; margin-bottom: 8px; display: flex; align-items: baseline; gap: 6px;">'
                    f'<span style="color: #DC2626; font-weight: 700;">↑</span> <span>{factor["feature_description"]}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.markdown('<p style="font-size: 0.85rem; color: #64748B; font-style: italic;">No specific clinical risk-elevating conditions identified.</p>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_prot:
        st.markdown(
            """
            <div style="background-color: #FFFFFF; border: 1px solid #CBD5E1; border-top: 3px solid #64748B; border-radius: 6px; padding: 1.15rem; height: 100%;">
                <div style="font-weight: 700; color: #334155; font-size: 0.95rem; margin-bottom: 0.65rem;">
                    Lower-Risk / Mitigating Factors
                </div>
            """,
            unsafe_allow_html=True
        )
        if protective:
            for factor in protective:
                st.markdown(
                    f'<div style="font-size: 0.88rem; color: #1E293B; margin-bottom: 8px; display: flex; align-items: baseline; gap: 6px;">'
                    f'<span style="color: #2563EB; font-weight: 700;">↓</span> <span>{factor["feature_description"]}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.markdown('<p style="font-size: 0.85rem; color: #64748B; font-style: italic;">No specific mitigating factors identified.</p>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr />", unsafe_allow_html=True)

    # 4. Layer 2: Technical Model Information (Section 20 - Collapsed progressive disclosure)
    with st.expander("Technical Model Details (Base Estimator Consensus & Stacking Weights)", expanded=False):
        st.markdown(
            '<p style="color: #64748B; font-size: 0.86rem; margin-bottom: 0.75rem;">'
            'Individual predictions from base learners prior to meta-learner aggregation and isotonic calibration.'
            '</p>',
            unsafe_allow_html=True
        )

        model_contribs = explanation_data.get("model_contributions", {})
        meta_weights = explanation_data.get("meta_weights", {})

        c_lr, c_rf, c_xgb, c_meta = st.columns(4)
        with c_lr:
            lr_prob = model_contribs.get("logistic_regression", 0.0)
            st.metric("Logistic Regression", f"{lr_prob * 100:.1f}%")
        with c_rf:
            rf_prob = model_contribs.get("random_forest", 0.0)
            st.metric("Random Forest", f"{rf_prob * 100:.1f}%")
        with c_xgb:
            xgb_prob = model_contribs.get("xgboost", 0.0)
            st.metric("XGBoost", f"{xgb_prob * 100:.1f}%")
        with c_meta:
            final_prob = current_item.calibrated_risk
            st.metric("Calibrated Ensemble", f"{final_prob * 100:.1f}%")

        if meta_weights:
            st.markdown("**Meta-Learner Blending Weights:**")
            mw_df = pd.DataFrame([
                {"Model": "Logistic Regression", "Weight": f"{meta_weights.get('logistic_regression', 0.0):.3f}"},
                {"Model": "Random Forest", "Weight": f"{meta_weights.get('random_forest', 0.0):.3f}"},
                {"Model": "XGBoost", "Weight": f"{meta_weights.get('xgboost', 0.0):.3f}"}
            ])
            st.dataframe(mw_df, hide_index=True, use_container_width=True)

    # Footer navigation
    col_ret, col_atlas = st.columns([0.5, 0.5])
    with col_ret:
        if st.button("← Back to Risk Results", use_container_width=True):
            from streamlit_app.navigation.router import PAGE_RESULTS
            st.switch_page(PAGE_RESULTS)
    with col_atlas:
        if st.button("Browse Disease Explorer →", use_container_width=True):
            from streamlit_app.navigation.router import PAGE_EXPLORER
            st.switch_page(PAGE_EXPLORER)


if __name__ == "__main__":
    render()