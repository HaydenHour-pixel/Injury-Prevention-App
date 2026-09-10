"""The day payload: full single-day view and the calendar-range summary.

Both endpoints are read-only — neither ever creates a daily_entry. Every
section is queried by (athlete_id, date) directly rather than by joining
through daily_entry_id, so the response stays correct even in the edge case
where a symptom's daily_entry_id has been nulled out by a daily_entry
deletion elsewhere (slice 1a) but the symptom's own date still identifies it.
"""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_athlete
from app.db import get_db
from app.models import Athlete, DailyEntry, Nutrition, RecoveryMethod, Sleep, Symptom, Training
from app.schemas.day import Completeness, DayResponse, DaySummary
from app.schemas.nutrition import NutritionRead
from app.schemas.recovery import RecoveryRead
from app.schemas.sleep import SleepRead
from app.schemas.symptom import SymptomRead
from app.schemas.training import TrainingRead

router = APIRouter(tags=["days"])

MAX_RANGE_DAYS = 120


@router.get("/days/{date}", response_model=DayResponse)
def get_day(
    date: dt.date,
    db: Session = Depends(get_db),
    athlete: Athlete = Depends(get_current_athlete),
) -> DayResponse:
    entry = db.query(DailyEntry).filter_by(athlete_id=athlete.id, date=date).first()
    daily_entry_exists = entry is not None
    no_pain_confirmed = entry.no_pain_confirmed if entry is not None else None

    training_rows = db.query(Training).filter_by(athlete_id=athlete.id, date=date).all()
    sleep_rows = db.query(Sleep).filter_by(athlete_id=athlete.id, date=date).all()
    # Singleton per day (see app/api/nutrition.py); most-recent guards against
    # a stray duplicate ever existing in the data.
    nutrition_row = (
        db.query(Nutrition)
        .filter_by(athlete_id=athlete.id, date=date)
        .order_by(Nutrition.created_at.desc())
        .first()
    )
    recovery_rows = db.query(RecoveryMethod).filter_by(athlete_id=athlete.id, date=date).all()
    symptom_rows = db.query(Symptom).filter_by(athlete_id=athlete.id, date=date).all()

    return DayResponse(
        date=date,
        daily_entry_exists=daily_entry_exists,
        training=[TrainingRead.model_validate(r) for r in training_rows],
        sleep=[SleepRead.model_validate(r) for r in sleep_rows],
        nutrition=NutritionRead.model_validate(nutrition_row) if nutrition_row else None,
        recovery=[RecoveryRead.model_validate(r) for r in recovery_rows],
        symptoms=[SymptomRead.model_validate(r) for r in symptom_rows],
        no_pain_confirmed=no_pain_confirmed,
        completeness=Completeness(
            training=len(training_rows) > 0,
            sleep=len(sleep_rows) > 0,
            nutrition=nutrition_row is not None,
            recovery=len(recovery_rows) > 0,
            # spec.md section 4: an explicit "no pain" confirmation is as
            # complete an answer for the section as a logged symptom.
            symptoms=len(symptom_rows) > 0 or no_pain_confirmed is True,
        ),
    )


@router.get("/days", response_model=list[DaySummary])
def get_days_range(
    start: dt.date = Query(...),
    end: dt.date = Query(...),
    db: Session = Depends(get_db),
    athlete: Athlete = Depends(get_current_athlete),
) -> list[DaySummary]:
    if end < start:
        raise HTTPException(status_code=422, detail="end date must not be before start date")

    span_days = (end - start).days + 1
    if span_days > MAX_RANGE_DAYS:
        raise HTTPException(
            status_code=422,
            detail=f"range spans {span_days} days; the maximum is {MAX_RANGE_DAYS}",
        )

    def dates_with(model) -> set[dt.date]:
        rows = (
            db.query(model.date)
            .filter(model.athlete_id == athlete.id, model.date.between(start, end))
            .distinct()
            .all()
        )
        return {row[0] for row in rows}

    daily_entry_dates = dates_with(DailyEntry)
    training_dates = dates_with(Training)
    sleep_dates = dates_with(Sleep)
    nutrition_dates = dates_with(Nutrition)
    recovery_dates = dates_with(RecoveryMethod)
    symptom_dates = dates_with(Symptom)
    no_pain_dates = {
        row[0]
        for row in db.query(DailyEntry.date)
        .filter(
            DailyEntry.athlete_id == athlete.id,
            DailyEntry.date.between(start, end),
            DailyEntry.no_pain_confirmed.is_(True),
        )
        .all()
    }

    return [
        DaySummary(
            date=day,
            daily_entry_exists=day in daily_entry_dates,
            completeness=Completeness(
                training=day in training_dates,
                sleep=day in sleep_dates,
                nutrition=day in nutrition_dates,
                recovery=day in recovery_dates,
                symptoms=(day in symptom_dates) or (day in no_pain_dates),
            ),
        )
        for day in (start + dt.timedelta(days=i) for i in range(span_days))
    ]
