# Empirical Disease Incidence & Target Space Selection Report

*Generated At:* 2026-09-18T02:02:43.893063  
*Specification:* `COMORBIDITY_ENSEMBLE_ML_PLAN.md` (Sections 1.4, 8)  

---

## 1. Target Selection Rationale & Threshold Analysis

Rather than arbitrarily fixing $K = 30\text{--}75$, we measured actual 365-day incident onset events across all 143 condition concepts in Synthea 100K.
For each condition, the at-risk denominator strictly excludes landmarks where the patient was already diagnosed on or before $T$.

### Target Retention by Minimum Positive Landmark Count
| Minimum Positive Landmark Threshold | Cohort A Targets (Inpatient/ED) | Cohort B Targets (General) | Modeling Feasibility / Imbalance Profile |
|---|---|---|---|
| $\ge 50$ positive events | **109 diseases** | **128 diseases** | Broad coverage, includes lower prevalence chronic entities |
| $\ge 100$ positive events (Recommended baseline) | **86 diseases** | **125 diseases** | Stable 5-fold CV splits ($\ge 20$ positives per fold) |
| $\ge 200$ positive events | **72 diseases** | **119 diseases** | Highly robust, focused on major chronic/acute conditions |

---

## 2. Ranked Incidence Table: Top 50 Condition Targets (Cohort A — Inpatient / ED)

| Concept ID | Condition / Disease Name | Pre-existing at $T$ | At-Risk Landmarks | Incident Positive Events | Unique Incident Patients | Incidence Rate (%) | Prevalence Tier |
|---|---|---|---|---|---|---|---|
| `40481087` | **Viral sinusitis** | 99,892 | 159,997 | **14,035** | **8,731** | **8.772%** | High (≥5%) |
| `4112343` | **Normal body mass index** | 62,482 | 197,407 | **10,063** | **6,134** | **5.098%** | High (≥5%) |
| `260139` | **Acute bronchitis** | 54,230 | 205,659 | **8,860** | **5,393** | **4.308%** | Medium (1–5%) |
| `43530652` | **Condition (source_code: 124171000119105)** | 59,694 | 200,195 | **3,249** | **2,011** | **1.623%** | Medium (1–5%) |
| `436096` | **Condition (source_code: 82423001)** | 59,975 | 199,914 | **3,136** | **1,975** | **1.569%** | Medium (1–5%) |
| `4055754` | **Fracture of rib** | 59,735 | 200,154 | **3,121** | **1,965** | **1.559%** | Medium (1–5%) |
| `28060` | **Streptococcal sore throat** | 16,329 | 243,560 | **2,807** | **1,770** | **1.152%** | Medium (1–5%) |
| `439777` | **Anemia** | 103,382 | 156,507 | **2,406** | **1,803** | **1.537%** | Medium (1–5%) |
| `4217975` | **Normal pregnancy** | 44,090 | 215,799 | **2,361** | **1,573** | **1.094%** | Medium (1–5%) |
| `378419` | **Condition (source_code: 26929004)** | 19,873 | 240,016 | **2,337** | **619** | **0.974%** | Low (0.1–1%) |
| `81151` | **Sprain of ankle** | 21,719 | 238,170 | **1,768** | **974** | **0.742%** | Low (0.1–1%) |
| `4310703` | **Condition (source_code: 424132000)** | 37,731 | 222,158 | **1,754** | **1,281** | **0.79%** | Low (0.1–1%) |
| `4285898` | **Polyp of colon** | 17,632 | 242,257 | **1,742** | **814** | **0.719%** | Low (0.1–1%) |
| `4115276` | **Condition (source_code: 254637007)** | 37,751 | 222,138 | **1,736** | **1,281** | **0.781%** | Low (0.1–1%) |
| `4311629` | **Prediabetes** | 93,931 | 165,958 | **1,734** | **1,218** | **1.045%** | Medium (1–5%) |
| `4208104` | **Condition (source_code: 55680006)** | 36,831 | 223,058 | **1,728** | **870** | **0.775%** | Low (0.1–1%) |
| `4229440` | **Chronic kidney disease** | 4,247 | 255,642 | **1,570** | **707** | **0.614%** | Low (0.1–1%) |
| `4294548` | **Acute viral pharyngitis** | 8,694 | 251,195 | **1,535** | **894** | **0.611%** | Low (0.1–1%) |
| `257012` | **Chronic sinusitis** | 61,983 | 197,906 | **1,505** | **861** | **0.76%** | Low (0.1–1%) |
| `4283893` | **Sinusitis** | 8,453 | 251,436 | **1,496** | **807** | **0.595%** | Low (0.1–1%) |
| `4129902` | **Condition (source_code: 126906006)** | 25,872 | 234,017 | **1,335** | **302** | **0.57%** | Low (0.1–1%) |
| `317576` | **Coronary arteriosclerosis** | 19,475 | 240,414 | **1,295** | **553** | **0.539%** | Low (0.1–1%) |
| `432867` | **Hyperlipidemia** | 35,130 | 224,759 | **1,268** | **683** | **0.564%** | Low (0.1–1%) |
| `316866` | **Hypertensive disorder** | 81,227 | 178,662 | **1,225** | **782** | **0.686%** | Low (0.1–1%) |
| `200970` | **Condition (source_code: 92691004)** | 25,448 | 234,441 | **1,107** | **252** | **0.472%** | Low (0.1–1%) |
| `372328` | **Otitis media** | 8,948 | 250,941 | **1,088** | **848** | **0.434%** | Low (0.1–1%) |
| `4078393` | **Miscarriage** | 42,793 | 217,096 | **1,040** | **810** | **0.479%** | Low (0.1–1%) |
| `378001` | **Concussion injury** | 12,627 | 247,262 | **1,035** | **585** | **0.419%** | Low (0.1–1%) |
| `313217` | **Condition (source_code: 49436004)** | 14,440 | 245,449 | **978** | **380** | **0.398%** | Low (0.1–1%) |
| `80502` | **Osteoporosis** | 18,532 | 241,357 | **914** | **407** | **0.379%** | Low (0.1–1%) |
| `4218389` | **Condition (source_code: 39848009)** | 10,130 | 249,759 | **875** | **504** | **0.35%** | Low (0.1–1%) |
| `4278672` | **Condition (source_code: 65966004)** | 9,885 | 250,004 | **852** | **371** | **0.341%** | Low (0.1–1%) |
| `40318618` | **Condition (source_code: 156073000)** | 4,252 | 255,637 | **837** | **641** | **0.327%** | Low (0.1–1%) |
| `381316` | **Stroke (Cerebrovascular accident)** | 19,841 | 240,048 | **818** | **499** | **0.341%** | Low (0.1–1%) |
| `78272` | **Sprain of wrist** | 9,534 | 250,355 | **728** | **436** | **0.291%** | Low (0.1–1%) |
| `4237458` | **Fracture of upper limb** | 7,424 | 252,465 | **717** | **330** | **0.284%** | Low (0.1–1%) |
| `4109685` | **Condition (source_code: 284551006)** | 6,675 | 253,214 | **708** | **334** | **0.28%** | Low (0.1–1%) |
| `4059173` | **Condition (source_code: 16114001)** | 6,910 | 252,979 | **704** | **284** | **0.278%** | Low (0.1–1%) |
| `4116491` | **Condition (source_code: 301011002)** | 3,316 | 256,573 | **685** | **482** | **0.267%** | Low (0.1–1%) |
| `40480160` | **Condition (source_code: 443165006)** | 5,255 | 254,634 | **668** | **208** | **0.262%** | Low (0.1–1%) |
| `4155034` | **Condition (source_code: 283371005)** | 5,889 | 254,000 | **654** | **311** | **0.257%** | Low (0.1–1%) |
| `4113008` | **Condition (source_code: 284549007)** | 6,585 | 253,304 | **641** | **322** | **0.253%** | Low (0.1–1%) |
| `4156265` | **Condition (source_code: 370247008)** | 6,496 | 253,393 | **630** | **310** | **0.249%** | Low (0.1–1%) |
| `4134304` | **Acute upper respiratory infection** | 6,699 | 253,190 | **576** | **289** | **0.227%** | Low (0.1–1%) |
| `4152936` | **Condition (source_code: 283385000)** | 6,473 | 253,416 | **573** | **313** | **0.226%** | Low (0.1–1%) |
| `4296204` | **Condition (source_code: 403190006)** | 5,058 | 254,831 | **475** | **248** | **0.186%** | Low (0.1–1%) |
| `37017023` | **Condition (source_code: 713197008)** | 5,735 | 254,154 | **457** | **232** | **0.18%** | Low (0.1–1%) |
| `195588` | **Condition (source_code: 38822007)** | 2,552 | 257,337 | **445** | **320** | **0.173%** | Low (0.1–1%) |
| `4079750` | **Osteoarthritis of knee** | 15,228 | 244,661 | **413** | **281** | **0.169%** | Low (0.1–1%) |
| `439393` | **Condition (source_code: 398254007)** | 4,130 | 255,759 | **391** | **288** | **0.153%** | Low (0.1–1%) |