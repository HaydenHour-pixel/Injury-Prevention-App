from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import enable_sqlite_foreign_keys, get_db
from app.main import app
from app.models import Athlete, Base


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


@pytest.fixture()
def test_db():
    """A sessionmaker bound to a fresh in-memory DB, for API tests that need to
    both drive requests through `client` and make verification queries directly
    (e.g. "exactly one daily_entry exists").

    StaticPool is required here, unlike the `session` fixture above: TestClient
    runs the app in a worker thread, and a plain `:memory:` engine hands each
    thread its own private, empty database (SQLAlchemy's default pooling for
    SQLite is thread-local). StaticPool keeps everyone on the one connection
    that actually has the schema on it.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    enable_sqlite_foreign_keys(engine)
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    yield SessionLocal
    engine.dispose()


@pytest.fixture()
def client(test_db):
    db = test_db()
    db.add(Athlete(name="Hayden"))
    db.commit()
    db.close()

    def override_get_db():
        db = test_db()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
