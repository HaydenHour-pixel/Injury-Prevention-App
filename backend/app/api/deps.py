"""Shared FastAPI dependencies and small helpers used by every section router."""

from __future__ import annotations

import datetime as dt
from enum import Enum
from zoneinfo import ZoneInfo

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import ATHLETE_TIMEZONE
from app.db import get_db
from app.models import Athlete, DailyEntry


def get_current_athlete(db: Session = Depends(get_db)) -> Athlete:
    """Single-user app: there is exactly one athlete row, and every endpoint
    uses it. No athlete_id in any path, no auth.
    """
    athlete = db.query(Athlete).first()
    if athlete is None:
        raise HTTPException(status_code=404, detail="no athlete configured")
    return athlete


def get_or_create_daily_entry(db: Session, athlete: Athlete, date: dt.date) -> DailyEntry:
    """spec.md section 4: logging happens per section, not per day. Every
    section write get-or-creates the daily_entry for (athlete, date) so a
    section can be logged without one already existing.

    Only flushes, never commits — the caller adds its section row and commits
    both in one transaction, so a failed section insert takes this insert down
    with it rather than leaving an orphan daily_entry behind.
    """
    entry = db.query(DailyEntry).filter_by(athlete_id=athlete.id, date=date).first()
    if entry is None:
        entry = DailyEntry(athlete_id=athlete.id, date=date)
        db.add(entry)
        db.flush()
    return entry


def assert_date_not_too_far_future(date: dt.date) -> None:
    """spec.md's dates rule: the server never derives a date from its own
    clock, but it does validate against "now" here to catch typos. "Now" is
    the athlete's local today, not the server's UTC today, for the same reason
    dates are never derived from a UTC timestamp elsewhere in this app.
    """
    today_local = dt.datetime.now(ZoneInfo(ATHLETE_TIMEZONE)).date()
    if date > today_local + dt.timedelta(days=1):
        raise HTTPException(
            status_code=422,
            detail=f"date {date.isoformat()} is more than 1 day in the future",
        )


def apply_partial_update(row: object, data: dict) -> None:
    """Assign only the fields the client actually sent (`exclude_unset=True`
    on the Update schema), converting any enum values to their plain string —
    slice 1a's rule is strings in SQLite, no native enum types.
    """
    for field, value in data.items():
        if isinstance(value, Enum):
            value = value.value
        setattr(row, field, value)
