from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field

from app.models.enums import RecoveryMethodType
from app.schemas.common import ORMModel

# No `source` field: recovery is always athlete-entered, there's no table
# column for it (spec.md section 2 lists "method type, duration, intensity,
# time applied, optional linked symptom" — no source). source_confidence is
# fixed to the manual value server-side (see app/api/recovery.py).


class RecoveryCreate(BaseModel):
    method_type: RecoveryMethodType
    duration_minutes: int | None = None
    intensity_1_to_10: int | None = Field(default=None, ge=1, le=10)
    applied_at: dt.time | None = None
    symptom_id: int | None = None


class RecoveryUpdate(BaseModel):
    method_type: RecoveryMethodType | None = None
    duration_minutes: int | None = None
    intensity_1_to_10: int | None = Field(default=None, ge=1, le=10)
    applied_at: dt.time | None = None
    symptom_id: int | None = None


class RecoveryRead(ORMModel):
    id: int
    daily_entry_id: int
    date: dt.date
    method_type: str
    duration_minutes: int | None
    intensity_1_to_10: int | None
    applied_at: dt.time | None
    symptom_id: int | None
    source_confidence: float | None
    recall_confidence: float | None
    created_at: dt.datetime
