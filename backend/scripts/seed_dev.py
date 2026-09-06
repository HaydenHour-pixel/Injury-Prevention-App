"""Development seed data.

Inserts one athlete, a profile, and three consecutive daily entries with
training, sleep, and nutrition children. Deliberately makes concrete the
distinction in spec.md section 4:

  day 1: recovery_method row with method_type='none' (recovery section opened,
         athlete recorded doing nothing)
  day 2: no recovery_method row at all (section never opened)
  day 3: a real recovery_method row (stretching)

Safe to re-run against a fresh database; it does not check for existing data,
so run it once per empty database.
"""

from __future__ import annotations

import datetime as dt

from app.db import SessionLocal
from app.models import Athlete, AthleteProfile, DailyEntry, Nutrition, RecoveryMethod, Sleep, Training
from app.models.enums import DataSource, RecoveryMethodType, TrainingPhase


def seed(session) -> None:
    athlete = Athlete(name="Hayden", sport="running", onboarding_completed=True)
    session.add(athlete)
    session.flush()

    profile = AthleteProfile(
        athlete_id=athlete.id,
        weight_kg=70.0,
        height_cm=178.0,
        gender="male",
        age=22,
        current_weekly_mileage=50.0,
        peak_weekly_mileage=65.0,
        current_training_phase=TrainingPhase.BUILD.value,
        baseline_protein_g=150.0,
        baseline_carbs_g=400.0,
        baseline_fat_g=70.0,
        baseline_calories=2800.0,
        baseline_sleep_hours=8.0,
    )
    session.add(profile)

    start_date = dt.date(2026, 9, 1)

    day1 = DailyEntry(athlete_id=athlete.id, date=start_date)
    day2 = DailyEntry(athlete_id=athlete.id, date=start_date + dt.timedelta(days=1))
    day3 = DailyEntry(athlete_id=athlete.id, date=start_date + dt.timedelta(days=2))
    session.add_all([day1, day2, day3])
    session.flush()

    for entry in (day1, day2, day3):
        session.add(
            Training(
                athlete_id=athlete.id,
                daily_entry_id=entry.id,
                date=entry.date,
                mileage=6.0,
                intensity_1_to_10=6,
                intensity_factor=1.2,
                elevation_gain_ft=150.0,
                source=DataSource.STRAVA.value,
            )
        )
        session.add(
            Sleep(
                athlete_id=athlete.id,
                daily_entry_id=entry.id,
                date=entry.date,
                hours=7.5,
                quality_1_to_10=7,
                bedtime=dt.time(22, 30),
                wake_time=dt.time(6, 30),
                source=DataSource.MANUAL.value,
            )
        )
        session.add(
            Nutrition(
                athlete_id=athlete.id,
                daily_entry_id=entry.id,
                date=entry.date,
                protein_g=140.0,
                carbs_g=380.0,
                fat_g=65.0,
                calories=2700.0,
                training_phase=TrainingPhase.BUILD.value,
                training_load=9.0,
                source=DataSource.MANUAL_FOOD_ENTRY.value,
            )
        )

    # Day 1: recovery section opened, athlete did nothing. A real row exists.
    session.add(
        RecoveryMethod(
            athlete_id=athlete.id,
            daily_entry_id=day1.id,
            date=day1.date,
            method_type=RecoveryMethodType.NONE.value,
        )
    )

    # Day 2: recovery section never opened. No row at all, on purpose.

    # Day 3: a real recovery session.
    session.add(
        RecoveryMethod(
            athlete_id=athlete.id,
            daily_entry_id=day3.id,
            date=day3.date,
            method_type=RecoveryMethodType.STRETCHING.value,
            duration_minutes=15,
            intensity_1_to_10=3,
            applied_at=dt.time(20, 0),
        )
    )

    session.commit()


def main() -> None:
    session = SessionLocal()
    try:
        seed(session)
        print("Seeded 1 athlete, 1 profile, 3 daily entries.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
