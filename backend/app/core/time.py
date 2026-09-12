"""Single source of truth for "now" — timezone-aware UTC, since every DateTime column in this project is
declared `timezone=True`. Use this instead of the deprecated `datetime.utcnow()` everywhere in the app.
"""

from __future__ import annotations

from datetime import UTC, datetime


def utcnow() -> datetime:
    return datetime.now(UTC)


def ensure_aware(dt: datetime) -> datetime:
    """Coerce a naive datetime to UTC-aware.

    Postgres preserves tzinfo for `DateTime(timezone=True)` columns, but SQLite (used for the fast
    in-memory unit-test DB — see backend/tests/conftest.py) silently drops it on round-trip. Wrap any
    value read back from the DB in this before comparing/subtracting against `utcnow()`, so those
    comparisons work the same under both.
    """
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)
