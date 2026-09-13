"""Independent short-TTL cache + lookup for airport weather (docs/features/status-card-requirements.md
#SC-D2). Deliberately separate from flight_status_service's AeroAPI-gated caching (see #SC-X4) — this is
airport+time data from a free API with its own freshness policy, not derived from a flight's status.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.clients.openmeteo_client import OpenMeteoClient
from app.config import get_settings
from app.core.cache import ttl_from_now
from app.core.time import ensure_aware, utcnow
from app.db.models import Airport, AirportWeatherSnapshot
from app.schemas.weather import AirportWeatherResponse, WeatherGlyph
from app.services.wmo_weather_codes import bucket_for_wmo_code

# Beyond this, the nearest cached hourly entry is too far from the requested time to show as a
# meaningful "outlook" (e.g. a flight booked far enough out that it's past Open-Meteo's forecast
# horizon) — better to show nothing than a misleadingly stale match.
_MAX_OUTLOOK_GAP = timedelta(hours=3)


def _parse_open_meteo_time(value: str | None) -> datetime | None:
    """Open-Meteo timestamps come back as naive-looking ISO strings when `timezone=UTC` is requested
    (no offset suffix) — they ARE UTC, just not marked as such; attach tzinfo explicitly.
    """
    if not value:
        return None
    return datetime.fromisoformat(value).replace(tzinfo=UTC)


def get_airport_weather(
    db: Session, openmeteo: OpenMeteoClient, airport: Airport, at: datetime | None = None
) -> AirportWeatherResponse | None:
    """`at` is the local flight-relevant time to find the nearest outlook hour for (a leg's scheduled/
    estimated departure or arrival) — defaults to now if not given. Returns None if the airport has no
    known coordinates (can't call Open-Meteo without lat/lon).
    """
    if airport.lat is None or airport.lon is None:
        return None

    target = at or utcnow()
    snapshot = db.get(AirportWeatherSnapshot, airport.code)

    if snapshot is None or ensure_aware(snapshot.expires_at) <= utcnow():
        forecast = openmeteo.get_forecast(airport.lat, airport.lon)
        ttl = get_settings().airport_weather_cache_ttl_seconds
        current = forecast["current"]

        if snapshot is None:
            snapshot = AirportWeatherSnapshot(airport_code=airport.code)
            db.add(snapshot)

        snapshot.current_weather_code = current["weather_code"]
        snapshot.current_temp_f = current["temp_f"]
        snapshot.current_observed_at = _parse_open_meteo_time(current["time"])
        snapshot.hourly_forecast = forecast["hourly"]
        snapshot.fetched_at = utcnow()
        snapshot.expires_at = ttl_from_now(ttl)
        db.commit()
        db.refresh(snapshot)

    now_glyph = WeatherGlyph(
        bucket=bucket_for_wmo_code(snapshot.current_weather_code),
        temp_f=snapshot.current_temp_f,
        at=ensure_aware(snapshot.current_observed_at) if snapshot.current_observed_at else utcnow(),
    )
    outlook_glyph = _nearest_hour_glyph(snapshot.hourly_forecast, target)

    return AirportWeatherResponse(code=airport.code, now=now_glyph, outlook=outlook_glyph)


def _nearest_hour_glyph(hourly_forecast: list, target: datetime) -> WeatherGlyph | None:
    target = ensure_aware(target)
    best_entry = None
    best_gap = None
    for entry in hourly_forecast:
        entry_time = _parse_open_meteo_time(entry.get("time"))
        if entry_time is None:
            continue
        gap = abs(entry_time - target)
        if best_gap is None or gap < best_gap:
            best_entry, best_gap = entry, gap

    if best_entry is None or best_gap is None or best_gap > _MAX_OUTLOOK_GAP:
        return None
    return WeatherGlyph(
        bucket=bucket_for_wmo_code(best_entry.get("weather_code")),
        temp_f=best_entry.get("temp_f"),
        at=_parse_open_meteo_time(best_entry.get("time")),
    )
