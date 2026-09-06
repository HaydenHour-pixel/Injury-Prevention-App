"""Model bookkeeping: calibration outcomes and per-day model snapshots.

Populated by the calibration loop (slice 5) and the daily batch job (slice 4),
not by this slice. The tables exist now so the schema is complete, per the task:
schema only, no batch job or risk logic yet.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import Date, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin


class PredictionAccuracy(CreatedAtMixin, Base):
    """One row per calibration window (spec.md section 10): a risk prediction
    matched up against the actual outcome the athlete later reports.
    """

    __tablename__ = "prediction_accuracy"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    athlete_id: Mapped[int] = mapped_column(
        ForeignKey("athlete.id", ondelete="CASCADE"), nullable=False, index=True
    )

    prediction_date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)
    predicted_risk: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # Outcome, captured on the two-week cadence in spec.md section 10.
    outcome: Mapped[str | None] = mapped_column(String(30), nullable=True)
    outcome_location: Mapped[str | None] = mapped_column(String(60), nullable=True)
    outcome_duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # predicted_risk - actual_severity, once the outcome is known.
    calibration_error: Mapped[float | None] = mapped_column(Float, nullable=True)
    athlete_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)


class ModelMetrics(CreatedAtMixin, Base):
    """A per-day snapshot of the model's own state, one row per athlete per day."""

    __tablename__ = "model_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    athlete_id: Mapped[int] = mapped_column(
        ForeignKey("athlete.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)

    days_of_data: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stress_instances_observed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    variance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # From consistent over/underestimation across 4+ calibration windows,
    # -20 to +20 (spec.md section 10).
    calibration_offset: Mapped[float | None] = mapped_column(Float, nullable=True)
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Per-method efficacy, keyed by RecoveryMethodType value.
    per_method_efficacy: Mapped[Any | None] = mapped_column(JSON, nullable=True)
