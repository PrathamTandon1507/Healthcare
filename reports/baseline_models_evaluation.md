# Baseline Models Evaluation & Benchmark Report
**Models Evaluated**: PREVALENCE, LR, RF, XGB  
**Target Diseases**: K = 41 Curated Chronic Comorbidity Targets  
**Features**: 81 Active Clinical Predictors (Excluding Network Placeholders)  

## 1. Macro Model Benchmark Comparison

| Model Architecture | Val Macro-AUPRC | Val Macro-AUROC | Val Brier | Test Macro-AUPRC | Test Macro-AUROC | Test Brier | Test P@3 | Test R@3 | Test MAP@3 |
|---|---|---|---|---|---|---|---|---|---|
| **PREVALENCE** | 0.0033 | 0.5000 | 0.0033 | **0.0025** | 0.5000 | 0.0025 | 0.1065 | 0.2946 | 0.1843 |
| **LR** | 0.0564 | 0.8595 | 0.1001 | **0.0446** | 0.8634 | 0.1091 | 0.2103 | 0.5358 | 0.4038 |
| **RF** | 0.0750 | 0.8675 | 0.0713 | **0.0649** | 0.8714 | 0.0731 | 0.2504 | 0.6262 | 0.5353 |
| **XGB** | 0.0947 | 0.8831 | 0.0528 | **0.0818** | 0.8848 | 0.0549 | 0.2774 | 0.6930 | 0.5796 |

---

## 2. Prevalence Tier Breakdown (Test Macro-AUPRC)

| Model Architecture | High Prevalence (>0.5%) | Medium Prevalence (0.1%-0.5%) | Low Prevalence (<0.1%) |
|---|---|---|---|
| **PREVALENCE** | 0.0074 | 0.0024 | 0.0006 |
| **LR** | 0.1034 | 0.0547 | 0.0127 |
| **RF** | 0.1438 | 0.0817 | 0.0191 |
| **XGB** | 0.1946 | 0.1024 | 0.0196 |
