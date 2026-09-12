"""Tiny shared helpers for the Postgres-row-as-cache pattern used throughout services/.

There's no separate cache layer (Redis etc.) for this project — cache state lives directly on the
relevant table's fetched_at/expires_at columns, checked here before a service decides whether to hit
AeroAPI. See docs/DATA_SOURCES.md#cost-control for the TTL policy per data type.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from app.core.time import utcnow


def is_expired(expires_at: datetime | None, *, now: datetime | None = None) -> bool:
    if expires_at is None:
        return True
    return (now or utcnow()) >= expires_at


def ttl_from_now(seconds: int, *, now: datetime | None = None) -> datetime:
    return (now or utcnow()) + timedelta(seconds=seconds)
