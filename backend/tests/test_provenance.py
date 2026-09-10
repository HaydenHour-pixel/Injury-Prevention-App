"""Direct unit tests for app/provenance.py against spec.md section 3's worked
examples and both tables, independent of the API layer.
"""

from __future__ import annotations

import datetime as dt

import pytest

from app.provenance import FieldGroup, recall_confidence, source_confidence

TZ = "America/New_York"


def at(date: dt.date) -> dt.datetime:
    """A UTC instant that lands on `date` in TZ, regardless of DST.

    America/New_York is UTC-4 (EDT) or UTC-5 (EST); 17:00 UTC is 12:00-13:00
    local, comfortably clear of both calendar-date boundaries.
    """
    return dt.datetime(date.year, date.month, date.day, 17, tzinfo=dt.timezone.utc)


class TestSourceConfidence:
    def test_strava(self):
        assert source_confidence("strava") == 1.0

    def test_manual(self):
        assert source_confidence("manual") == 0.9

    def test_umass_dining_menu(self):
        assert source_confidence("umass_dining_menu") == 0.7

    def test_manual_food_entry(self):
        assert source_confidence("manual_food_entry") == 0.6

    def test_unknown_source_raises(self):
        with pytest.raises(ValueError):
            source_confidence("carrier_pigeon")


class TestObjective:
    def test_always_1_regardless_of_lag(self):
        monday = dt.date(2026, 9, 7)
        thursday_utc_instant = at(dt.date(2026, 9, 10))
        assert recall_confidence(FieldGroup.OBJECTIVE, monday, thursday_utc_instant, TZ) == 1.0


class TestSubjectiveEffort:
    def test_same_day(self):
        d = dt.date(2026, 9, 1)
        assert recall_confidence(FieldGroup.SUBJECTIVE_EFFORT, d, at(d), TZ) == 1.0

    def test_one_day_late(self):
        d = dt.date(2026, 9, 1)
        assert (
            recall_confidence(FieldGroup.SUBJECTIVE_EFFORT, d, at(d + dt.timedelta(days=1)), TZ)
            == 0.85
        )

    def test_two_days_late(self):
        d = dt.date(2026, 9, 1)
        assert (
            recall_confidence(FieldGroup.SUBJECTIVE_EFFORT, d, at(d + dt.timedelta(days=2)), TZ)
            == 0.6
        )

    def test_three_or_more_days_late(self):
        d = dt.date(2026, 9, 1)
        assert (
            recall_confidence(FieldGroup.SUBJECTIVE_EFFORT, d, at(d + dt.timedelta(days=3)), TZ)
            == 0.4
        )
        assert (
            recall_confidence(FieldGroup.SUBJECTIVE_EFFORT, d, at(d + dt.timedelta(days=10)), TZ)
            == 0.4
        )

    def test_monday_entered_thursday_is_three_days_of_lag(self):
        """spec.md section 3's own worked example."""
        monday = dt.date(2026, 9, 7)
        thursday = at(dt.date(2026, 9, 10))
        assert recall_confidence(FieldGroup.SUBJECTIVE_EFFORT, monday, thursday, TZ) == 0.4


class TestSleepQuality:
    def test_same_day_is_zero_lag(self):
        d = dt.date(2026, 9, 1)
        assert recall_confidence(FieldGroup.SLEEP_QUALITY, d, at(d), TZ) == 1.0

    def test_next_morning_is_zero_lag_not_one_day(self):
        """The spec's explicit example: entering sleep quality the following
        morning is zero lag, not one day of lag."""
        d = dt.date(2026, 9, 1)
        next_morning = at(d + dt.timedelta(days=1))
        assert recall_confidence(FieldGroup.SLEEP_QUALITY, d, next_morning, TZ) == 1.0

    def test_one_day_past_the_window(self):
        d = dt.date(2026, 9, 1)
        assert (
            recall_confidence(FieldGroup.SLEEP_QUALITY, d, at(d + dt.timedelta(days=2)), TZ)
            == 0.85
        )

    def test_two_days_past_the_window(self):
        d = dt.date(2026, 9, 1)
        assert (
            recall_confidence(FieldGroup.SLEEP_QUALITY, d, at(d + dt.timedelta(days=3)), TZ) == 0.6
        )

    def test_far_past_the_window(self):
        d = dt.date(2026, 9, 1)
        assert (
            recall_confidence(FieldGroup.SLEEP_QUALITY, d, at(d + dt.timedelta(days=4)), TZ) == 0.4
        )


class TestSymptomIntensityAndBodySentiment:
    @pytest.mark.parametrize("group", [FieldGroup.SYMPTOM_INTENSITY, FieldGroup.BODY_SENTIMENT])
    def test_same_day(self, group):
        d = dt.date(2026, 9, 1)
        assert recall_confidence(group, d, at(d), TZ) == 1.0

    @pytest.mark.parametrize("group", [FieldGroup.SYMPTOM_INTENSITY, FieldGroup.BODY_SENTIMENT])
    def test_one_day_late(self, group):
        d = dt.date(2026, 9, 1)
        assert recall_confidence(group, d, at(d + dt.timedelta(days=1)), TZ) == 0.7

    @pytest.mark.parametrize("group", [FieldGroup.SYMPTOM_INTENSITY, FieldGroup.BODY_SENTIMENT])
    def test_two_or_more_days_late(self, group):
        d = dt.date(2026, 9, 1)
        assert recall_confidence(group, d, at(d + dt.timedelta(days=2)), TZ) == 0.4
        assert recall_confidence(group, d, at(d + dt.timedelta(days=20)), TZ) == 0.4
