"""Shared base classes for response schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base for Read schemas: lets `.model_validate(orm_instance)` work directly
    against a SQLAlchemy row.
    """

    model_config = ConfigDict(from_attributes=True)
