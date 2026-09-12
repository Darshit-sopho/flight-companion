"""Small pure-function helpers shared across the services layer. Kept dependency-free (no DB/HTTP) so
they're trivially unit-testable.
"""

from __future__ import annotations

from datetime import datetime

from app.db.models import FlightStatus

_ON_TIME_THRESHOLD_MINUTES = 15

_STATUS_MAP = {
    "scheduled": FlightStatus.SCHEDULED,
    "en route": FlightStatus.ACTIVE,
    "active": FlightStatus.ACTIVE,
    "arrived": FlightStatus.LANDED,
    "landed": FlightStatus.LANDED,
    "cancelled": FlightStatus.CANCELLED,
    "canceled": FlightStatus.CANCELLED,
    "diverted": FlightStatus.DIVERTED,
}


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def map_status(raw_status: str | None) -> FlightStatus:
    if not raw_status:
        return FlightStatus.SCHEDULED
    return _STATUS_MAP.get(raw_status.strip().lower(), FlightStatus.SCHEDULED)


def compute_delay_minutes(scheduled: datetime | None, actual_or_estimated: datetime | None) -> int | None:
    if scheduled is None or actual_or_estimated is None:
        return None
    delta = actual_or_estimated - scheduled
    return round(delta.total_seconds() / 60)


def is_on_time(delay_minutes: int | None) -> bool | None:
    if delay_minutes is None:
        return None
    return delay_minutes <= _ON_TIME_THRESHOLD_MINUTES


def meters_to_feet(meters: float | None) -> float | None:
    return round(meters * 3.28084, 1) if meters is not None else None


def ms_to_knots(meters_per_second: float | None) -> float | None:
    return round(meters_per_second * 1.94384, 1) if meters_per_second is not None else None
