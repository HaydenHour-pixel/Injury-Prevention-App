from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field

from app.models.enums import PainOnset, PainType
from app.schemas.common import ORMModel

# No `source` field: symptoms are always athlete-entered self-reports.
# source_confidence is fixed to the manual value server-side (see
# app/api/symptoms.py).


class SymptomCreate(BaseModel):
    body_location: str
    intensity_1_to_10: int = Field(ge=1, le=10)
    type: PainType
    onset: PainOnset | None = None
    limiting: bool = False
    description: str | None = None
    active: bool = True
    pain_profile_id: int | None = None


class SymptomUpdate(BaseModel):
    body_location: str | None = None
    intensity_1_to_10: int | None = Field(default=None, ge=1, le=10)
    type: PainType | None = None
    onset: PainOnset | None = None
    limiting: bool | None = None
    description: str | None = None
    active: bool | None = None
    pain_profile_id: int | None = None


class SymptomRead(ORMModel):
    id: int
    daily_entry_id: int | None
    date: dt.date
    body_location: str
    intensity_1_to_10: int
    type: str
    onset: str | None
    limiting: bool
    description: str | None
    active: bool
    pain_profile_id: int | None
    source_confidence: float | None
    recall_confidence: float | None
    created_at: dt.datetime
