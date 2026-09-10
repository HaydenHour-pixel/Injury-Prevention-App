"""Symptoms, the pain episodes they belong to, and per-location aggregates.

A `symptom` is a single day's report. A `pain_profile` is one episode spanning
onset to resolution, made up of one or more symptom rows. A
`body_part_vulnerability` row aggregates across episodes at one location.
"""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    Date,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, ProvenanceMixin

if TYPE_CHECKING:
    from app.models.daily import DailyEntry, RecoveryMethod


class PainProfile(Base):
    """One pain episode, from onset to resolution, at one body location."""

    __tablename__ = "pain_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    athlete_id: Mapped[int] = mapped_column(
        ForeignKey("athlete.id", ondelete="CASCADE"), nullable=False, index=True
    )

    body_location: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    onset_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    resolution_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_intensity_1_to_10: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Ordered list of PainType values observed across the episode, e.g.
    # ["muscle_soreness", "dull_ache", "dull_ache"].
    type_progression: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    concurrent_conditions: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    contributing_factors: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    effective_recovery_methods: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    # This athlete's Nth episode at this location, for the recurrence check in
    # spec.md section 6 ("same location, 2+ episodes").
    episode_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Default cascade (no delete-orphan): removing a symptom from this list, or
    # deleting the profile, unlinks the symptom rather than destroying them.
    # Regrouping symptoms between episodes is an expected operation, and symptom
    # rows are calibration labels (spec.md section 10) — the least replaceable
    # data in the app. The FK itself is ondelete="SET NULL"; this must agree with
    # it rather than escalate a NULL-out into a delete at the ORM level.
    symptoms: Mapped[list[Symptom]] = relationship(
        back_populates="pain_profile", passive_deletes=True
    )


class Symptom(ProvenanceMixin, Base):
    """A single day's symptom report. `intensity_1_to_10` and `type` are
    independent fields; a 7/10 muscle soreness and a 7/10 sharp pain are different
    events (spec.md section 5.5).
    """

    __tablename__ = "symptom"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    athlete_id: Mapped[int] = mapped_column(
        ForeignKey("athlete.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Nullable, ondelete="SET NULL": a symptom must survive its daily_entry being
    # deleted. athlete_id and date are sufficient identity on their own, and
    # symptom rows are the calibration labels in spec.md section 10 — the least
    # replaceable data in the app.
    daily_entry_id: Mapped[int | None] = mapped_column(
        ForeignKey("daily_entry.id", ondelete="SET NULL"), nullable=True, index=True
    )
    date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)

    body_location: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    intensity_1_to_10: Mapped[int] = mapped_column(Integer, nullable=False)
    # PainType.
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    # PainOnset.
    onset: Mapped[str | None] = mapped_column(String(20), nullable=True)
    limiting: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    pain_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("pain_profile.id", ondelete="SET NULL"), nullable=True, index=True
    )

    daily_entry: Mapped[DailyEntry | None] = relationship(back_populates="symptoms")
    pain_profile: Mapped[PainProfile | None] = relationship(back_populates="symptoms")
    recovery_methods: Mapped[list[RecoveryMethod]] = relationship(back_populates="symptom")


class BodyPartVulnerability(Base):
    """Aggregate per body location, recomputed from `pain_profile` history.

    Not a heatmap or any UI concept — CLAUDE.md rules out the vulnerability
    heatmap visualisation for MVP. This is only the numeric aggregate that feeds
    the location multiplier in spec.md section 5.5.
    """

    __tablename__ = "body_part_vulnerability"
    __table_args__ = (
        UniqueConstraint(
            "athlete_id", "body_location", name="uq_body_part_vulnerability_athlete_location"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    athlete_id: Mapped[int] = mapped_column(
        ForeignKey("athlete.id", ondelete="CASCADE"), nullable=False, index=True
    )
    body_location: Mapped[str] = mapped_column(String(60), nullable=False)

    episode_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # RecurrenceRisk.
    recurrence_risk: Mapped[str | None] = mapped_column(String(20), nullable=True)
    average_duration_days: Mapped[float | None] = mapped_column(Float, nullable=True)
    common_triggers: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    effective_methods: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    days_since_last_episode: Mapped[int | None] = mapped_column(Integer, nullable=True)
