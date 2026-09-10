from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel

# No `source` field here, deliberately: CLAUDE.md rules out Apple HealthKit /
# any wearable integration for MVP ("Sleep is manual entry"), so there is
# nothing else to choose from. The row's source is always fixed to "manual"
# server-side (see app/api/sleep.py).


class SleepCreate(BaseModel):
    hours: float | None = None
    quality_1_to_10: int | None = Field(default=None, ge=1, le=10)
    bedtime: dt.time | None = None
    wake_time: dt.time | None = None
    is_nap: bool = False


class SleepUpdate(BaseModel):
    hours: float | None = None
    quality_1_to_10: int | None = Field(default=None, ge=1, le=10)
    bedtime: dt.time | None = None
    wake_time: dt.time | None = None
    is_nap: bool | None = None


class SleepRead(ORMModel):
    id: int
    daily_entry_id: int
    date: dt.date
    hours: float | None
    quality_1_to_10: int | None
    bedtime: dt.time | None
    wake_time: dt.time | None
    is_nap: bool
    source: str | None
    source_confidence: float | None
    recall_confidence: float | None
    created_at: dt.datetime
