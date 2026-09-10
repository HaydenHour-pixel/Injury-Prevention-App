"""Data provenance: source confidence and recall-decay confidence.

Pure functions, no DB access, no I/O, no clock reads (spec.md section 3).
Callers pass in whatever moment they mean by "when this was actually written":
`datetime.now(UTC)` for a fresh write, and the same at PATCH time, since
restating a value takes on the recall lag of the moment it is restated, not
the lag of when the row first appeared.
"""

from __future__ import annotations

import datetime as dt
from enum import StrEnum
from zoneinfo import ZoneInfo

from app.models.enums import DataSource


class FieldGroup(StrEnum):
    """Which recall-decay curve applies to a field (spec.md section 3).

    OBJECTIVE fields (mileage, elevation, bedtime, wake time) don't decay: a
    number is either recorded or it isn't, there's no memory of *how it felt*
    to fade. The other groups are self-report and decay with reporting lag,
    each against its own natural reporting window.
    """

    OBJECTIVE = "objective"
    SUBJECTIVE_EFFORT = "subjective_effort"
    SLEEP_QUALITY = "sleep_quality"
    SYMPTOM_INTENSITY = "symptom_intensity"
    BODY_SENTIMENT = "body_sentiment"


_SOURCE_CONFIDENCE: dict[str, float] = {
    DataSource.STRAVA.value: 1.0,
    DataSource.MANUAL.value: 0.9,
    DataSource.UMASS_DINING_MENU.value: 0.7,
    DataSource.MANUAL_FOOD_ENTRY.value: 0.6,
}


def source_confidence(source: str) -> float:
    """Trust in the data source itself (spec.md section 3), independent of when
    it was reported. An unrecognized source is a caller bug, not a data
    condition, so this fails loudly rather than guessing a value.
    """
    try:
        return _SOURCE_CONFIDENCE[source]
    except KeyError:
        raise ValueError(f"unknown data source: {source!r}") from None


def _local_lag_days(entry_date: dt.date, created_at: dt.datetime, athlete_tz: str) -> int:
    """Calendar-day lag between the date being described and the date the row
    was actually written, in the athlete's local time.

    `created_at` is a UTC instant; converting it to local time before taking
    its calendar date matters because "the following morning" is a
    local-calendar concept, not a UTC one — the same instant can fall on
    different local dates depending on the athlete's timezone.
    """
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=dt.timezone.utc)
    local_written_date = created_at.astimezone(ZoneInfo(athlete_tz)).date()
    # Negative lag (writing "for" a date before the row was written, i.e. a
    # future date) isn't a real lag; clamp rather than return a confidence
    # above the scale.
    return max(0, (local_written_date - entry_date).days)


def recall_confidence(
    field_group: str,
    entry_date: dt.date,
    created_at: dt.datetime,
    athlete_tz: str,
) -> float:
    """Trust given reporting lag (spec.md section 3).

    Lag is measured against the field's natural reporting window, not against
    a flat day count from `entry_date`: sleep quality entered the following
    morning is zero lag, not one day of lag, because "the following morning"
    is inside sleep quality's natural window. Symptom intensity and body
    sentiment share the same window and curve.
    """
    if field_group == FieldGroup.OBJECTIVE:
        return 1.0

    lag = _local_lag_days(entry_date, created_at, athlete_tz)

    if field_group == FieldGroup.SUBJECTIVE_EFFORT:
        # Natural window: same day.
        if lag == 0:
            return 1.0
        if lag == 1:
            return 0.85
        if lag == 2:
            return 0.6
        return 0.4

    if field_group == FieldGroup.SLEEP_QUALITY:
        # Natural window: through the next morning, i.e. one day later than
        # subjective effort's. The decay curve past the window is otherwise
        # the same shape, just shifted by that extra day.
        if lag <= 1:
            return 1.0
        if lag == 2:
            return 0.85
        if lag == 3:
            return 0.6
        return 0.4

    if field_group in (FieldGroup.SYMPTOM_INTENSITY, FieldGroup.BODY_SENTIMENT):
        # Natural window: same day. Only three steps, not four — spec.md's
        # table has no "+2d" entry for this group.
        if lag == 0:
            return 1.0
        if lag == 1:
            return 0.7
        return 0.4

    raise ValueError(f"unknown field group: {field_group!r}")
