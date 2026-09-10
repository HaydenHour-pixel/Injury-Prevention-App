"""Symptom section. Multiple rows per day are expected (different locations).

`intensity_1_to_10` maps unambiguously to spec.md section 3's "symptom
intensity" field group — no assumption needed here, unlike nutrition or
recovery. No `source` column on this table: symptoms are always
athlete-entered, so source_confidence is fixed to the manual value.

No DELETE for daily_entry is exposed anywhere in this API (deliberate — see
app/api/deps.py and slice 1a), but this router's own DELETE removes a symptom
row outright. That's a distinct, legitimate operation: correcting a
mis-logged entry, not losing calibration history to a cascade.
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
from app.models import Athlete, Symptom
from app.models.enums import DataSource
from app.provenance import FieldGroup, recall_confidence, source_confidence
from app.schemas.symptom import SymptomCreate, SymptomRead, SymptomUpdate

router = APIRouter(tags=["symptoms"])

_SYMPTOM_SOURCE = DataSource.MANUAL.value


@router.post(
    "/days/{date}/symptoms", response_model=SymptomRead, status_code=status.HTTP_201_CREATED
)
def create_symptom(
    date: dt.date,
    payload: SymptomCreate,
    db: Session = Depends(get_db),
    athlete: Athlete = Depends(get_current_athlete),
) -> Symptom:
    assert_date_not_too_far_future(date)
    now = dt.datetime.now(dt.timezone.utc)

    try:
        entry = get_or_create_daily_entry(db, athlete, date)
        row = Symptom(
            athlete_id=athlete.id,
            daily_entry_id=entry.id,
            date=date,
            body_location=payload.body_location,
            intensity_1_to_10=payload.intensity_1_to_10,
            type=payload.type.value,
            onset=payload.onset.value if payload.onset else None,
            limiting=payload.limiting,
            description=payload.description,
            active=payload.active,
            pain_profile_id=payload.pain_profile_id,
        )
        row.source_confidence = source_confidence(_SYMPTOM_SOURCE)
        row.recall_confidence = recall_confidence(
            FieldGroup.SYMPTOM_INTENSITY,
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


@router.patch("/symptoms/{symptom_id}", response_model=SymptomRead)
def update_symptom(
    symptom_id: int,
    payload: SymptomUpdate,
    db: Session = Depends(get_db),
    athlete: Athlete = Depends(get_current_athlete),
) -> Symptom:
    row = db.get(Symptom, symptom_id)
    if row is None or row.athlete_id != athlete.id:
        raise HTTPException(status_code=404, detail="symptom row not found")

    apply_partial_update(row, payload.model_dump(exclude_unset=True))

    row.recall_confidence = recall_confidence(
        FieldGroup.SYMPTOM_INTENSITY,
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


@router.delete("/symptoms/{symptom_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_symptom(
    symptom_id: int,
    db: Session = Depends(get_db),
    athlete: Athlete = Depends(get_current_athlete),
) -> None:
    row = db.get(Symptom, symptom_id)
    if row is None or row.athlete_id != athlete.id:
        raise HTTPException(status_code=404, detail="symptom row not found")
    db.delete(row)
    db.commit()
