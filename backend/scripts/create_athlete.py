"""One-off: create the sole athlete row this app needs to run at all.

get_current_athlete() (app/api/deps.py) 404s on every endpoint until this row
exists. Unlike seed_dev.py — which also inserts three days of fake
training/sleep/nutrition/recovery data for local testing — this only creates
the athlete. Safe to re-run: does nothing if an athlete already exists.

Usage:
    python scripts/create_athlete.py "Hayden"
    python scripts/create_athlete.py            # defaults to "Hayden"
"""

from __future__ import annotations

import sys

from app.db import SessionLocal
from app.models import Athlete


def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else "Hayden"

    session = SessionLocal()
    try:
        existing = session.query(Athlete).first()
        if existing is not None:
            print(f"Athlete already exists: id={existing.id}, name={existing.name!r}")
            return

        athlete = Athlete(name=name)
        session.add(athlete)
        session.commit()
        print(f"Created athlete: id={athlete.id}, name={athlete.name!r}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
