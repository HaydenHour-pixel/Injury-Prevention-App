from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel

# Sleep can't come from Strava (CLAUDE.md rules out wearable integration for
# MVP), but training can, once slice 6 builds the import. The column exists
# now; only "manual" is reachable until then.
TrainingSource = Literal["strava", "manual"]


class TrainingCreate(BaseModel):
    mileage: float | None = None
    intensity_1_to_10: int | None = Field(default=None, ge=1, le=10)
    elevation_gain_ft: float | None = None
    notes: str | None = None
    source: TrainingSource = "manual"


class TrainingUpdate(BaseModel):
    mileage: float | None = None
    intensity_1_to_10: int | None = Field(default=None, ge=1, le=10)
    elevation_gain_ft: float | None = None
    notes: str | None = None
    source: TrainingSource | None = None


class TrainingRead(ORMModel):
    id: int
    daily_entry_id: int
    date: dt.date
    mileage: float | None
    intensity_1_to_10: int | None
    # Derived by the scoring layer (spec.md section 5.3) — always null until
    # slice 2 populates it. Not settable via this API.
    intensity_factor: float | None
    elevation_gain_ft: float | None
    notes: str | None
    source: str | None
    source_confidence: float | None
    recall_confidence: float | None
    created_at: dt.datetime
