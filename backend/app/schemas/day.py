"""The day payload: the point of slice 1b.

Response shape must preserve absent-vs-logged (spec.md section 4): an empty
list or null means the section was never touched; a populated list — even a
single recovery row with `method_type='none'` — means it was. `completeness`
reflects row existence, not whether the content is "full" or non-zero.
"""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel

from app.schemas.nutrition import NutritionRead
from app.schemas.recovery import RecoveryRead
from app.schemas.sleep import SleepRead
from app.schemas.symptom import SymptomRead
from app.schemas.training import TrainingRead


class Completeness(BaseModel):
    training: bool
    sleep: bool
    nutrition: bool
    recovery: bool
    symptoms: bool


class DayResponse(BaseModel):
    date: dt.date
    daily_entry_exists: bool
    training: list[TrainingRead]
    sleep: list[SleepRead]
    nutrition: NutritionRead | None
    recovery: list[RecoveryRead]
    symptoms: list[SymptomRead]
    # NULL = not answered, true = athlete confirmed no pain that day (spec.md
    # section 4). Cleared back to NULL by logging any symptom for the date.
    no_pain_confirmed: bool | None
    completeness: Completeness


class DaySummary(BaseModel):
    """One calendar tile: enough to render the range view without shipping
    every section's full content for every day in range.
    """

    date: dt.date
    daily_entry_exists: bool
    completeness: Completeness
