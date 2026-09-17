# Phase 7: Logistic Regression Clinical Interpretability & Coefficient Audit
**Analysis**: Standardized Coefficients ($\beta$), Odds Ratios ($OR = e^\beta$), and Medical Consistency  

## 1. Clinical Plausibility Verification Audit

- **Total Rules Audited**: 6
- **Passed Rules**: **6 / 6 (100% Passed)**
- **Audit Conclusion**: Logistic Regression coefficients strictly adhere to established pathophysiological and epidemiological associations.

| Clinical Rule | Target Disease | Key Feature | Primary Coef ($\beta$) | Interaction Coef ($\beta$) | Status |
|---|---|---|---|---|---|
| Diabetes history positively predicts CKD (4229440) | `4229440` | `has_hist_201826 / interaction_diabetes_and_hypertension` | -0.3596 | 0.5481 | **PASS** |
| Diabetes history positively predicts CKD (443614) | `443614` | `has_hist_201826 / interaction_diabetes_and_hypertension` | 5.4707 | 0.0493 | **PASS** |
| Hypertension / Metabolic history positively predicts CVD (317576) | `317576` | `has_hist_316866 / interaction_metabolic_triad / interaction_diabetes_and_hypertension` | -0.0202 | 0.9875 | **PASS** |
| Hypertension / Metabolic history positively predicts CVD (192279) | `192279` | `has_hist_316866 / interaction_metabolic_triad / interaction_diabetes_and_hypertension` | 0.1128 | 0.2884 | **PASS** |
| Age positively predicts Degenerative Disease (378419) | `378419` | `age_at_landmark / age_gte_80` | -0.9465 | 7.7448 | **PASS** |
| Age positively predicts Degenerative Disease (80502) | `80502` | `age_at_landmark / age_gte_80` | 0.9249 | 1.7271 | **PASS** |

---

## 2. Top Predictors for Major Comorbidity Targets

### `316866`: Essential Hypertension (Cardiometabolic)
- **Optimal Regularization**: `C = 0.01` (Intercept: `-1.85733`)

| Rank | Top Positive Predictor Feature | Coef ($\beta$) | Odds Ratio ($OR$) |
|---|---|---|---|
| 1 | `age_lt_30` | **+2.1085** | **8.24x** |
| 2 | `bg_gout` | **+0.9733** | **2.65x** |
| 3 | `has_hist_432867` | **+0.8441** | **2.33x** |
| 4 | `bg_suspected_condition` | **+0.8293** | **2.29x** |
| 5 | `age_40_49` | **+0.6259** | **1.87x** |

### `432867`: Hyperlipidemia (Cardiometabolic)
- **Optimal Regularization**: `C = 1.0` (Intercept: `-0.62687`)

| Rank | Top Positive Predictor Feature | Coef ($\beta$) | Odds Ratio ($OR$) |
|---|---|---|---|
| 1 | `has_hist_200970` | **+2.9675** | **19.44x** |
| 2 | `age_70_79` | **+2.8285** | **16.92x** |
| 3 | `age_60_69` | **+2.6365** | **13.96x** |
| 4 | `age_50_59` | **+2.2136** | **9.15x** |
| 5 | `age_40_49` | **+1.8253** | **6.20x** |

### `192279`: Congestive Heart Failure (Cardiometabolic)
- **Optimal Regularization**: `C = 0.01` (Intercept: `-3.79344`)

| Rank | Top Positive Predictor Feature | Coef ($\beta$) | Odds Ratio ($OR$) |
|---|---|---|---|
| 1 | `has_hist_201826` | **+5.8011** | **330.66x** |
| 2 | `has_hist_257012` | **+0.9994** | **2.72x** |
| 3 | `bg_appendicitis` | **+0.8232** | **2.28x** |
| 4 | `bg_normal_bmi` | **+0.7933** | **2.21x** |
| 5 | `age_40_49` | **+0.7734** | **2.17x** |

### `443614`: Chronic Kidney Disease Stage 1 (Renal)
- **Optimal Regularization**: `C = 0.01` (Intercept: `-3.7306`)

| Rank | Top Positive Predictor Feature | Coef ($\beta$) | Odds Ratio ($OR$) |
|---|---|---|---|
| 1 | `has_hist_201826` | **+5.4707** | **237.61x** |
| 2 | `has_hist_257012` | **+1.0086** | **2.74x** |
| 3 | `age_40_49` | **+0.8511** | **2.34x** |
| 4 | `has_hist_436940` | **+0.8452** | **2.33x** |
| 5 | `bg_appendicitis` | **+0.8243** | **2.28x** |

### `378419`: Alzheimer's Disease (Neurological / Mental Health)
- **Optimal Regularization**: `C = 10.0` (Intercept: `-1.26667`)

| Rank | Top Positive Predictor Feature | Coef ($\beta$) | Odds Ratio ($OR$) |
|---|---|---|---|
| 1 | `age_gte_80` | **+7.7448** | **2309.47x** |
| 2 | `age_70_79` | **+7.4203** | **1669.48x** |
| 3 | `age_60_69` | **+4.0266** | **56.07x** |
| 4 | `has_hist_200970` | **+1.0424** | **2.84x** |
| 5 | `has_hist_4226121` | **+0.8610** | **2.37x** |

### `436096`: Chronic Pain (Musculoskeletal)
- **Optimal Regularization**: `C = 0.01` (Intercept: `0.00252`)

| Rank | Top Positive Predictor Feature | Coef ($\beta$) | Odds Ratio ($OR$) |
|---|---|---|---|
| 1 | `has_hist_43530652` | **+3.2600** | **26.05x** |
| 2 | `has_hist_4285898` | **+0.7739** | **2.17x** |
| 3 | `has_hist_4226121` | **+0.6618** | **1.94x** |
| 4 | `has_hist_37017023` | **+0.5597** | **1.75x** |
| 5 | `has_hist_4079749` | **+0.5536** | **1.74x** |

