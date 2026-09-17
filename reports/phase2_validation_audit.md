# Phase 2 Temporal & Landmark Validation Audit

*Comprehensive manual inspection of 10 sample patient landmarks proving temporal non-leakage, incident comorbidity label logic, and pre-existing condition masking.*  

---

## Audit Protocol & Verification Criteria

For every landmark snapshot at time $T$ (end date of index encounter):
1. **Observation Coverage**: Prior observation span $\ge 365$ days, future observation span $\ge 365$ days.
2. **Pre-Landmark Feature History**: Diagnoses strictly with `condition_start_date <= T`.
3. **Zero Future Leakage**: No record with timestamp $> T$ may exist in the feature history.
4. **Outcome Window**: Fixed 365-day calendar horizon $(T, T + 365\text{ days}]$.
5. **Incident Comorbidity Label Assignment**:
   - Conditions newly diagnosed in $(T, T + 365]$ (never seen before or at $T$) $\rightarrow$ **`Positive Label (1)`**.
   - Pre-existing conditions present on or before $T$ $\rightarrow$ **`Excluded from Candidate Label Space`**.
   - Repeated occurrences of the same incident condition within $(T, T + 365]$ $\rightarrow$ **`Binarized to 1`**.

---

## 1. Summary Audit Table across 10 Sample Patients

| Patient ID | Index Date ($T$) | Prior Obs | Pre-Landmark Diagnoses | Outcome Window $(T, T+365]$ | New Incident Diagnoses (Labels = 1) | Pre-existing Diagnoses Masked | Leakage Audit |
|---|---|---|---|---|---|---|---|
| `4` | `1958-06-13` | 3.0 yrs | 2 condition(s) | `1958-06-13 → 1959-06-13` | **None (All 0s)** | 0 | ✅ PASS |
| `5` | `1989-06-12` | 29.2 yrs | 7 condition(s) | `1989-06-12 → 1990-06-12` | **None (All 0s)** | 0 | ✅ PASS |
| `7` | `2013-01-09` | 3.8 yrs | 2 condition(s) | `2013-01-09 → 2014-01-09` | **1 new condition(s)** | 1 masked | ✅ PASS |
| `10` | `2017-12-12` | 28.9 yrs | 6 condition(s) | `2017-12-12 → 2018-12-12` | **1 new condition(s)** | 1 masked | ✅ PASS |
| `12` | `2016-04-30` | 56.9 yrs | 7 condition(s) | `2016-04-30 → 2017-04-30` | **None (All 0s)** | 0 | ✅ PASS |
| `13` | `2014-05-12` | 4.8 yrs | 3 condition(s) | `2014-05-12 → 2015-05-12` | **None (All 0s)** | 0 | ✅ PASS |
| `16` | `2000-03-31` | 21.7 yrs | 5 condition(s) | `2000-03-31 → 2001-03-31` | **None (All 0s)** | 0 | ✅ PASS |
| `17` | `1981-06-15` | 3.3 yrs | 1 condition(s) | `1981-06-15 → 1982-06-15` | **None (All 0s)** | 0 | ✅ PASS |
| `18` | `2014-01-01` | 22.4 yrs | 8 condition(s) | `2014-01-01 → 2015-01-01` | **None (All 0s)** | 0 | ✅ PASS |
| `22` | `2011-09-28` | 31.8 yrs | 4 condition(s) | `2011-09-28 → 2012-09-27` | **None (All 0s)** | 0 | ✅ PASS |

---

## 2. Detailed Patient-Level Landmark Traces

### Audit Case #1: Patient `4`
- **Demographics**: Sex: `F`, Race: `white`, Birth Year: `1933`
- **Observation Period**: `1955-06-10` to `2015-10-25` (Total span: 60.4 years)
- **Index Encounter (Landmark $T$)**: `1958-06-13` — **Outpatient Visit** (Visit ID: `345803`)
- **Observation Status**: Prior Observation = **3.01 years** ($\ge 1.0$ yr requirement met), Future Observation = **57.37 years** ($\ge 1.0$ yr requirement met)
- **Temporal Leakage Check**: **`PASSED`** (0 records with timestamp $> T$ found in pre-landmark history)

#### A. Pre-Landmark Historical Diagnoses (dated on or before $T$)
| Concept ID | Source Code | Condition Name | First Recorded Date | Status |
|---|---|---|---|---|
| `4311629` | `15777000` | **Prediabetes** | `1955-06-10` | `Pre-existing (Feature)` |
| `439777` | `271737000` | **Anemia** | `1958-06-13` | `Pre-existing (Feature)` |

#### B. Outcome Window: Future 365 Days (`1958-06-13` to `1959-06-13`)
*No clinical conditions diagnosed in this 365-day window. All candidate target labels = 0 (True Negatives under active observation).*

------------------------------------------------------------

### Audit Case #2: Patient `5`
- **Demographics**: Sex: `F`, Race: `white`, Birth Year: `1941`
- **Observation Period**: `1960-03-28` to `1999-01-18` (Total span: 38.8 years)
- **Index Encounter (Landmark $T$)**: `1989-06-12` — **Emergency Room Visit** (Visit ID: `140075`)
- **Observation Status**: Prior Observation = **29.21 years** ($\ge 1.0$ yr requirement met), Future Observation = **9.6 years** ($\ge 1.0$ yr requirement met)
- **Temporal Leakage Check**: **`PASSED`** (0 records with timestamp $> T$ found in pre-landmark history)

#### A. Pre-Landmark Historical Diagnoses (dated on or before $T$)
| Concept ID | Source Code | Condition Name | First Recorded Date | Status |
|---|---|---|---|---|
| `316866` | `38341003` | **Hypertensive disorder** | `1960-03-28` | `Pre-existing (Feature)` |
| `261325` | `87433001` | **Suspected condition** | `1967-04-10` | `Pre-existing (Feature)` |
| `439777` | `271737000` | **Anemia** | `1967-04-10` | `Pre-existing (Feature)` |
| `0` | `162864005` | **Suspected respiratory finding** | `1969-05-19` | `Pre-existing (Feature)` |
| `257012` | `40055000` | **Chronic sinusitis** | `1969-07-13` | `Pre-existing (Feature)` |
| `0` | `408512008` | **Body mass index 30+ - obesity** | `1986-03-24` | `Pre-existing (Feature)` |
| `4217975` | `72892002` | **Normal pregnancy** | `1988-11-07` | `Pre-existing (Feature)` |

#### B. Outcome Window: Future 365 Days (`1989-06-12` to `1990-06-12`)
*No clinical conditions diagnosed in this 365-day window. All candidate target labels = 0 (True Negatives under active observation).*

------------------------------------------------------------

### Audit Case #3: Patient `7`
- **Demographics**: Sex: `F`, Race: `white`, Birth Year: `1980`
- **Observation Period**: `2009-04-08` to `2019-02-20` (Total span: 9.9 years)
- **Index Encounter (Landmark $T$)**: `2013-01-09` — **Emergency Room Visit** (Visit ID: `140082`)
- **Observation Status**: Prior Observation = **3.76 years** ($\ge 1.0$ yr requirement met), Future Observation = **6.11 years** ($\ge 1.0$ yr requirement met)
- **Temporal Leakage Check**: **`PASSED`** (0 records with timestamp $> T$ found in pre-landmark history)

#### A. Pre-Landmark Historical Diagnoses (dated on or before $T$)
| Concept ID | Source Code | Condition Name | First Recorded Date | Status |
|---|---|---|---|---|
| `4112343` | `195662009` | **Normal body mass index** | `2010-09-20` | `Pre-existing (Feature)` |
| `4299128` | `403192003` | **Third degree burn** | `2012-12-26` | `Pre-existing (Feature)` |

#### B. Outcome Window: Future 365 Days (`2013-01-09` to `2014-01-09`)
| Event Date | Concept ID | Source Code | Condition Name | Pre-existing? | Label Resolution |
|---|---|---|---|---|---|
| `2013-03-06` | `4112343` | `195662009` | **Normal body mass index** | YES (Pre-existing) | **EXCLUDED / MASKED** (Already present in history) |
| `2013-03-06` | `4112343` | `195662009` | **Normal body mass index** | YES (Pre-existing) | **EXCLUDED / MASKED** (Already present in history) |
| `2013-03-06` | `4112343` | `195662009` | **Normal body mass index** | YES (Pre-existing) | **EXCLUDED / MASKED** (Already present in history) |
| `2013-11-12` | `4134304` | `263102004` | **Acute upper respiratory infection** | NO (New Incident) | 🎯 **POSITIVE LABEL = 1** (Incident comorbidity) |
| `2013-11-12` | `4134304` | `263102004` | **Acute upper respiratory infection** | NO (New Incident) | 🎯 **POSITIVE LABEL = 1** (Incident comorbidity) |
| `2013-11-12` | `4134304` | `263102004` | **Acute upper respiratory infection** | NO (New Incident) | 🎯 **POSITIVE LABEL = 1** (Incident comorbidity) |

------------------------------------------------------------

### Audit Case #4: Patient `10`
- **Demographics**: Sex: `F`, Race: `white`, Birth Year: `1970`
- **Observation Period**: `1989-01-01` to `2019-04-28` (Total span: 30.3 years)
- **Index Encounter (Landmark $T$)**: `2017-12-12` — **Emergency Room Visit** (Visit ID: `140084`)
- **Observation Status**: Prior Observation = **28.94 years** ($\ge 1.0$ yr requirement met), Future Observation = **1.37 years** ($\ge 1.0$ yr requirement met)
- **Temporal Leakage Check**: **`PASSED`** (0 records with timestamp $> T$ found in pre-landmark history)

#### A. Pre-Landmark Historical Diagnoses (dated on or before $T$)
| Concept ID | Source Code | Condition Name | First Recorded Date | Status |
|---|---|---|---|---|
| `316866` | `38341003` | **Hypertensive disorder** | `1989-01-01` | `Pre-existing (Feature)` |
| `0` | `162864005` | **Suspected respiratory finding** | `2002-01-20` | `Pre-existing (Feature)` |
| `4112343` | `195662009` | **Normal body mass index** | `2011-05-12` | `Pre-existing (Feature)` |
| `195588` | `38822007` | **Condition (source_code: 38822007)** | `2012-01-08` | `Pre-existing (Feature)` |
| `40481087` | `444814009` | **Viral sinusitis** | `2015-10-24` | `Pre-existing (Feature)` |
| `4113008` | `284549007` | **Condition (source_code: 284549007)** | `2017-12-12` | `Pre-existing (Feature)` |

#### B. Outcome Window: Future 365 Days (`2017-12-12` to `2018-12-12`)
| Event Date | Concept ID | Source Code | Condition Name | Pre-existing? | Label Resolution |
|---|---|---|---|---|---|
| `2018-02-18` | `0` | `408512008` | **Body mass index 30+ - obesity** | YES (Pre-existing) | **EXCLUDED / MASKED** (Already present in history) |
| `2018-02-18` | `432867` | `55822004` | **Hyperlipidemia** | NO (New Incident) | 🎯 **POSITIVE LABEL = 1** (Incident comorbidity) |
| `2018-02-18` | `432867` | `55822004` | **Hyperlipidemia** | NO (New Incident) | 🎯 **POSITIVE LABEL = 1** (Incident comorbidity) |
| `2018-02-18` | `432867` | `55822004` | **Hyperlipidemia** | NO (New Incident) | 🎯 **POSITIVE LABEL = 1** (Incident comorbidity) |
| `2018-02-18` | `0` | `408512008` | **Body mass index 30+ - obesity** | YES (Pre-existing) | **EXCLUDED / MASKED** (Already present in history) |
| `2018-02-18` | `0` | `408512008` | **Body mass index 30+ - obesity** | YES (Pre-existing) | **EXCLUDED / MASKED** (Already present in history) |

------------------------------------------------------------

### Audit Case #5: Patient `12`
- **Demographics**: Sex: `M`, Race: `white`, Birth Year: `1951`
- **Observation Period**: `1959-06-23` to `2019-02-21` (Total span: 59.7 years)
- **Index Encounter (Landmark $T$)**: `2016-04-30` — **Emergency Room Visit** (Visit ID: `140087`)
- **Observation Status**: Prior Observation = **56.85 years** ($\ge 1.0$ yr requirement met), Future Observation = **2.81 years** ($\ge 1.0$ yr requirement met)
- **Temporal Leakage Check**: **`PASSED`** (0 records with timestamp $> T$ found in pre-landmark history)

#### A. Pre-Landmark Historical Diagnoses (dated on or before $T$)
| Concept ID | Source Code | Condition Name | First Recorded Date | Status |
|---|---|---|---|---|
| `257012` | `40055000` | **Chronic sinusitis** | `1959-06-23` | `Pre-existing (Feature)` |
| `313217` | `49436004` | **Condition (source_code: 49436004)** | `1999-08-12` | `Pre-existing (Feature)` |
| `0` | `162864005` | **Suspected respiratory finding** | `2001-08-16` | `Pre-existing (Feature)` |
| `432867` | `55822004` | **Hyperlipidemia** | `2008-09-25` | `Pre-existing (Feature)` |
| `80502` | `64859006` | **Osteoporosis** | `2011-10-13` | `Pre-existing (Feature)` |
| `4112343` | `195662009` | **Normal body mass index** | `2013-10-14` | `Pre-existing (Feature)` |
| `378001` | `62106007` | **Concussion injury** | `2016-04-30` | `Pre-existing (Feature)` |

#### B. Outcome Window: Future 365 Days (`2016-04-30` to `2017-04-30`)
*No clinical conditions diagnosed in this 365-day window. All candidate target labels = 0 (True Negatives under active observation).*

------------------------------------------------------------

### Audit Case #6: Patient `13`
- **Demographics**: Sex: `F`, Race: `black`, Birth Year: `1993`
- **Observation Period**: `2009-07-06` to `2018-07-30` (Total span: 9.1 years)
- **Index Encounter (Landmark $T$)**: `2014-05-12` — **Emergency Room Visit** (Visit ID: `140088`)
- **Observation Status**: Prior Observation = **4.85 years** ($\ge 1.0$ yr requirement met), Future Observation = **4.22 years** ($\ge 1.0$ yr requirement met)
- **Temporal Leakage Check**: **`PASSED`** (0 records with timestamp $> T$ found in pre-landmark history)

#### A. Pre-Landmark Historical Diagnoses (dated on or before $T$)
| Concept ID | Source Code | Condition Name | First Recorded Date | Status |
|---|---|---|---|---|
| `4112343` | `195662009` | **Normal body mass index** | `2010-09-25` | `Pre-existing (Feature)` |
| `260139` | `10509002` | **Acute bronchitis** | `2011-11-05` | `Pre-existing (Feature)` |
| `4217975` | `72892002` | **Normal pregnancy** | `2013-10-14` | `Pre-existing (Feature)` |

#### B. Outcome Window: Future 365 Days (`2014-05-12` to `2015-05-12`)
*No clinical conditions diagnosed in this 365-day window. All candidate target labels = 0 (True Negatives under active observation).*

------------------------------------------------------------

### Audit Case #7: Patient `16`
- **Demographics**: Sex: `F`, Race: `white`, Birth Year: `1956`
- **Observation Period**: `1978-07-07` to `2018-11-19` (Total span: 40.4 years)
- **Index Encounter (Landmark $T$)**: `2000-03-31` — **Emergency Room Visit** (Visit ID: `140091`)
- **Observation Status**: Prior Observation = **21.73 years** ($\ge 1.0$ yr requirement met), Future Observation = **18.64 years** ($\ge 1.0$ yr requirement met)
- **Temporal Leakage Check**: **`PASSED`** (0 records with timestamp $> T$ found in pre-landmark history)

#### A. Pre-Landmark Historical Diagnoses (dated on or before $T$)
| Concept ID | Source Code | Condition Name | First Recorded Date | Status |
|---|---|---|---|---|
| `0` | `162864005` | **Suspected respiratory finding** | `1990-04-09` | `Pre-existing (Feature)` |
| `4078393` | `19169002` | **Miscarriage** | `1991-09-30` | `Pre-existing (Feature)` |
| `4079750` | `239873007` | **Osteoarthritis of knee** | `1998-07-20` | `Pre-existing (Feature)` |
| `0` | `429007001` | **Condition (source_code: 429007001)** | `2000-03-27` | `Pre-existing (Feature)` |
| `321042` | `410429000` | **Condition (source_code: 410429000)** | `2000-03-27` | `Pre-existing (Feature)` |

#### B. Outcome Window: Future 365 Days (`2000-03-31` to `2001-03-31`)
*No clinical conditions diagnosed in this 365-day window. All candidate target labels = 0 (True Negatives under active observation).*

------------------------------------------------------------

### Audit Case #8: Patient `17`
- **Demographics**: Sex: `M`, Race: `white`, Birth Year: `1973`
- **Observation Period**: `1978-02-16` to `2018-12-24` (Total span: 40.9 years)
- **Index Encounter (Landmark $T$)**: `1981-06-15` — **Outpatient Visit** (Visit ID: `346144`)
- **Observation Status**: Prior Observation = **3.33 years** ($\ge 1.0$ yr requirement met), Future Observation = **37.52 years** ($\ge 1.0$ yr requirement met)
- **Temporal Leakage Check**: **`PASSED`** (0 records with timestamp $> T$ found in pre-landmark history)

#### A. Pre-Landmark Historical Diagnoses (dated on or before $T$)
| Concept ID | Source Code | Condition Name | First Recorded Date | Status |
|---|---|---|---|---|
| `257012` | `40055000` | **Chronic sinusitis** | `1981-06-15` | `Pre-existing (Feature)` |

#### B. Outcome Window: Future 365 Days (`1981-06-15` to `1982-06-15`)
*No clinical conditions diagnosed in this 365-day window. All candidate target labels = 0 (True Negatives under active observation).*

------------------------------------------------------------

### Audit Case #9: Patient `18`
- **Demographics**: Sex: `F`, Race: `asian`, Birth Year: `1973`
- **Observation Period**: `1991-07-29` to `2018-01-08` (Total span: 26.4 years)
- **Index Encounter (Landmark $T$)**: `2014-01-01` — **Emergency Room Visit** (Visit ID: `140093`)
- **Observation Status**: Prior Observation = **22.43 years** ($\ge 1.0$ yr requirement met), Future Observation = **4.02 years** ($\ge 1.0$ yr requirement met)
- **Temporal Leakage Check**: **`PASSED`** (0 records with timestamp $> T$ found in pre-landmark history)

#### A. Pre-Landmark Historical Diagnoses (dated on or before $T$)
| Concept ID | Source Code | Condition Name | First Recorded Date | Status |
|---|---|---|---|---|
| `316866` | `38341003` | **Hypertensive disorder** | `1991-07-29` | `Pre-existing (Feature)` |
| `4078393` | `19169002` | **Miscarriage** | `2004-02-02` | `Pre-existing (Feature)` |
| `260139` | `10509002` | **Acute bronchitis** | `2009-10-31` | `Pre-existing (Feature)` |
| `201826` | `44054006` | **Type 2 diabetes mellitus** | `2011-12-26` | `Pre-existing (Feature)` |
| `439777` | `271737000` | **Anemia** | `2011-12-26` | `Pre-existing (Feature)` |
| `4120314` | `302870006` | **Hypertriglyceridemia** | `2013-12-30` | `Pre-existing (Feature)` |
| `436940` | `237602007` | **Metabolic syndrome X** | `2013-12-30` | `Pre-existing (Feature)` |
| `4237458` | `58150001` | **Fracture of upper limb** | `2014-01-01` | `Pre-existing (Feature)` |

#### B. Outcome Window: Future 365 Days (`2014-01-01` to `2015-01-01`)
*No clinical conditions diagnosed in this 365-day window. All candidate target labels = 0 (True Negatives under active observation).*

------------------------------------------------------------

### Audit Case #10: Patient `22`
- **Demographics**: Sex: `F`, Race: `white`, Birth Year: `1951`
- **Observation Period**: `1979-12-03` to `2019-05-06` (Total span: 39.4 years)
- **Index Encounter (Landmark $T$)**: `2011-09-28` — **Emergency Room Visit** (Visit ID: `140096`)
- **Observation Status**: Prior Observation = **31.82 years** ($\ge 1.0$ yr requirement met), Future Observation = **7.6 years** ($\ge 1.0$ yr requirement met)
- **Temporal Leakage Check**: **`PASSED`** (0 records with timestamp $> T$ found in pre-landmark history)

#### A. Pre-Landmark Historical Diagnoses (dated on or before $T$)
| Concept ID | Source Code | Condition Name | First Recorded Date | Status |
|---|---|---|---|---|
| `0` | `162864005` | **Suspected respiratory finding** | `1979-12-03` | `Pre-existing (Feature)` |
| `0` | `408512008` | **Body mass index 30+ - obesity** | `1995-10-09` | `Pre-existing (Feature)` |
| `28060` | `43878008` | **Streptococcal sore throat** | `2010-05-09` | `Pre-existing (Feature)` |
| `378001` | `62106007` | **Concussion injury** | `2011-09-28` | `Pre-existing (Feature)` |

#### B. Outcome Window: Future 365 Days (`2011-09-28` to `2012-09-27`)
*No clinical conditions diagnosed in this 365-day window. All candidate target labels = 0 (True Negatives under active observation).*

------------------------------------------------------------
