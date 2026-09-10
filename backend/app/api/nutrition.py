"""Nutrition section. One row per day.

spec.md section 2 models a day's intake as a single row with a `meals` JSON
column for itemization, and the day payload exposes `nutrition` as one object
(or null), not a list — unlike training/sleep/recovery/symptoms. A second POST
for a date that already has a nutrition row is rejected with 409; PATCH the
existing row instead.

ASSUMPTION FLAGGED FOR CONFIRMATION: spec.md section 3's recall-decay table
has no row for nutrition at all. Treated here as "subjective effort" (same-day
window) since recalling exact intake is a self-report task, not an objective
measurement — but this is a genuine gap in the spec, not a documented rule.
"""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import (
    apply_partial_update,
    assert_date_not_too_far_future,
    get_current_athlete,
    get_or_create_daily_entry,
)
from app.config import ATHLETE_TIMEZONE
from app.db import get_db
from app.models import Athlete, Nutrition
from app.provenance import FieldGroup, recall_confidence, source_confidence
from app.schemas.nutrition import NutritionCreate, NutritionRead, NutritionUpdate

router = APIRouter(tags=["nutrition"])


@router.post(
    "/days/{date}/nutrition", response_model=NutritionRead, status_code=status.HTTP_201_CREATED
)
def create_nutrition(
    date: dt.date,
    payload: NutritionCreate,
    db: Session = Depends(get_db),
    athlete: Athlete = Depends(get_current_athlete),
) -> Nutrition:
    assert_date_not_too_far_future(date)
    now = dt.datetime.now(dt.timezone.utc)

    try:
        entry = get_or_create_daily_entry(db, athlete, date)

        existing = db.query(Nutrition).filter_by(daily_entry_id=entry.id).first()
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="nutrition already logged for this date; PATCH the existing row instead",
            )

        row = Nutrition(
            athlete_id=athlete.id,
            daily_entry_id=entry.id,
            date=date,
            protein_g=payload.protein_g,
            carbs_g=payload.carbs_g,
            fat_g=payload.fat_g,
            calories=payload.calories,
            training_phase=payload.training_phase.value if payload.training_phase else None,
            training_load=payload.training_load,
            meals=payload.meals,
            source=payload.source,
        )
        row.source_confidence = source_confidence(row.source)
        row.recall_confidence = recall_confidence(
            FieldGroup.SUBJECTIVE_EFFORT,
            entry_date=date,
            created_at=now,
            athlete_tz=ATHLETE_TIMEZONE,
        )
        db.add(row)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc.orig)) from exc

    db.refresh(row)
    return row


@router.patch("/nutrition/{nutrition_id}", response_model=NutritionRead)
def update_nutrition(
    nutrition_id: int,
    payload: NutritionUpdate,
    db: Session = Depends(get_db),
    athlete: Athlete = Depends(get_current_athlete),
) -> Nutrition:
    row = db.get(Nutrition, nutrition_id)
    if row is None or row.athlete_id != athlete.id:
        raise HTTPException(status_code=404, detail="nutrition row not found")

    data = payload.model_dump(exclude_unset=True)
    apply_partial_update(row, data)

    if "source" in data:
        row.source_confidence = source_confidence(row.source)

    row.recall_confidence = recall_confidence(
        FieldGroup.SUBJECTIVE_EFFORT,
        entry_date=row.date,
        created_at=dt.datetime.now(dt.timezone.utc),
        athlete_tz=ATHLETE_TIMEZONE,
    )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc.orig)) from exc

    db.refresh(row)
    return row


@router.delete("/nutrition/{nutrition_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_nutrition(
    nutrition_id: int,
    db: Session = Depends(get_db),
    athlete: Athlete = Depends(get_current_athlete),
) -> None:
    row = db.get(Nutrition, nutrition_id)
    if row is None or row.athlete_id != athlete.id:
        raise HTTPException(status_code=404, detail="nutrition row not found")
    db.delete(row)
    db.commit()
