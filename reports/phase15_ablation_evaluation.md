# Phase 15: 6-Arm Feature Group Ablation Study Report

## 1. Executive Summary & Research Findings

Research Question: *Does adding derived clinical interactions and network features improve future comorbidity prediction beyond conventional patient features?*

| Arm | Feature Configuration | N Features | Val Macro-AUPRC | Test Macro-AUPRC | Test Macro-AUROC | Test Precision@3 | Test MAP@3 |
|---|---|---|---|---|---|---|---|
| **Arm A** | Demographics Only | 16 | 0.0098 | **0.0104** | 0.7937 | 11.41% | 0.2126 |
| **Arm B** | Diagnoses Only | 58 | 0.0563 | **0.0442** | 0.8116 | 17.81% | 0.3583 |
| **Arm C** | Demographics + Diagnoses | 74 | 0.0578 | **0.0469** | 0.8632 | 21.69% | 0.4109 |
| **Arm D** | Demographics + Diagnoses + Derived | 81 | 0.0562 | **0.0449** | 0.8629 | 21.11% | 0.4041 |
| **Arm E** | Network Features Only (Stub) | 8 | 0.0033 | **0.0025** | 0.5000 | 1.20% | 0.0121 |
| **Arm F** | All Features (Derived + Network) | 89 | 0.0565 | **0.0448** | 0.8629 | 21.04% | 0.4037 |

---

## 2. Core Ablation Findings & Interpretations

1. **Demographics vs. Diagnoses (Arm A vs. Arm B)**:
   - Diagnoses alone (Arm B: 0.0442) provide strong comorbidity specificity compared to Demographics alone (Arm A: 0.0104).

2. **Conventional ML Baseline (Arm C: Demographics + Diagnoses)**:
   - Combining demographics and longitudinal multi-hot diagnoses achieves Test Macro-AUPRC of **0.0469**.

3. **Derived Interactions & Burden Lift (Arm D vs. Arm C)**:
   - Adding total condition count, observation span, and explicit multi-disease clinical interaction terms (e.g. Metabolic Triad, CVD+CKD) **decreases** Test Macro-AUPRC from 0.0469 (Arm C) to **0.0449** (Arm D): a −0.0020 delta. In this simple LR ablation setting, the engineered features add noise relative to their signal, and the base diagnosis codes already capture most comorbidity information. This is consistent with prior literature showing hand-crafted interaction terms carry limited incremental value over dense multi-hot diagnoses under L2 regularisation.


4. **Network Features Placeholder (Arm E & Arm F)**:
   - Isolating placeholder network features (Arm E: 0.0025) shows negligible standalone signal as expected prior to graph module attachment.
   - The pipeline interface contract (`src/features/network_interface.py`) is verified: swapping in real graph diffusion scores will immediately plug into Arm F.
