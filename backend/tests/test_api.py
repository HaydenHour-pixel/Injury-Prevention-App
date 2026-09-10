"""Slice 1b tests: the HTTP API over the slice 1a schema.

Covers: get-or-create daily_entry semantics, the day payload's absent-vs-none
distinction (spec.md section 4), date validation, provenance population on
write and on PATCH, and transactional rollback of a failed section insert.
"""

from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

from app.config import ATHLETE_TIMEZONE
from app.models import Athlete, DailyEntry, Symptom

TZ = ZoneInfo(ATHLETE_TIMEZONE)


def today() -> dt.date:
    return dt.datetime.now(TZ).date()


def test_post_section_with_no_daily_entry_creates_exactly_one(client, test_db):
    date = today()
    resp = client.post(f"/api/days/{date}/training", json={"mileage": 5.0})
    assert resp.status_code == 201

    db = test_db()
    entries = db.query(DailyEntry).filter_by(date=date).all()
    db.close()
    assert len(entries) == 1


def test_two_sections_same_date_share_one_daily_entry(client, test_db):
    date = today()
    r1 = client.post(f"/api/days/{date}/training", json={"mileage": 5.0})
    r2 = client.post(f"/api/days/{date}/sleep", json={"hours": 7.0})
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["daily_entry_id"] == r2.json()["daily_entry_id"]

    db = test_db()
    entries = db.query(DailyEntry).filter_by(date=date).all()
    db.close()
    assert len(entries) == 1


def test_get_day_with_no_data_returns_empty_shell_200(client):
    resp = client.get("/api/days/2020-01-01")
    assert resp.status_code == 200
    body = resp.json()

    assert body["daily_entry_exists"] is False
    assert body["training"] == []
    assert body["sleep"] == []
    assert body["nutrition"] is None
    assert body["recovery"] == []
    assert body["symptoms"] == []
    assert body["completeness"] == {
        "training": False,
        "sleep": False,
        "nutrition": False,
        "recovery": False,
        "symptoms": False,
    }


def test_get_day_distinguishes_no_recovery_rows_vs_method_type_none(client):
    date_logged_none = today()
    date_never_opened = today() - dt.timedelta(days=1)

    resp = client.post(
        f"/api/days/{date_logged_none}/recovery", json={"method_type": "none"}
    )
    assert resp.status_code == 201

    logged_day = client.get(f"/api/days/{date_logged_none}").json()
    never_opened_day = client.get(f"/api/days/{date_never_opened}").json()

    assert len(logged_day["recovery"]) == 1
    assert logged_day["recovery"][0]["method_type"] == "none"
    assert logged_day["completeness"]["recovery"] is True

    assert never_opened_day["recovery"] == []
    assert never_opened_day["completeness"]["recovery"] is False


def test_completeness_false_for_unlogged_true_for_logged(client):
    date = today()
    client.post(f"/api/days/{date}/training", json={"mileage": 3.0})

    body = client.get(f"/api/days/{date}").json()
    assert body["completeness"]["training"] is True
    assert body["completeness"]["sleep"] is False
    assert body["completeness"]["nutrition"] is False
    assert body["completeness"]["recovery"] is False
    assert body["completeness"]["symptoms"] is False


def test_future_date_beyond_plus_one_rejected(client):
    too_far = today() + dt.timedelta(days=2)
    resp = client.post(f"/api/days/{too_far}/training", json={"mileage": 5.0})
    assert resp.status_code == 422


def test_date_one_day_future_is_allowed(client):
    tomorrow = today() + dt.timedelta(days=1)
    resp = client.post(f"/api/days/{tomorrow}/training", json={"mileage": 5.0})
    assert resp.status_code == 201


def test_backdated_symptom_gets_lower_recall_confidence_than_same_day(client):
    same_day = client.post(
        f"/api/days/{today()}/symptoms",
        json={"body_location": "left knee", "intensity_1_to_10": 4, "type": "dull_ache"},
    ).json()
    backdated = client.post(
        f"/api/days/{today() - dt.timedelta(days=5)}/symptoms",
        json={"body_location": "left knee", "intensity_1_to_10": 4, "type": "dull_ache"},
    ).json()

    assert same_day["recall_confidence"] == 1.0
    assert backdated["recall_confidence"] == 0.4
    assert backdated["recall_confidence"] < same_day["recall_confidence"]


def test_sleep_quality_logged_next_morning_gets_recall_confidence_1(client):
    last_night = today() - dt.timedelta(days=1)
    resp = client.post(
        f"/api/days/{last_night}/sleep",
        json={"hours": 7.5, "quality_1_to_10": 8},
    )
    assert resp.status_code == 201
    assert resp.json()["recall_confidence"] == 1.0


def test_failed_section_insert_rolls_back_daily_entry_creation(client, test_db):
    date = today() - dt.timedelta(days=30)  # a date touched by no other test

    resp = client.post(
        f"/api/days/{date}/symptoms",
        json={
            "body_location": "left knee",
            "intensity_1_to_10": 4,
            "type": "dull_ache",
            "pain_profile_id": 999999,  # does not exist -> FK violation
        },
    )
    assert resp.status_code == 400

    db = test_db()
    assert db.query(DailyEntry).filter_by(date=date).first() is None
    assert db.query(Symptom).filter_by(date=date).first() is None
    db.close()


def test_patch_recomputes_recall_confidence(client, test_db):
    old_date = today() - dt.timedelta(days=10)

    db = test_db()
    athlete = db.query(Athlete).first()
    row = Symptom(
        athlete_id=athlete.id,
        daily_entry_id=None,
        date=old_date,
        body_location="left knee",
        intensity_1_to_10=4,
        type="dull_ache",
        source_confidence=0.9,
        recall_confidence=1.0,  # as if originally logged same-day
    )
    db.add(row)
    db.commit()
    symptom_id = row.id
    db.close()

    resp = client.patch(f"/api/symptoms/{symptom_id}", json={"description": "still there"})
    assert resp.status_code == 200
    # Restated 10 days later: symptom-intensity curve caps at 0.4 beyond +1d.
    assert resp.json()["recall_confidence"] == 0.4
