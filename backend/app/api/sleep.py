"""Sleep section. Multiple rows per day are expected (naps — see `is_nap`).

Source is always "manual": CLAUDE.md rules out any wearable integration for
MVP, so there's nothing else to choose from. `quality_1_to_10` is spec.md
section 3's "sleep quality" field group; hours/bedtime/wake_time are
objective.
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
from app.models import Athlete, Sleep
from app.models.enums import DataSource
from app.provenance import FieldGroup, recall_confidence, source_confidence
from app.schemas.sleep import SleepCreate, SleepRead, SleepUpdate

router = APIRouter(tags=["sleep"])

_SLEEP_SOURCE = DataSource.MANUAL.value


def _recall_field_group(quality_1_to_10: int | None) -> FieldGroup:
    return FieldGroup.SLEEP_QUALITY if quality_1_to_10 is not None else FieldGroup.OBJECTIVE


@router.post("/days/{date}/sleep", response_model=SleepRead, status_code=status.HTTP_201_CREATED)
def create_sleep(
    date: dt.date,
    payload: SleepCreate,
    db: Session = Depends(get_db),
    athlete: Athlete = Depends(get_current_athlete),
) -> Sleep:
    assert_date_not_too_far_future(date)
    now = dt.datetime.now(dt.timezone.utc)

    try:
        entry = get_or_create_daily_entry(db, athlete, date)
        row = Sleep(
            athlete_id=athlete.id,
            daily_entry_id=entry.id,
            date=date,
            hours=payload.hours,
            quality_1_to_10=payload.quality_1_to_10,
            bedtime=payload.bedtime,
            wake_time=payload.wake_time,
            is_nap=payload.is_nap,
            source=_SLEEP_SOURCE,
        )
        row.source_confidence = source_confidence(row.source)
        row.recall_confidence = recall_confidence(
            _recall_field_group(row.quality_1_to_10),
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


@router.patch("/sleep/{sleep_id}", response_model=SleepRead)
def update_sleep(
    sleep_id: int,
    payload: SleepUpdate,
    db: Session = Depends(get_db),
    athlete: Athlete = Depends(get_current_athlete),
) -> Sleep:
    row = db.get(Sleep, sleep_id)
    if row is None or row.athlete_id != athlete.id:
        raise HTTPException(status_code=404, detail="sleep row not found")

    apply_partial_update(row, payload.model_dump(exclude_unset=True))

    row.recall_confidence = recall_confidence(
        _recall_field_group(row.quality_1_to_10),
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


@router.delete("/sleep/{sleep_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_sleep(
    sleep_id: int,
    db: Session = Depends(get_db),
    athlete: Athlete = Depends(get_current_athlete),
) -> None:
    row = db.get(Sleep, sleep_id)
    if row is None or row.athlete_id != athlete.id:
        raise HTTPException(status_code=404, detail="sleep row not found")
    db.delete(row)
    db.commit()
