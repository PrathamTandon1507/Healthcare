# Phase 9: XGBoost Feature Importance Audit (Gain, Weight, Cover)

## 1. Top Clinical Predictors by Gain for Representative Benchmark Diseases

### Essential Hypertension (OMOP `316866`)

| Rank | Feature Name | Gain (Relative Information) | Weight (Splits) | Cover (Hessian Support) |
|---|---|---|---|---|
| 1 | `age_lt_30` | **3336.5952** | 28 | 7956.43 |
| 2 | `age_at_landmark` | **2526.1965** | 1202 | 7205.08 |
| 3 | `has_hist_316866` | **596.7419** | 157 | 10435.48 |
| 4 | `has_hist_4310703` | **436.3582** | 3 | 8385.93 |
| 5 | `has_hist_4115276` | **291.8055** | 13 | 9969.40 |

### Type 2 Diabetes Mellitus (OMOP `201826`)

| Rank | Feature Name | Gain (Relative Information) | Weight (Splits) | Cover (Hessian Support) |
|---|---|---|---|---|
| 1 | `age_at_landmark` | **2335.6912** | 800 | 11748.50 |
| 2 | `interaction_metabolic_triad` | **1002.3340** | 1 | 9206.79 |
| 3 | `has_hist_4120314` | **940.2305** | 20 | 9203.12 |
| 4 | `has_hist_4310703` | **805.4271** | 22 | 13261.09 |
| 5 | `has_hist_4115276` | **771.9575** | 101 | 12452.00 |

### Coronary Arteriosclerosis (OMOP `317576`)

| Rank | Feature Name | Gain (Relative Information) | Weight (Splits) | Cover (Hessian Support) |
|---|---|---|---|---|
| 1 | `has_hist_317576` | **2246.4819** | 95 | 40548.99 |
| 2 | `gender_male` | **1321.9945** | 139 | 15763.88 |
| 3 | `age_at_landmark` | **1291.8099** | 391 | 20286.91 |
| 4 | `interaction_cvd_and_ckd` | **1269.5531** | 15 | 17703.18 |
| 5 | `has_hist_192279` | **1107.8380** | 31 | 18403.15 |

### Hyperlipidemia (OMOP `432867`)

| Rank | Feature Name | Gain (Relative Information) | Weight (Splits) | Cover (Hessian Support) |
|---|---|---|---|---|
| 1 | `has_hist_432867` | **3526.0112** | 114 | 34220.02 |
| 2 | `age_lt_30` | **2162.5955** | 14 | 34107.03 |
| 3 | `age_at_landmark` | **1193.0764** | 940 | 12643.30 |
| 4 | `age_30_39` | **715.9701** | 17 | 13378.76 |
| 5 | `has_hist_4129902` | **540.4268** | 35 | 5590.15 |

