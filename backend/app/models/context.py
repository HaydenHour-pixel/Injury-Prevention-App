"""Context tables: recurring lifestyle commitments and ad-hoc stress events.

Both feed the context interpretation in spec.md section 6 — the distinction
between a metric that is worse than normal and one that is worse than this
athlete's own established pattern for a similar stressor.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import Date, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin


class LifestyleCommitment(CreatedAtMixin, Base):
    """A recurring class or work commitment, e.g. "organic chem, MWF 9-10am,
    fall term". Not a one-off — see `StressEvent` for ad-hoc stressors.
    """

    __tablename__ = "lifestyle_commitment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    athlete_id: Mapped[int] = mapped_column(
        ForeignKey("athlete.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # CommitmentType.
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    # Day-of-week names, e.g. ["monday", "wednesday", "friday"].
    days_of_week: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    start_time: Mapped[dt.time | None] = mapped_column(nullable=True)
    end_time: Mapped[dt.time | None] = mapped_column(nullable=True)
    workload_intensity_1_to_10: Mapped[int | None] = mapped_column(Integer, nullable=True)

    term_start_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    term_end_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)


class StressEvent(CreatedAtMixin, Base):
    """An ad-hoc stressor with a concrete date range, e.g. finals week or a move.

    `expected_intensity_1_to_10` is the athlete's own estimate going in; it is not
    derived from logged data because it describes an event still ahead, which is
    exactly what section 6's "known stress period" context adjustment needs.
    """

    __tablename__ = "stress_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    athlete_id: Mapped[int] = mapped_column(
        ForeignKey("athlete.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # StressEventType.
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    start_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    expected_intensity_1_to_10: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resolution: Mapped[str | None] = mapped_column(String(255), nullable=True)
