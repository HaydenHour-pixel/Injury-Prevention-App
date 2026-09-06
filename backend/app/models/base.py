"""Declarative base and the mixins shared across model modules."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, Float, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Explicit constraint naming so Alembic can find constraints by name when it
# rewrites tables. SQLite has no ALTER for constraints; batch mode recreates the
# table, and it needs names to do that.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class CreatedAtMixin:
    """When the row was actually written, in UTC.

    This is a genuine event timestamp, not a calendar day. It is what the recall
    decay in spec.md section 3 is measured from. Do not derive any `date` column
    from it.
    """

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class ProvenanceMixin(CreatedAtMixin):
    """Provenance fields required on every logged table (spec.md section 3).

    Both confidence columns are nullable and stay NULL for now. They are populated
    in a later slice, from the source table and the recall-decay table in section 3.
    NULL means "not yet computed", which is not the same as 0.0 ("no trust").
    """

    source_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    recall_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
