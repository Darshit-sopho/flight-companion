"""Shared pytest fixtures. See docs/TESTING.md for the overall test strategy.

`sqlite_session` — fast, in-memory, no external dependency. Used by unit tests (tests/unit/) that need a
real DB session (e.g. icao24_resolver's registry lookup) but shouldn't require Postgres to be running.

`db_session` — a real Postgres session against TEST_DATABASE_URL (defaults to the same local dev
database docker-compose provisions). Used by integration tests (tests/integration/) to exercise the
actual router/service/DB wiring. Requires `docker compose up -d db` and the schema migrated
(`alembic upgrade head`) — see ../README.md. Each test gets a clean slate via row deletion at teardown,
NOT a dropped/recreated schema — dropping tables here would fight with Alembic's migrations on a shared
dev database. Point TEST_DATABASE_URL at a separate database if you'd rather not share with dev data.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import models  # noqa: F401 — registers all models on Base.metadata
from app.db.base import Base

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://flightcompanion:flightcompanion@localhost:5432/flightcompanion",
)


@pytest.fixture()
def sqlite_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def db_session():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine, checkfirst=True)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        with engine.begin() as connection:
            for table in reversed(Base.metadata.sorted_tables):
                connection.execute(table.delete())
        engine.dispose()
