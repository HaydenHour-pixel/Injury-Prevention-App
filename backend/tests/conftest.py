from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import enable_sqlite_foreign_keys
from app.models import Base


@pytest.fixture()
def session():
    # StaticPool would share one connection across the whole engine, which is
    # the usual trick for in-memory SQLite; here a single connect() per test is
    # enough since everything in a test happens on one Session/one connection.
    engine = create_engine("sqlite:///:memory:")
    enable_sqlite_foreign_keys(engine)
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()
