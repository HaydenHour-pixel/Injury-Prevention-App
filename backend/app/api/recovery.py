"""Recovery section. Multiple rows per day are expected.

`method_type='none'` means the athlete opened the section and recorded doing
nothing — a normal, valid create (spec.md section 4), not a special case.

There is no `source` column on this table (spec.md section 2 lists no source
field for recovery_method): recovery is always athlete-entered, so
source_confidence is fixed to the manual value.

ASSUMPTION FLAGGED FOR CONFIRMATION: spec.md section 3's recall-decay table
has no row for recovery methods. When a felt intensity is logged for the
session, this treats it like training's subjective effort (same reasoning:
a felt rating, not a fact); otherwise the row is treated as objective
(duration/time applied, akin to mileage or bedtime). This fills a genuine gap
in the spec, not a documented rule.
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
from app.models import Athlete, RecoveryMethod
from app.models.enums import DataSource
from app.provenance import FieldGroup, recall_confidence, source_confidence
from app.schemas.recovery import RecoveryCreate, RecoveryRead, RecoveryUpdate

router = APIRouter(tags=["recovery"])

_RECOVERY_SOURCE = DataSource.MANUAL.value


def _recall_field_group(intensity_1_to_10: int | None) -> FieldGroup:
    return FieldGroup.SUBJECTIVE_EFFORT if intensity_1_to_10 is not None else FieldGroup.OBJECTIVE


@router.post(
    "/days/{date}/recovery", response_model=RecoveryRead, status_code=status.HTTP_201_CREATED
)
def create_recovery(
    date: dt.date,
    payload: RecoveryCreate,
    db: Session = Depends(get_db),
    athlete: Athlete = Depends(get_current_athlete),
) -> RecoveryMethod:
    assert_date_not_too_far_future(date)
    now = dt.datetime.now(dt.timezone.utc)

    try:
        entry = get_or_create_daily_entry(db, athlete, date)
        row = RecoveryMethod(
            athlete_id=athlete.id,
            daily_entry_id=entry.id,
            date=date,
            method_type=payload.method_type.value,
            duration_minutes=payload.duration_minutes,
            intensity_1_to_10=payload.intensity_1_to_10,
            applied_at=payload.applied_at,
            symptom_id=payload.symptom_id,
        )
        row.source_confidence = source_confidence(_RECOVERY_SOURCE)
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


@router.patch("/recovery/{recovery_id}", response_model=RecoveryRead)
def update_recovery(
    recovery_id: int,
    payload: RecoveryUpdate,
    db: Session = Depends(get_db),
    athlete: Athlete = Depends(get_current_athlete),
) -> RecoveryMethod:
    row = db.get(RecoveryMethod, recovery_id)
    if row is None or row.athlete_id != athlete.id:
        raise HTTPException(status_code=404, detail="recovery row not found")

    apply_partial_update(row, payload.model_dump(exclude_unset=True))

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


@router.delete("/recovery/{recovery_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_recovery(
    recovery_id: int,
    db: Session = Depends(get_db),
    athlete: Athlete = Depends(get_current_athlete),
) -> None:
    row = db.get(RecoveryMethod, recovery_id)
    if row is None or row.athlete_id != athlete.id:
        raise HTTPException(status_code=404, detail="recovery row not found")
    db.delete(row)
    db.commit()
