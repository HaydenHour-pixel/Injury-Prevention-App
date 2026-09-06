"""The daily entry and the four logged tables that hang off it.

One `daily_entry` per athlete per date. `training`, `sleep`, `nutrition`, and
`recovery_method` are its children and each carries the provenance fields from
spec.md section 3.

Every child is a one-to-many. Doubles, naps, and two recovery sessions in an
evening are all ordinary.
"""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.athlete import Athlete
from app.models.base import Base, CreatedAtMixin, ProvenanceMixin

if TYPE_CHECKING:
    from app.models.symptoms import Symptom


class DailyEntry(CreatedAtMixin, Base):
    """One row per athlete per calendar day.

    `date` is the athlete's local calendar date. A run logged at 11:40pm belongs to
    that day. It is never derived from `created_at`.

    Every computed column below is nullable. NULL means "the batch job has not run
    for this day yet", which is a different fact from a computed score of 0.0. Do
    not default any of them.
    """

    __tablename__ = "daily_entry"
    __table_args__ = (UniqueConstraint("athlete_id", "date", name="uq_daily_entry_athlete_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    athlete_id: Mapped[int] = mapped_column(
        ForeignKey("athlete.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)

    # --- Dimension scores (spec.md section 5). Populated by slice 2. ---
    sleep_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    nutrition_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    training_load_normalized: Mapped[float | None] = mapped_column(Float, nullable=True)
    recovery_daily_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    symptom_severity: Mapped[float | None] = mapped_column(Float, nullable=True)

    # --- Rolling windows (spec.md sections 5.3 and 5.4). Populated by slice 3. ---
    daily_load: Mapped[float | None] = mapped_column(Float, nullable=True)
    load_7d: Mapped[float | None] = mapped_column(Float, nullable=True)
    load_28d: Mapped[float | None] = mapped_column(Float, nullable=True)
    acute_chronic_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    recovery_volume_7d: Mapped[float | None] = mapped_column(Float, nullable=True)
    recovery_adequacy: Mapped[float | None] = mapped_column(Float, nullable=True)
    recovery_shortfall: Mapped[float | None] = mapped_column(Float, nullable=True)

    # --- Context flags (spec.md section 6). Populated by slice 3. ---
    training_phase: Mapped[str | None] = mapped_column(String(30), nullable=True)
    in_stress_period: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    within_stress_pattern: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # --- Risk output (spec.md sections 7-9). Populated by slice 4. ---
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Each weighted burden term, kept so the athlete can see what drove the number.
    # spec.md section 7: "Every contribution must be displayable as a term".
    risk_terms: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    hard_limits_triggered: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    alert_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # A genuine event timestamp, in UTC, not a calendar day.
    alert_sent_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # When the batch job last computed the columns above. Lets a re-run be
    # idempotent without guessing (spec.md section 11).
    computed_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    athlete: Mapped[Athlete] = relationship(back_populates="daily_entries")
    training_sessions: Mapped[list[Training]] = relationship(
        back_populates="daily_entry", cascade="all, delete-orphan", passive_deletes=True
    )
    sleep_records: Mapped[list[Sleep]] = relationship(
        back_populates="daily_entry", cascade="all, delete-orphan", passive_deletes=True
    )
    nutrition_records: Mapped[list[Nutrition]] = relationship(
        back_populates="daily_entry", cascade="all, delete-orphan", passive_deletes=True
    )
    recovery_methods: Mapped[list[RecoveryMethod]] = relationship(
        back_populates="daily_entry", cascade="all, delete-orphan", passive_deletes=True
    )
    symptoms: Mapped[list[Symptom]] = relationship(
        back_populates="daily_entry", cascade="all, delete-orphan", passive_deletes=True
    )


class Training(ProvenanceMixin, Base):
    __tablename__ = "training"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    athlete_id: Mapped[int] = mapped_column(
        ForeignKey("athlete.id", ondelete="CASCADE"), nullable=False, index=True
    )
    daily_entry_id: Mapped[int] = mapped_column(
        ForeignKey("daily_entry.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)

    mileage: Mapped[float | None] = mapped_column(Float, nullable=True)
    intensity_1_to_10: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Derived from intensity via the step function in spec.md section 5.3.
    # Nullable because it is computed, and because intensity itself is optional.
    intensity_factor: Mapped[float | None] = mapped_column(Float, nullable=True)
    elevation_gain_ft: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(40), nullable=True)

    daily_entry: Mapped[DailyEntry] = relationship(back_populates="training_sessions")


class Sleep(ProvenanceMixin, Base):
    __tablename__ = "sleep"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    athlete_id: Mapped[int] = mapped_column(
        ForeignKey("athlete.id", ondelete="CASCADE"), nullable=False, index=True
    )
    daily_entry_id: Mapped[int] = mapped_column(
        ForeignKey("daily_entry.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)

    hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_1_to_10: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Local wall-clock times, not timestamps. Bedtime of 23:40 and wake of 06:15
    # are the same night; the crossing of midnight is implied, not stored.
    bedtime: Mapped[dt.time | None] = mapped_column(Time, nullable=True)
    wake_time: Mapped[dt.time | None] = mapped_column(Time, nullable=True)
    source: Mapped[str | None] = mapped_column(String(40), nullable=True)

    daily_entry: Mapped[DailyEntry] = relationship(back_populates="sleep_records")


class Nutrition(ProvenanceMixin, Base):
    __tablename__ = "nutrition"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    athlete_id: Mapped[int] = mapped_column(
        ForeignKey("athlete.id", ondelete="CASCADE"), nullable=False, index=True
    )
    daily_entry_id: Mapped[int] = mapped_column(
        ForeignKey("daily_entry.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)

    protein_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbs_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    calories: Mapped[float | None] = mapped_column(Float, nullable=True)

    # The phase and load in force on that date, recorded alongside the intake so
    # the taper adjustment in spec.md section 5.2 can be reproduced later even if
    # the profile's current phase has since moved on.
    training_phase: Mapped[str | None] = mapped_column(String(30), nullable=True)
    training_load: Mapped[float | None] = mapped_column(Float, nullable=True)

    meals: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    source: Mapped[str | None] = mapped_column(String(40), nullable=True)

    daily_entry: Mapped[DailyEntry] = relationship(back_populates="nutrition_records")


class RecoveryMethod(ProvenanceMixin, Base):
    """A recovery action taken on a day.

    A row with `method_type = 'none'` means the athlete opened the recovery section
    and recorded doing nothing. No row at all means the section was never opened.
    These are different facts and the schema keeps them apart (spec.md section 4).
    """

    __tablename__ = "recovery_method"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    athlete_id: Mapped[int] = mapped_column(
        ForeignKey("athlete.id", ondelete="CASCADE"), nullable=False, index=True
    )
    daily_entry_id: Mapped[int] = mapped_column(
        ForeignKey("daily_entry.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)

    # RecoveryMethodType, including the member 'none'.
    method_type: Mapped[str] = mapped_column(String(40), nullable=False)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    intensity_1_to_10: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Local wall-clock time of day the method was applied.
    applied_at: Mapped[dt.time | None] = mapped_column(Time, nullable=True)

    # Optional: the symptom this was aimed at. Deleting the symptom does not delete
    # the recovery session, it just unlinks it.
    symptom_id: Mapped[int | None] = mapped_column(
        ForeignKey("symptom.id", ondelete="SET NULL"), nullable=True, index=True
    )

    daily_entry: Mapped[DailyEntry] = relationship(back_populates="recovery_methods")
    symptom: Mapped[Symptom | None] = relationship(back_populates="recovery_methods")
