"""Past-occurrence history + trend aggregation for a flight number. Cached long-term since historical
on-time stats change slowly — see docs/DATA_SOURCES.md#cost-control.
"""

from __future__ import annotations

from datetime import date as date_cls
from datetime import timedelta
from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.aeroapi_client import AeroAPIClient
from app.config import get_settings
from app.core.time import utcnow
from app.db.models import FlightHistoryRecord
from app.services.utils import compute_delay_minutes, is_on_time, parse_dt

# A meaningful trend needs enough data points on each side of the split; below this, call it "stable".
_MIN_RECORDS_FOR_TREND = 4
_TREND_DELTA_MINUTES = 5


def get_history(db: Session, aeroapi: AeroAPIClient, ident: str, limit: int = 10) -> dict:
    records = _get_cached_or_fetch(db, aeroapi, ident, limit)
    return _aggregate(records)


def _get_cached_or_fetch(
    db: Session, aeroapi: AeroAPIClient, ident: str, limit: int
) -> list[FlightHistoryRecord]:
    settings = get_settings()
    cutoff = utcnow() - timedelta(seconds=settings.aeroapi_history_cache_ttl_seconds)
    stmt = (
        select(FlightHistoryRecord)
        .where(FlightHistoryRecord.ident == ident.upper())
        .where(FlightHistoryRecord.fetched_at >= cutoff)
        .order_by(FlightHistoryRecord.flight_date.desc())
        .limit(limit)
    )
    cached = list(db.scalars(stmt).all())
    if len(cached) >= limit:
        return cached[:limit]

    raw_flights = aeroapi.get_flight_history(ident, limit=limit)
    records = [_upsert_history_record(db, ident, raw) for raw in raw_flights]
    db.commit()
    records.sort(key=lambda r: r.flight_date or date_cls.min, reverse=True)
    return records[:limit]


def _upsert_history_record(db: Session, ident: str, raw: dict) -> FlightHistoryRecord:
    scheduled_departure = parse_dt(raw.get("scheduled_out"))
    actual_departure = parse_dt(raw.get("actual_out"))
    flight_date = scheduled_departure.date() if scheduled_departure else None

    existing = None
    if flight_date is not None:
        existing = db.scalar(
            select(FlightHistoryRecord)
            .where(FlightHistoryRecord.ident == ident.upper())
            .where(FlightHistoryRecord.flight_date == flight_date)
        )

    record = existing or FlightHistoryRecord(ident=ident.upper(), flight_date=flight_date)
    record.route_origin = (raw.get("origin") or {}).get("code")
    record.route_destination = (raw.get("destination") or {}).get("code")
    record.scheduled_departure = scheduled_departure
    record.actual_departure = actual_departure
    record.delay_minutes = compute_delay_minutes(scheduled_departure, actual_departure)
    record.on_time = is_on_time(record.delay_minutes)
    record.fetched_at = utcnow()
    if existing is None:
        db.add(record)
    return record


def _aggregate(records: list[FlightHistoryRecord]) -> dict:
    if not records:
        return {
            "on_time_percentage": None,
            "average_delay_minutes": None,
            "trend": "stable",
            "occurrences": [],
        }

    delays = [r.delay_minutes for r in records if r.delay_minutes is not None]
    on_time_count = sum(1 for r in records if r.on_time)
    on_time_percentage = round(100 * on_time_count / len(records), 1)
    average_delay_minutes = round(mean(delays), 1) if delays else None

    trend = "stable"
    if len(delays) >= _MIN_RECORDS_FOR_TREND:
        midpoint = len(delays) // 2
        newer_half, older_half = delays[:midpoint], delays[midpoint:]
        diff = mean(newer_half) - mean(older_half)
        if diff < -_TREND_DELTA_MINUTES:
            trend = "improving"
        elif diff > _TREND_DELTA_MINUTES:
            trend = "worsening"

    occurrences = [
        {
            "date": r.flight_date.isoformat() if r.flight_date else None,
            "delay_minutes": r.delay_minutes,
            "on_time": r.on_time,
        }
        for r in records
    ]
    return {
        "on_time_percentage": on_time_percentage,
        "average_delay_minutes": average_delay_minutes,
        "trend": trend,
        "occurrences": occurrences,
    }
