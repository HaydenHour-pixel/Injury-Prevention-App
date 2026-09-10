# Athlete Injury Risk Tracker — MVP Spec

**Scope:** single athlete, 12-week validation.
**Status:** implementation source of truth. Formulas here are authoritative.
**Derived from:** architecture doc v1.1, trimmed for MVP.

Anything not in this document is out of scope. See `CLAUDE.md`.

---

## 1. Risk definition

> Injury risk is the probability that, if current patterns continue unchanged,
> clinically significant pain will manifest within 2–4 weeks.

It is a statement about accumulated chronic load, not about how the athlete feels today.

**Tiers:** 0–45 green · 45–60 yellow · 60–75 orange · 75–100 red.

---

## 2. Data model

Fourteen tables. Defined in SQLAlchemy; the DDL below is illustrative, not literal
(the original was MySQL dialect).

### Core

- `athlete` — id, name, sport, created_at, onboarding_completed
- `athlete_profile` — body metrics (weight, height, gender, age), current and peak weekly
  mileage, current training phase, auto-calculated nutrition baselines, baseline sleep
  hours, structured injury history (JSON), preferred recovery methods, stress response
  profile
- `daily_entry` — one row per athlete per date. Holds computed dimension scores, context
  flags, risk output, confidence, alert level. Unique on `(athlete_id, date)`.

### Logged data (child of `daily_entry`)

- `training` — mileage, `intensity_1_to_10`, derived `intensity_factor`, elevation,
  notes, source fields
- `sleep` — hours, quality 1–10, bedtime, wake time, source fields
- `nutrition` — protein/carbs/fat/calories, training phase and load on that date, meals
  JSON, source fields
- `recovery_method` — method type, duration, intensity, time applied, optional linked
  symptom

### Symptoms

- `symptom` — date, body location, `intensity_1_to_10`, type, onset, limiting flag,
  description, FK to pain profile, active flag
- `pain_profile` — one episode from onset to resolution. Location, dates, duration, max
  intensity, type progression, concurrent conditions, contributing factors, effective
  recovery methods, episode number
- `body_part_vulnerability` — aggregate per location. Episode count, recurrence risk,
  average duration, common triggers, effective methods, days since last episode

### Context

- `lifestyle_commitment` — recurring classes/work. Type, name, days of week, times,
  workload intensity, term dates
- `stress_event` — ad-hoc stressors. Type, name, date range, expected intensity 1–10,
  resolution

### Model bookkeeping

- `prediction_accuracy` — prediction date, predicted risk, confidence, outcome, outcome
  location and duration, calibration error, athlete feedback
- `model_metrics` — per-day snapshot. Days of data, stress instances observed, variance
  score, calibration offset, accuracy, per-method efficacy JSON

### Provenance fields (all logged tables)

```
created_at        TIMESTAMP   -- when the row was actually written (UTC)
date              DATE        -- the athlete's local day this describes
source_confidence FLOAT       -- 0-1, trust in the data source
recall_confidence FLOAT       -- 0-1, trust given reporting lag
```

`date` is the athlete's local calendar date. A run logged at 11:40pm belongs to that day.
Never derive it from a UTC timestamp.

---

## 3. Data provenance and recall decay

Two independent factors, multiplied when weighting an observation.

### Source confidence

| Source            | Confidence |
|-------------------|-----------|
| Strava            | 1.0       |
| Manual            | 0.9       |
| UMass dining menu | 0.7       |
| Manual food entry | 0.6       |

### Recall confidence

Lag is measured against the field's **natural reporting window**, not against `date`.
Entering sleep quality the following morning is zero lag. Entering it on Thursday for
Monday is three days of lag.

| Field group | Natural window | Decay |
|---|---|---|
| Objective (mileage, elevation, bedtime, wake time, duration, macros) | any | none, always 1.0 |
| Subjective effort (`intensity_1_to_10`) | same day | 1.0 same day, 0.85 +1d, 0.6 +2d, 0.4 beyond |
| Sleep quality | next morning | 1.0 through next morning, then the effort curve shifted one day |
| Symptom intensity | same day | 1.0 same day, 0.7 +1d, 0.4 beyond |
| Body sentiment | same day | same as symptom |
| Nutrition recall | same day | same curve as subjective effort |

Nutrition is listed separately because it decays by a different mechanism. It is
episodic memory of discrete events, not a felt quality fading. The rate happens to be
comparable, so it shares the effort curve, but the two should be recalibrated
independently rather than assumed to move together.

### Row-level scope

The database stores one `recall_confidence` per row, but a single row can span field
groups: `training` holds objective mileage alongside a subjective intensity rating.

**The stored value describes that row's subjective fields only.** Objective fields are
always treated as confidence 1.0 regardless of what the row's column says.

Which group governs the stored value: if the row has a subjective field
(`intensity_1_to_10`, `quality_1_to_10`), that field's group applies. Otherwise the row
is objective and the value is 1.0.

Without this rule, a training row whose intensity was entered three days late would
carry `recall_confidence = 0.4`, and consequence 1 below would exclude its mileage from
the training-load baseline. Mileage is the same number whenever it was typed. Excluding
it corrupts the baseline behind `acute_chronic_ratio`, which carries weight 0.25 in the
risk formula.

### Consequences

1. **High-lag subjective values are excluded from baseline and variance computation.**
   They regress toward the athlete's mean, which would artificially suppress observed
   variance and inflate model confidence. They remain visible in the UI.

   This applies to subjective fields only, per the row-level scope rule above. Objective
   fields on the same row are never excluded on recall grounds.

2. **Retrospective symptom entries are down-weighted as calibration labels.** Pain memory
   anchors to peak and endpoint. A symptom row with `recall_confidence < 0.7` contributes
   to `prediction_accuracy` at reduced weight.

3. **The app prompts for same-day symptom entry specifically.** Other fields tolerate lag;
   this one is the label set.

---

## 4. Missing data

Absence is not zero.

| Situation | Representation |
|---|---|
| No recovery done, logged as such | `recovery_method` row, `method_type = 'none'` |
| Recovery section never opened | no `recovery_method` row for that date |
| Nutrition not logged | no `nutrition` row |
| No pain, confirmed | `daily_entry.no_pain_confirmed = true`, no `symptom` rows |
| Symptoms not yet answered for the day | `daily_entry.no_pain_confirmed` is `NULL`, no `symptom` rows |

`no_pain_confirmed` exists because symptoms are the calibration labels (section 10): an
unlogged painful day and an explicitly-confirmed pain-free day must not collapse into the
same "no symptom rows" state, or an unlogged day of real pain reads as outcome `none` and
calibrates the model to be *less* sensitive. It is never set to `false` — only `NULL`
(unanswered) or `true` (confirmed). Logging any symptom for the date clears a standing
`true` back to `NULL`, since the new report contradicts the earlier answer. It is not
represented as a `symptom` row with intensity 0: a sentinel there would leak into
escalation trends, `pain_profile` grouping, and the trailing-3d max in section 5.5.

Scoring functions return `None` for absent inputs. The caller decides how to handle it.
Never substitute 0. A missing nutrition log is not a day of zero protein.

Completeness is tracked **per section, not per day**. The common failure is partial
logging: the run gets recorded right after it happens, dining hall food does not.

---

## 5. Dimension scores

All computed daily, all pure functions, all unit tested against the worked examples below.

### 5.1 Sleep score

```
sleep_score = hours_normalized * quality_normalized * consistency_factor

hours_normalized   = min(hours / 8, 1.0)
quality_normalized = quality_rating / 10
consistency_factor = 1.0 - (bedtime_variance_minutes / 120)
```

Worked example: 6.5h, quality 7, variance ±45min
→ 0.8125 × 0.7 × 0.625 = **0.355**

Note the multiplicative form is punishing. Three mediocre inputs produce a very low score.
This is intentional but should be watched during calibration.

### 5.2 Nutrition score

```
IF training_phase in (taper, recovery):
    adj_protein = baseline_protein * 0.85
    adj_carbs   = baseline_carbs   * 0.80
ELSE:
    adj_protein = baseline_protein
    adj_carbs   = baseline_carbs

nutrition_score = avg([consumed_protein / adj_protein,
                       consumed_carbs   / adj_carbs])
```

Not capped at 1.0; exceeding baseline is not penalised.

Worked example (build): 140/150 and 380/400 → avg(0.93, 0.95) = **0.94**
Worked example (taper): 130/127.5 and 340/320 → avg(1.02, 1.06) = **1.04**

### 5.3 Training load

```
intensity_factor: 1-3 → 1.0 | 4-6 → 1.2 | 7-8 → 1.5 | 9-10 → 1.8

daily_load = mileage * intensity_factor
load_7d    = sum(daily_load over trailing 7 days)
load_28d   = sum(daily_load over trailing 28 days)

training_load_normalized = daily_load / (current_weekly_mileage / 7)
acute_chronic_ratio      = load_7d / (load_28d / 4)
```

`acute_chronic_ratio` is the term that feeds risk. Around 1.0 is steady state; sustained
values above ~1.3 indicate the athlete is ramping faster than they have adapted to.
Below 28 days of data it is undefined — use whatever history exists and let confidence
carry the uncertainty.

Worked example: 6 miles at intensity 8 → 6 × 1.5 = 9 load. Against a 50 mi/wk baseline
(7.14/day), normalized = **1.26**

### 5.4 Recovery

Two separate quantities. Do not conflate them.

**Daily display score** — what the athlete did today, shown in the UI, not fed to risk:

```
recovery_daily = avg(learned_efficacy of methods applied today)
               = 0.0 if method_type == 'none'
               = None if nothing logged
```

**Rolling adequacy** — the value that feeds the risk formula:

```
recovery_volume_7d  = sum(duration_minutes * learned_efficacy) over trailing 7d
recovery_adequacy   = recovery_volume_7d / expected_recovery_for(load_7d)
recovery_shortfall  = clamp(1.0 - recovery_adequacy, 0.0, 1.0)
```

Rationale: runners do not recover every day, and they should not have to. Two solid
sessions in a light week is adequate; the same two in a 60-mile week is thin. Only the
ratio carries meaning. Using the daily value would flag five days out of seven for an
athlete doing nothing wrong.

`expected_recovery_for(load)` is provisional: `load_7d * 0.5` minutes. Calibrate against
observed data.

### 5.5 Symptom severity

```
base by type and intensity:
  none                        0.0
  muscle_soreness   (1-3/10)  0.1 - 0.3
  dull_ache         (3-6/10)  0.3 - 0.6
  sharp_pain        (6+/10)   0.7 - 1.0

escalation:  × 1.5 if intensity rising across 3 consecutive days
location:    × 1.3 if body_part_vulnerability.recurrence_risk = high
             × 0.8 if no prior episodes at this location
```

Type and intensity are independent fields. A 7/10 muscle soreness and a 7/10 sharp pain
are different events.

**Noise filter:** muscle soreness appearing 12–48h after a session of intensity 7+, with
no escalation, is DOMS. It does not contribute to symptom severity and does not count
against any recovery method's efficacy.

### 5.6 Recovery method efficacy (learned)

```
observation: (intensity_on_prior_day, method, pain_before, pain_after)
credit if pain_after < pain_before
minimum n = 10 before the learned value is trusted
below n = 10, use the population default
```

Efficacy is learned conditional on prior-day intensity, since methods that help after
hard sessions may do nothing after easy ones. Intensity is athlete-relative; the model
learns this athlete's personal scale rather than assuming 8 means the same thing to
everyone.

Defaults before learning: foam_roll 0.7, yoga 0.6, ice_bath 0.7, massage 0.65,
stretching 0.5, rest 0.6.

---

## 6. Context interpretation

### Inside a stress period

```
retrieve historical metric deltas during similar stress events
stress_adjusted_baseline = normal_baseline - observed_typical_drop

if current >= stress_adjusted_baseline:  "within your exam pattern, expected"
else:                                     flag
```

The flag fires when a metric is worse than this athlete's *own stress pattern*, not merely
below their normal baseline.

### Outside a stress period

Compare to normal baseline. Flag deviation beyond 1 SD.

### Hard limits — never adapt to context

These fire regardless of stress, phase, or learned pattern:

- sharp pain > 5/10 and escalating
- pain rising 3+ points over 2–3 days
- same location, 2+ episodes
- sleep < 4h combined with mileage > 80% of typical
- protein < 50% of baseline for 2+ weeks

---

## 7. Risk formula (MVP)

No neural network. Transparent weighted sum, hard-limit floors applied after.

```
burden terms, each 0-1, higher is worse:

  sleep_debt          = 1 - mean(sleep_score, trailing 7d)
  nutrition_deficit   = clamp(1 - mean(nutrition_score, trailing 7d), 0, 1)
  load_strain         = clamp((acute_chronic_ratio - 1.0) / 0.5, 0, 1)
  recovery_shortfall  = as defined in 5.4
  symptom_burden      = max(symptom_severity, trailing 3d)

base_risk = 100 * (
    0.20 * sleep_debt
  + 0.10 * nutrition_deficit
  + 0.25 * load_strain
  + 0.15 * recovery_shortfall
  + 0.30 * symptom_burden
)

interaction bonus:
  + 10 if load_strain > 0.5 AND sleep_debt > 0.5
  (low sleep under high load is worse than either alone)

context adjustment:
  - 5 if inside a stress period and all metrics are within the athlete's
    established stress pattern

hard limit floor:
  any hard limit triggered → risk = max(risk, 65)

risk = clamp(risk, 0, 100)
```

**These weights are provisional and uncalibrated.** They encode initial judgement: current
symptoms and training load matter most, nutrition least. They exist to be wrong in a
legible way and corrected against 12 weeks of outcomes. Every contribution must be
displayable as a term so the athlete can see what drove the number.

---

## 8. Confidence

```
confidence = days_factor * stress_factor * (1 - variance_penalty)

days_factor:    <7d 0.2 | 7-14d 0.4 | 14-30d 0.6 | 30d+ 0.85 | 60d+ 1.0
stress_factor:  0 instances → omit from product | 1 → 0.3 | 2-3 → 0.65 | 4+ → 1.0
variance_penalty: std_dev/mean of key metrics. Low 0.1, high 0.4.
```

High-lag subjective entries are excluded from the variance computation (see §3).

Risk output is suppressed entirely below 30% confidence during weeks 1–2. From week 3,
risk is shown with confidence displayed alongside. A risk number without its confidence
is a bug.

---

## 9. Alert levels

| Level | Trigger | Action |
|---|---|---|
| 1 — silent | risk ≥ 50 and confidence < 40 | log only, no notification |
| 2 — soft | risk ≥ 55 and confidence ≥ 40 | dashboard only, no push |
| 3 — hard | risk ≥ 65, or risk ≥ 50 with escalating sharp pain, or risk ≥ 50 with recurrence | push notification + dashboard |

Thresholds shift by `calibration_offset` once calibration data exists.

Level 3 copy must state the observation, the contributing factors with concrete numbers,
and a suggestion to consult a professional. It must not issue instructions.

---

## 10. Calibration

Every two weeks, capture the actual outcome:

```
none | mild_soreness | moderate_pain | significant_pain | clinical_injury
```

mapped to actual severity 0 / 25 / 50 / 75 / 100.

```
calibration_error = predicted_risk - actual_severity
```

Consistent overestimation across 4+ windows → `calibration_offset` of −10 to −20.
Consistent underestimation → +10 to +20.

Retrospective symptom entries contribute at reduced weight (see §3).

---

## 11. Daily batch job

Runs end of day.

1. Recompute dimension scores for the day
2. Recompute rolling windows (7d, 28d)
3. Apply context interpretation
4. Evaluate hard limits
5. Compute risk and confidence
6. Determine alert level, dispatch if 2 or 3
7. Update `model_metrics`
8. Log the prediction to `prediction_accuracy` for later outcome matching

Idempotent. Re-running for a date must produce the same result and must not duplicate
alerts.

---

## 12. Open items

1. **Recovery weights and `expected_recovery_for()`** are guesses. First calibration
   target.
2. **Confidence is multiplicative and collapses fast.** Three moderate factors give ~11%.
   May be too conservative; watch whether it suppresses output for longer than intended.
3. **Sleep score is also multiplicative** and produces low absolute values for ordinary
   nights. Verify the risk formula's `sleep_debt` term isn't permanently elevated.
4. **`acute_chronic_ratio` needs 28 days** before it means anything. Weeks 1–4 risk is
   driven mostly by symptoms.
5. **Hard limit thresholds** (the 80% mileage figure, the 50% protein figure) are
   unvalidated.
6. **UMass dining API** access method unknown. Fallback is manual entry against a USDA
   food dictionary.
