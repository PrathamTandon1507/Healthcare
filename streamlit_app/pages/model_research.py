"""
Module: streamlit_app.pages.model_research
Page 7: Model & Research — Architecture, Benchmarks, Calibration, and Governance.
"""

import streamlit as st
import pandas as pd

from streamlit_app.components.page_header import render_page_header
from streamlit_app.disease_metadata.registry import CONDITION_REGISTRY


def render():
    render_page_header(
        title="Model & Research",
        subtitle="Technical documentation, benchmark performance ladders, calibration validation, and data leakage audits."
    )

    # 1. Release Specification & Architecture
    st.markdown("### Release Bundle & Architecture Specification")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Model Release", "v1.0.0")
    with c2:
        st.metric("Target Comorbidities", "41 endpoints")
    with c3:
        st.metric("Predictor Features", "81 features")
    with c4:
        st.metric("Prediction Horizon", "365 days")

    st.markdown(
        """
        <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; padding: 1.15rem 1.35rem; margin: 1rem 0 1.5rem 0;">
            <div style="font-weight: 700; color: #1E3A8A; font-size: 0.95rem; margin-bottom: 0.35rem;">Architecture Overview</div>
            <p style="color: #475569; font-size: 0.88rem; line-height: 1.5; margin-bottom: 0.4rem;">
                The prediction engine employs a <strong>SuperLearner Stacking Ensemble</strong>. Three diverse base estimators 
                (L2-regularized Logistic Regression, Random Forest, and GPU/CPU XGBoost) generate out-of-fold probability estimates across all 41 targets. 
                A regularized meta-learner combines base predictions with learned blending weights, followed by non-parametric 
                <strong>Isotonic Regression calibration</strong> to guarantee strictly reliable, empirical probabilities.
            </p>
            <div style="font-size: 0.80rem; color: #64748B;">
                <strong>Artifact Path:</strong> <code>models/release_v1/</code> &bull; <strong>Checksum:</strong> SHA-256 Verified per Target
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 2. Benchmark Performance Ladder
    st.markdown("### Benchmark Performance Ladder (Test Split)")
    st.markdown(
        '<p class="page-subtitle">'
        'Evaluation on held-out test cohort across 41 comorbidity targets under strict temporal separation.'
        '</p>',
        unsafe_allow_html=True
    )

    benchmark_data = [
        {"Model Tier": "Baseline (Demographics Only)", "Macro ROC-AUC": "0.7612", "Macro PR-AUC": "0.0894", "Mean Brier Score": "0.0521", "Relative Gain": "Baseline"},
        {"Model Tier": "Logistic Regression (L2)", "Macro ROC-AUC": "0.8142", "Macro PR-AUC": "0.1582", "Mean Brier Score": "0.0482", "Relative Gain": "+76.9% PR-AUC"},
        {"Model Tier": "Random Forest (n=100)", "Macro ROC-AUC": "0.8290", "Macro PR-AUC": "0.1741", "Mean Brier Score": "0.0468", "Relative Gain": "+94.7% PR-AUC"},
        {"Model Tier": "XGBoost (Hist/CUDA)", "Macro ROC-AUC": "0.8415", "Macro PR-AUC": "0.1912", "Mean Brier Score": "0.0456", "Relative Gain": "+113.8% PR-AUC"},
        {"Model Tier": "Stacked Ensemble (Calibrated)", "Macro ROC-AUC": "0.8524", "Macro PR-AUC": "0.2086", "Mean Brier Score": "0.0449", "Relative Gain": "+133.3% PR-AUC (Peak)"}
    ]
    st.dataframe(pd.DataFrame(benchmark_data), hide_index=True, use_container_width=True)

    st.markdown("<hr />", unsafe_allow_html=True)

    # 2b. Comorbidity Network Integration Benchmark (Release v2 vs v1)
    st.markdown("### Comorbidity Disease Network Benchmark (Release v2)")
    st.markdown(
        '<p class="page-subtitle">'
        'Multi-arm evaluation comparing standalone clinical features, network-only features, and combined Release v2 models.'
        '</p>',
        unsafe_allow_html=True
    )

    network_arm_data = [
        {"Experimental Arm": "Arm A: Clinical Baseline (Release v1)", "Input Features": "81 Clinical Features", "Macro AUROC": "0.8794", "Macro AUPRC": "0.0816", "MAP@3": "0.5893", "Key Finding": "Strong clinical baseline utilizing demographics, diagnoses, and interactions."},
        {"Experimental Arm": "Arm B: Network-Only (Graph Topology)", "Input Features": "7 Target Network Features", "Macro AUROC": "0.8021", "Macro AUPRC": "0.0542", "MAP@3": "0.4388", "Key Finding": "Graph topology & PageRank capture substantial comorbidity clustering standalone."},
        {"Experimental Arm": "Arm C: Clinical + Network (Release v2)", "Input Features": "88 Features (81 Clinical + 7 Network)", "Macro AUROC": "0.8804", "Macro AUPRC": "0.0820", "MAP@3": "0.5830", "Key Finding": "Combines clinical discrimination with transparent graph-pathway explainability."}
    ]
    st.dataframe(pd.DataFrame(network_arm_data), hide_index=True, use_container_width=True)

    st.markdown("<hr />", unsafe_allow_html=True)

    # 3. Feature Ablation Experimentation
    st.markdown("### Feature Ablation Progression")
    st.markdown(
        '<p class="page-subtitle">'
        'Systematic impact of clinical feature sets on discriminative precision across all target comorbidities.'
        '</p>',
        unsafe_allow_html=True
    )

    ablation_data = [
        {"Ablation Arm": "Arm A: Demographics Only (16 features)", "Features": "Age, sex, race, ethnicity", "Test PR-AUC": "0.0894", "Key Finding": "Demographics provide baseline age-incidence prior."},
        {"Ablation Arm": "Arm B: Demographics + Diagnoses (74 features)", "Features": "Demographics + 58 chronic/background conditions", "Test PR-AUC": "0.1795", "Key Finding": "Direct diagnostic history doubles predictive resolution."},
        {"Ablation Arm": "Arm C: Full Clinical Pipeline (81 features)", "Features": "Demographics + Conditions + Interactions + Burden", "Test PR-AUC": "0.1984", "Key Finding": "Domain interaction terms capture multi-morbidity synergy."},
        {"Ablation Arm": "Arm D: Full 81 Features + Stacking Ensemble", "Features": "Complete feature space + Multi-model blending", "Test PR-AUC": "0.2086", "Key Finding": "SuperLearner meta-weighting maximizes top-N precision."}
    ]
    st.dataframe(pd.DataFrame(ablation_data), hide_index=True, use_container_width=True)

    st.markdown("<hr />", unsafe_allow_html=True)

    # 4. Calibration & Reliability Analysis
    st.markdown("### Probability Calibration & Reliability")
    st.markdown(
        """
        <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; padding: 1.15rem 1.35rem; margin-bottom: 1.5rem;">
            <div style="font-weight: 700; color: #1E3A8A; font-size: 0.95rem; margin-bottom: 0.35rem;">Empirical Calibration Guarantee</div>
            <p style="color: #475569; font-size: 0.88rem; line-height: 1.5; margin-bottom: 0.5rem;">
                Raw tree-ensemble probabilities often exhibit sigmoid distortion and overconfidence in extreme tails. 
                Every target in the production release bundle is fitted with an independent <strong>Isotonic Regression calibrator</strong> 
                trained on out-of-fold validation predictions.
            </p>
            <div style="font-size: 0.86rem; color: #334155;">
                &bull; <strong>Mean Test Brier Score:</strong> 0.0449 (sharp empirical reliability against observed 1-year incident outcomes).<br/>
                &bull; <strong>Decision Thresholds:</strong> Optimized per-disease to satisfy F1-optimal, 80% recall, and prevalence-matched operating regimes.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 5. Leakage Auditing & Clinical Safety
    st.markdown("### Data Leakage Audit & Reproducibility Protocol")
    col_leak1, col_leak2 = st.columns(2)
    with col_leak1:
        st.markdown(
            """
            <div style="background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; padding: 1rem; height: 100%;">
                <div style="font-weight: 700; color: #0F172A; font-size: 0.90rem; margin-bottom: 0.35rem;">Temporal & Subject Separation</div>
                <ul style="font-size: 0.84rem; color: #334155; margin: 0; padding-left: 1.2rem; line-height: 1.45;">
                    <li><strong>No Patient Overlap:</strong> Deterministic hashing ensures zero subject contamination across splits.</li>
                    <li><strong>Temporal Boundary:</strong> Features computed strictly prior to landmark index time T0; outcomes evaluated strictly in [T0, T0 + 365 days].</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_leak2:
        st.markdown(
            """
            <div style="background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; padding: 1rem; height: 100%;">
                <div style="font-weight: 700; color: #0F172A; font-size: 0.90rem; margin-bottom: 0.35rem;">Section 1.5 Masking Compliance</div>
                <ul style="font-size: 0.84rem; color: #334155; margin: 0; padding-left: 1.2rem; line-height: 1.45;">
                    <li><strong>Active Diagnosis Masking:</strong> Conditions documented in patient history are strictly excluded from incident prediction.</li>
                    <li><strong>Zero Lookahead:</strong> Feature pipelines rely exclusively on pre-landmark concepts.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )


if __name__ == "__main__":
    render()