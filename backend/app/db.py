"""Engine and session setup.

SQLite does not enforce foreign keys unless told to per-connection. Call
`enable_sqlite_foreign_keys(engine)` on any SQLite engine before using it,
including the separate in-memory engines the tests construct.
"""

from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker


def enable_sqlite_foreign_keys(target_engine: Engine) -> None:
    @event.listens_for(target_engine, "connect")
    def _on_connect(dbapi_connection, connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./athlete_tracker.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
enable_sqlite_foreign_keys(engine)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
