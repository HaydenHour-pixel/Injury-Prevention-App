from __future__ import annotations

import datetime as dt
from typing import Any, Literal

from pydantic import BaseModel

from app.models.enums import TrainingPhase
from app.schemas.common import ORMModel

NutritionSource = Literal["umass_dining_menu", "manual_food_entry"]


class NutritionCreate(BaseModel):
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    calories: float | None = None
    training_phase: TrainingPhase | None = None
    training_load: float | None = None
    meals: Any | None = None
    source: NutritionSource = "manual_food_entry"


class NutritionUpdate(BaseModel):
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    calories: float | None = None
    training_phase: TrainingPhase | None = None
    training_load: float | None = None
    meals: Any | None = None
    source: NutritionSource | None = None


class NutritionRead(ORMModel):
    id: int
    daily_entry_id: int
    date: dt.date
    protein_g: float | None
    carbs_g: float | None
    fat_g: float | None
    calories: float | None
    training_phase: str | None
    training_load: float | None
    meals: Any | None
    source: str | None
    source_confidence: float | None
    recall_confidence: float | None
    created_at: dt.datetime
