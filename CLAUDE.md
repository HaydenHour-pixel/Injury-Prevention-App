# CLAUDE.md

Project instructions for Claude Code. Read this before making changes.

---

## What this is

A single-athlete performance and injury-risk tracking PWA. The athlete logs training,
sleep, nutrition, recovery, symptoms, and lifestyle context daily. The app computes
interpretable dimension scores and, from those, an injury-risk estimate with an explicit
confidence level.

The current phase is **MVP validation with one user (Hayden)**. Twelve weeks of real
logged data, to find out whether the risk signal matches lived experience.

---

## Non-negotiable product rules

These are product philosophy, not style preferences. Do not violate them even if a
change seems locally convenient.

1. **The app explains, it does not prescribe.** Output describes observations and
   correlations. It never issues commands. "We observed X, which has historically
   preceded Y for you", not "do Z".

2. **No medical advice, ever.** Any escalation copy ends with a suggestion to consult a
   professional. No diagnosis language. No naming specific conditions.

3. **Confidence is always displayed alongside risk.** A risk number without its
   confidence is a bug. If confidence is below threshold, suppress the number and say
   why.

4. **Context reframes risk, it doesn't excuse it.** Expected degradation during a known
   stress period is reported as expected. Hard limits (see spec) still fire regardless
   of context.

5. **Observation over estimation.** Never ask the user to quantify something they can't
   accurately self-report. Learn it from logged data instead.

---

## Stack

| Layer     | Choice                                                   |
|-----------|----------------------------------------------------------|
| Backend   | Python 3.12, FastAPI, SQLAlchemy 2.x (typed, `Mapped[]`)  |
| Database  | SQLite, single file, Alembic for migrations               |
| Frontend  | React 18 + TypeScript + Vite                              |
| Styling   | Tailwind                                                  |
| PWA       | `vite-plugin-pwa` (manifest + service worker)             |
| Testing   | pytest (backend), Vitest (frontend)                       |
| Hosting   | Fly.io, persistent volume mounted for the SQLite file     |

**No authentication system.** Single user. If deployed publicly, gate with one shared
secret from an env var. Do not build user accounts, sessions, password reset, or roles.

---

## Repo structure

```
/backend
  /app
    /models        SQLAlchemy models, one module per domain area
    /schemas       Pydantic request/response schemas
    /scoring       Dimension score calculators (pure functions)
    /risk          Risk formula, confidence calculation, alert levels
    /api           FastAPI routers
    /jobs          Daily batch job
    db.py
    main.py
  /tests
  /alembic
/frontend
  /src
    /components
    /pages
    /api           Typed client for the backend
    /types
/docs
  spec.md          Trimmed architecture spec (source of truth for formulas)
```

---

## Conventions

**Scoring functions are pure.** Everything in `/scoring` takes plain data in and returns
a number. No database access, no I/O, no clock reads. Pass dates and baselines in as
arguments. This is what makes them testable, and every one of them gets unit tests with
worked examples taken from `docs/spec.md`.

**Dates are the athlete's local calendar date, not UTC.** A run logged at 11:40pm belongs
to that day. Store dates as `DATE`, not `TIMESTAMP`, wherever the concept is "which day
was this". Only genuine event timestamps (`created_at`, `alert_sent_at`) are UTC
timestamps.

**Schema comes from `docs/spec.md`, but translate it.** The spec is written in MySQL
dialect (`AUTO_INCREMENT`, `UNIQUE KEY`). Define models in SQLAlchemy and let it generate
the DDL. JSON columns are fine on SQLite.

**Migrations are always Alembic.** Never edit the database by hand, never drop and
recreate. There is real logged data in there and it is irreplaceable.

**Missing data is normal, not exceptional.** Some days will have no nutrition entry, no
recovery entry, or nothing at all. Scoring functions must handle absent inputs by
returning `None` and letting the caller decide, rather than substituting zero. A missing
nutrition log is not a day of zero protein.

---

## Out of scope for MVP

Do not build these, do not add abstractions in anticipation of them, and do not suggest
them in code review:

- **Neural network.** Risk is a transparent weighted formula over dimension scores. The
  NN is deferred until there is enough labeled outcome data to justify it. Structure the
  risk module so a second implementation could slot in behind the same interface, but do
  not build the second implementation.
- **Multi-athlete support.** `athlete_id` stays in the schema. Nothing else generalizes.
- **Transfer learning / population baselines.**
- **NLP over free-text fields.**
- **Apple HealthKit.** Not accessible from a PWA. Sleep is manual entry.
- **Body-part vulnerability heatmap**, analytics export, recovery-method charts.

If a task seems to require one of these, stop and ask rather than building it.

---

## Build order

Work in vertical slices. Each slice ends with something usable end to end. Do not
scaffold ahead of the current slice.

1. **Logging loop.** Schema, daily entry CRUD, a mobile-usable form, PWA installable.
   Ships first because data collection is the bottleneck.
2. **Dimension scores.** The five calculators plus tests, displayed read-only.
3. **Baselines and context.** Rolling baselines, stress periods, training phase.
4. **Risk formula, confidence, alert levels.**
5. **Calibration loop.** Outcome capture, prediction accuracy tracking.
6. **Strava import.**

---

## Working style

- Ask before adding a dependency.
- Ask before changing anything in `/scoring` or `/risk` formulas. Those are specified in
  `docs/spec.md` and changes are product decisions, not implementation details.
- Prefer boring, readable code over clever code. This is a solo project that will be read
  months from now by someone with no memory of writing it.
- When something in `docs/spec.md` is ambiguous or contradicts itself, say so rather than
  picking silently.
