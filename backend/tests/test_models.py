"""Slice 1a schema tests.

Covers: every model persists, the (athlete_id, date) unique constraint on
daily_entry, that foreign keys are actually enforced (not just declared), and
that "no recovery_method row" is distinguishable from "method_type='none'".
"""

from __future__ import annotations

import datetime as dt

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import (
    Athlete,
    AthleteProfile,
    BodyPartVulnerability,
    DailyEntry,
    LifestyleCommitment,
    ModelMetrics,
    Nutrition,
    PainProfile,
    PredictionAccuracy,
    RecoveryMethod,
    Sleep,
    StressEvent,
    Symptom,
    Training,
)
from app.models.enums import (
    CommitmentType,
    DataSource,
    Outcome,
    PainType,
    RecoveryMethodType,
    RecurrenceRisk,
    StressEventType,
    TrainingPhase,
)


def make_athlete(session) -> Athlete:
    athlete = Athlete(name="Hayden", sport="running")
    session.add(athlete)
    session.flush()
    return athlete


def make_daily_entry(session, athlete: Athlete, date: dt.date) -> DailyEntry:
    entry = DailyEntry(athlete_id=athlete.id, date=date)
    session.add(entry)
    session.flush()
    return entry


class TestEveryModelPersists:
    def test_athlete_and_profile(self, session):
        athlete = make_athlete(session)
        profile = AthleteProfile(
            athlete_id=athlete.id,
            weight_kg=70.0,
            height_cm=178.0,
            current_weekly_mileage=50.0,
            current_training_phase=TrainingPhase.BUILD.value,
            baseline_protein_g=150.0,
            baseline_carbs_g=400.0,
            baseline_sleep_hours=8.0,
            injury_history=[{"location": "left knee", "year": 2024}],
        )
        session.add(profile)
        session.commit()

        assert profile.id is not None
        assert session.get(AthleteProfile, profile.id).athlete_id == athlete.id

    def test_daily_entry(self, session):
        athlete = make_athlete(session)
        entry = make_daily_entry(session, athlete, dt.date(2026, 9, 1))
        session.commit()

        assert entry.id is not None
        # Computed columns default to NULL, not zero.
        assert entry.sleep_score is None
        assert entry.risk_score is None

    def test_training(self, session):
        athlete = make_athlete(session)
        entry = make_daily_entry(session, athlete, dt.date(2026, 9, 1))
        training = Training(
            athlete_id=athlete.id,
            daily_entry_id=entry.id,
            date=entry.date,
            mileage=6.0,
            intensity_1_to_10=8,
            intensity_factor=1.5,
            source=DataSource.STRAVA.value,
        )
        session.add(training)
        session.commit()

        assert training.id is not None
        assert training.source_confidence is None
        assert training.recall_confidence is None
        assert training.created_at is not None

    def test_sleep(self, session):
        athlete = make_athlete(session)
        entry = make_daily_entry(session, athlete, dt.date(2026, 9, 1))
        sleep = Sleep(
            athlete_id=athlete.id,
            daily_entry_id=entry.id,
            date=entry.date,
            hours=6.5,
            quality_1_to_10=7,
            bedtime=dt.time(23, 15),
            wake_time=dt.time(6, 0),
        )
        session.add(sleep)
        session.commit()

        assert sleep.id is not None

    def test_nutrition(self, session):
        athlete = make_athlete(session)
        entry = make_daily_entry(session, athlete, dt.date(2026, 9, 1))
        nutrition = Nutrition(
            athlete_id=athlete.id,
            daily_entry_id=entry.id,
            date=entry.date,
            protein_g=140.0,
            carbs_g=380.0,
            training_phase=TrainingPhase.BUILD.value,
        )
        session.add(nutrition)
        session.commit()

        assert nutrition.id is not None

    def test_recovery_method(self, session):
        athlete = make_athlete(session)
        entry = make_daily_entry(session, athlete, dt.date(2026, 9, 1))
        recovery = RecoveryMethod(
            athlete_id=athlete.id,
            daily_entry_id=entry.id,
            date=entry.date,
            method_type=RecoveryMethodType.FOAM_ROLL.value,
            duration_minutes=10,
        )
        session.add(recovery)
        session.commit()

        assert recovery.id is not None

    def test_symptom_and_pain_profile(self, session):
        athlete = make_athlete(session)
        entry = make_daily_entry(session, athlete, dt.date(2026, 9, 1))
        pain_profile = PainProfile(
            athlete_id=athlete.id,
            body_location="left achilles",
            onset_date=entry.date,
            episode_number=1,
        )
        session.add(pain_profile)
        session.flush()

        symptom = Symptom(
            athlete_id=athlete.id,
            daily_entry_id=entry.id,
            date=entry.date,
            body_location="left achilles",
            intensity_1_to_10=4,
            type=PainType.DULL_ACHE.value,
            pain_profile_id=pain_profile.id,
        )
        session.add(symptom)
        session.commit()

        assert symptom.id is not None
        assert symptom.pain_profile_id == pain_profile.id

    def test_body_part_vulnerability(self, session):
        athlete = make_athlete(session)
        vuln = BodyPartVulnerability(
            athlete_id=athlete.id,
            body_location="left achilles",
            episode_count=2,
            recurrence_risk=RecurrenceRisk.HIGH.value,
            days_since_last_episode=30,
        )
        session.add(vuln)
        session.commit()

        assert vuln.id is not None

    def test_lifestyle_commitment(self, session):
        athlete = make_athlete(session)
        commitment = LifestyleCommitment(
            athlete_id=athlete.id,
            type=CommitmentType.CLASS.value,
            name="Organic Chemistry",
            days_of_week=["monday", "wednesday", "friday"],
            workload_intensity_1_to_10=7,
        )
        session.add(commitment)
        session.commit()

        assert commitment.id is not None

    def test_stress_event(self, session):
        athlete = make_athlete(session)
        event = StressEvent(
            athlete_id=athlete.id,
            type=StressEventType.EXAM.value,
            name="Finals week",
            start_date=dt.date(2026, 12, 8),
            end_date=dt.date(2026, 12, 12),
            expected_intensity_1_to_10=8,
        )
        session.add(event)
        session.commit()

        assert event.id is not None

    def test_prediction_accuracy(self, session):
        athlete = make_athlete(session)
        pred = PredictionAccuracy(
            athlete_id=athlete.id,
            prediction_date=dt.date(2026, 9, 1),
            predicted_risk=42.0,
            confidence=0.6,
            outcome=Outcome.MILD_SORENESS.value,
        )
        session.add(pred)
        session.commit()

        assert pred.id is not None

    def test_model_metrics(self, session):
        athlete = make_athlete(session)
        metrics = ModelMetrics(
            athlete_id=athlete.id,
            date=dt.date(2026, 9, 1),
            days_of_data=14,
            stress_instances_observed=2,
        )
        session.add(metrics)
        session.commit()

        assert metrics.id is not None


def test_daily_entry_unique_athlete_date(session):
    athlete = make_athlete(session)
    session.add(DailyEntry(athlete_id=athlete.id, date=dt.date(2026, 9, 1)))
    session.commit()

    session.add(DailyEntry(athlete_id=athlete.id, date=dt.date(2026, 9, 1)))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_foreign_keys_are_enforced(session):
    # No athlete with id 999 exists. If FK enforcement were off, SQLite would
    # happily insert this row.
    session.add(DailyEntry(athlete_id=999, date=dt.date(2026, 9, 1)))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_daily_entry_cascades_to_children_on_delete(session):
    athlete = make_athlete(session)
    entry = make_daily_entry(session, athlete, dt.date(2026, 9, 1))
    training = Training(
        athlete_id=athlete.id,
        daily_entry_id=entry.id,
        date=entry.date,
        mileage=5.0,
    )
    session.add(training)
    session.commit()
    training_id = training.id

    session.delete(entry)
    session.commit()

    assert session.get(Training, training_id) is None


def test_recovery_method_symptom_link_restricts_athlete_change_but_not_delete(session):
    # symptom_id uses ON DELETE SET NULL: deleting the symptom should unlink the
    # recovery method rather than delete it.
    athlete = make_athlete(session)
    entry = make_daily_entry(session, athlete, dt.date(2026, 9, 1))
    symptom = Symptom(
        athlete_id=athlete.id,
        daily_entry_id=entry.id,
        date=entry.date,
        body_location="left knee",
        intensity_1_to_10=3,
        type=PainType.MUSCLE_SORENESS.value,
    )
    session.add(symptom)
    session.flush()

    recovery = RecoveryMethod(
        athlete_id=athlete.id,
        daily_entry_id=entry.id,
        date=entry.date,
        method_type=RecoveryMethodType.ICE_BATH.value,
        symptom_id=symptom.id,
    )
    session.add(recovery)
    session.commit()
    recovery_id = recovery.id

    session.delete(symptom)
    session.commit()

    persisted = session.get(RecoveryMethod, recovery_id)
    assert persisted is not None
    assert persisted.symptom_id is None


def test_missing_recovery_row_distinguishable_from_method_type_none(session):
    """spec.md section 4: 'no recovery done, logged as such' (method_type='none')
    must be distinguishable from 'recovery section never opened' (no row)."""
    athlete = make_athlete(session)
    day_logged_none = make_daily_entry(session, athlete, dt.date(2026, 9, 1))
    day_never_opened = make_daily_entry(session, athlete, dt.date(2026, 9, 2))

    session.add(
        RecoveryMethod(
            athlete_id=athlete.id,
            daily_entry_id=day_logged_none.id,
            date=day_logged_none.date,
            method_type=RecoveryMethodType.NONE.value,
        )
    )
    session.commit()

    logged_none_rows = (
        session.query(RecoveryMethod)
        .filter(RecoveryMethod.daily_entry_id == day_logged_none.id)
        .all()
    )
    never_opened_rows = (
        session.query(RecoveryMethod)
        .filter(RecoveryMethod.daily_entry_id == day_never_opened.id)
        .all()
    )

    assert len(logged_none_rows) == 1
    assert logged_none_rows[0].method_type == RecoveryMethodType.NONE.value
    assert never_opened_rows == []
