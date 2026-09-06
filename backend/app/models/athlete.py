"""The athlete and their profile.

`athlete_id` is on every table in the schema, but nothing else in this project
generalises to more than one athlete. See CLAUDE.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin

if TYPE_CHECKING:
    from app.models.daily import DailyEntry


class Athlete(CreatedAtMixin, Base):
    __tablename__ = "athlete"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sport: Mapped[str | None] = mapped_column(String(60), nullable=True)
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )

    profile: Mapped[AthleteProfile | None] = relationship(
        back_populates="athlete",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    daily_entries: Mapped[list[DailyEntry]] = relationship(
        back_populates="athlete",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class AthleteProfile(CreatedAtMixin, Base):
    """One current profile per athlete. Not a history of snapshots.

    The nutrition baselines are auto-calculated (spec.md section 2) rather than
    asked for, per the observation-over-estimation rule in CLAUDE.md.
    """

    __tablename__ = "athlete_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    athlete_id: Mapped[int] = mapped_column(
        ForeignKey("athlete.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Body metrics.
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(30), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Mileage is in miles, matching the worked examples in spec.md section 5.3.
    current_weekly_mileage: Mapped[float | None] = mapped_column(Float, nullable=True)
    peak_weekly_mileage: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_training_phase: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Auto-calculated nutrition baselines, in grams (calories in kcal).
    baseline_protein_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    baseline_carbs_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    baseline_fat_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    baseline_calories: Mapped[float | None] = mapped_column(Float, nullable=True)

    baseline_sleep_hours: Mapped[float | None] = mapped_column(Float, nullable=True)

    injury_history: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    preferred_recovery_methods: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    stress_response_profile: Mapped[Any | None] = mapped_column(JSON, nullable=True)

    athlete: Mapped[Athlete] = relationship(back_populates="profile")
