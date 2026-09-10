"""Training section. Multiple rows per day are expected (doubles).

`intensity_1_to_10` is spec.md section 3's "subjective effort" field group;
mileage and elevation are objective. A row's recall_confidence follows the
more lag-sensitive field when one is present, and is 1.0 (objective) when the
row has no reported intensity at all.
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
from app.models import Athlete, Training
from app.provenance import FieldGroup, recall_confidence, source_confidence
from app.schemas.training import TrainingCreate, TrainingRead, TrainingUpdate

router = APIRouter(tags=["training"])


def _recall_field_group(intensity_1_to_10: int | None) -> FieldGroup:
    return FieldGroup.SUBJECTIVE_EFFORT if intensity_1_to_10 is not None else FieldGroup.OBJECTIVE


@router.post(
    "/days/{date}/training", response_model=TrainingRead, status_code=status.HTTP_201_CREATED
)
def create_training(
    date: dt.date,
    payload: TrainingCreate,
    db: Session = Depends(get_db),
    athlete: Athlete = Depends(get_current_athlete),
) -> Training:
    assert_date_not_too_far_future(date)
    now = dt.datetime.now(dt.timezone.utc)

    try:
        entry = get_or_create_daily_entry(db, athlete, date)
        row = Training(
            athlete_id=athlete.id,
            daily_entry_id=entry.id,
            date=date,
            mileage=payload.mileage,
            intensity_1_to_10=payload.intensity_1_to_10,
            elevation_gain_ft=payload.elevation_gain_ft,
            notes=payload.notes,
            source=payload.source,
        )
        row.source_confidence = source_confidence(row.source)
        row.recall_confidence = recall_confidence(
            _recall_field_group(row.intensity_1_to_10),
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


@router.patch("/training/{training_id}", response_model=TrainingRead)
def update_training(
    training_id: int,
    payload: TrainingUpdate,
    db: Session = Depends(get_db),
    athlete: Athlete = Depends(get_current_athlete),
) -> Training:
    row = db.get(Training, training_id)
    if row is None or row.athlete_id != athlete.id:
        raise HTTPException(status_code=404, detail="training row not found")

    data = payload.model_dump(exclude_unset=True)
    apply_partial_update(row, data)

    if "source" in data:
        row.source_confidence = source_confidence(row.source)

    # The value is being restated now, so recall lag is measured from this
    # PATCH's time, not the row's original created_at.
    row.recall_confidence = recall_confidence(
        _recall_field_group(row.intensity_1_to_10),
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


@router.delete("/training/{training_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_training(
    training_id: int,
    db: Session = Depends(get_db),
    athlete: Athlete = Depends(get_current_athlete),
) -> None:
    row = db.get(Training, training_id)
    if row is None or row.athlete_id != athlete.id:
        raise HTTPException(status_code=404, detail="training row not found")
    db.delete(row)
    db.commit()
