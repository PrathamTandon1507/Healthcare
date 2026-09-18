"""
Module: streamlit_app.components.risk_card
Section 7 Reusable Risk Card Component.
Rank, canonical term + plain-language explanation, 3 metrics, "why surfaced" bullet points, "View explanation" CTA.
Styled with White-Blue-Red Clinical Theme.
"""

from typing import Optional, Any
import streamlit as st

from src.inference.predict import PredictionItem
from streamlit_app.disease_metadata.registry import get_condition_info
from streamlit_app.styles.tokens import render_risk_badge_html
from streamlit_app.state.session import set_selected_explanation


def render_risk_card(
    rank: int,
    item: PredictionItem,
    switch_page_target: Optional[Any] = None
) -> None:
    """
    Renders structured clinical risk card meeting Section 7 specifications.
    Pairs clear ranking, plain language translation, accessible metrics, and explainability CTA.
    """
    info = get_condition_info(item.concept_id)
    rank_str = f"{rank:02d}"
    badge_html = render_risk_badge_html(
        prob=item.calibrated_risk,
        threshold=item.decision_threshold,
        multiplier=item.relative_risk_multiplier
    )
    
    # Border accent based on risk tier
    border_left_color = "#DC2626" if item.is_flagged_elevated_risk or item.calibrated_risk >= 0.5 else "#1E3A8A"

    # 1. Card Container Header
    with st.container():
        st.markdown(
            f"""
            <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid {border_left_color}; 
                        border-radius: 8px; padding: 1.35rem 1.5rem 1.15rem 1.5rem; margin-bottom: 1.25rem; 
                        box-shadow: 0 2px 5px rgba(15, 23, 42, 0.04);">
                <div style="display: flex; justify-content: space-between; align-items: center; 
                            border-bottom: 1px solid #F1F5F9; padding-bottom: 0.65rem; margin-bottom: 0.85rem;">
                    <div>
                        <span style="font-size: 1.15rem; font-weight: 800; color: #1E3A8A; margin-right: 10px; 
                                     background-color: #EFF6FF; border: 1px solid #DBEAFE; padding: 2px 8px; border-radius: 4px;">{rank_str}</span>
                        <span style="font-size: 1.15rem; font-weight: 700; color: #0F172A;">{info.canonical_term}</span>
                        <span style="font-size: 0.80rem; color: #64748B; margin-left: 8px; font-family: monospace;">OMOP: {item.concept_id}</span>
                    </div>
                    <div>
                        {badge_html}
                    </div>
                </div>
                <div style="font-size: 0.90rem; color: #334155; line-height: 1.5; margin-bottom: 1rem;">
                    {info.plain_language_explanation}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 2. Key Metrics Row
        col_m1, col_m2, col_m3, col_btn = st.columns([0.25, 0.25, 0.25, 0.25])
        with col_m1:
            st.metric(
                label="1-Year Calibrated Risk",
                value=f"{item.calibrated_risk * 100:.1f}%",
                help=f"Calibrated probability (Raw model output: {item.raw_probability * 100:.1f}%)"
            )
        with col_m2:
            st.metric(
                label="Risk Tier",
                value=item.risk_tier,
                help="Categorical clinical risk tier based on thresholding."
            )
        with col_m3:
            mult_val = f"{item.relative_risk_multiplier:.1f}×" if item.relative_risk_multiplier > 0 else "1.0×"
            st.metric(
                label="Compared to Baseline",
                value=mult_val,
                help=f"Relative risk compared to cohort baseline incidence."
            )
        with col_btn:
            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
            if st.button("View explanation →", key=f"btn_exp_{item.concept_id}", use_container_width=True):
                set_selected_explanation(item.concept_id)
                if switch_page_target is not None:
                    st.switch_page(switch_page_target)
                else:
                    from streamlit_app.navigation.router import PAGE_EXPLAINABILITY
                    st.switch_page(PAGE_EXPLAINABILITY)

        # 3. Why This Was Surfaced (Clinical summary factors)
        if item.explanation and "top_risk_increasing_factors" in item.explanation:
            factors = item.explanation["top_risk_increasing_factors"][:3]
            if factors:
                st.markdown(
                    '<div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 0.75rem 1rem; margin-top: 0.5rem;">'
                    '<span style="font-size: 0.82rem; font-weight: 700; color: #1E3A8A; text-transform: uppercase; letter-spacing: 0.03em;">'
                    'Key Clinical Risk Drivers:</span>',
                    unsafe_allow_html=True
                )
                factor_items = "".join([
                    f'<li style="font-size: 0.86rem; color: #1E293B; margin-bottom: 2px;">{f["feature_description"]}</li>'
                    for f in factors
                ])
                st.markdown(f'<ul style="margin-top: 4px; margin-bottom: 0; padding-left: 1.25rem;">{factor_items}</ul></div>', unsafe_allow_html=True)

        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
