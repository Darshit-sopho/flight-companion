"""Serves live position data for a flight, exclusively from OpenSky. Owns: the airborne/not-airborne/
landed state machine, throttling actual upstream OpenSky calls independent of frontend polling cadence,
and delegating icao24 resolution to icao24_resolver. See docs/ARCHITECTURE.md#request-flow.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.clients.opensky_client import OpenSkyClient
from app.config import get_settings
from app.core.time import ensure_aware, utcnow
from app.db.models import FlightSnapshot, FlightStatus, LivePosition, TrackedFlight
from app.services.icao24_resolver import resolve_icao24
from app.services.utils import meters_to_feet, ms_to_knots

_NOT_YET_AIRBORNE_STATUSES = {FlightStatus.SCHEDULED}
_ENDED_STATUSES = {FlightStatus.LANDED, FlightStatus.CANCELLED, FlightStatus.DIVERTED}


def get_live_track(db: Session, opensky: OpenSkyClient, flight_id: str) -> dict:
    snapshot = db.get(FlightSnapshot, flight_id)
    if snapshot is None:
        return _response("unavailable")

    if snapshot.status in _NOT_YET_AIRBORNE_STATUSES:
        return _response("not_airborne")
    if snapshot.status in _ENDED_STATUSES:
        return _response("landed")

    tracked = db.get(TrackedFlight, flight_id)
    if tracked is None:
        tracked = TrackedFlight(flight_id=flight_id)
        db.add(tracked)
        db.flush()

    if tracked.resolved_icao24 is None:
        # Codeshares broadcast the OPERATING carrier's ICAO ident over ADS-B (e.g. "RPA3513"), not
        # necessarily the marketing ident the user searched (e.g. "UA3513") — try both. See
        # docs/ARCHITECTURE.md#aeroapi--opensky-linking.
        candidate_idents = [snapshot.ident]
        if snapshot.operating_ident_icao and snapshot.operating_ident_icao != snapshot.ident:
            candidate_idents.append(snapshot.operating_ident_icao)
        result = resolve_icao24(
            db,
            registration=snapshot.registration,
            candidate_idents=candidate_idents,
            opensky_client=opensky,
        )
        tracked.resolved_icao24 = result.icao24
        tracked.resolution_method = result.method.value
        tracked.resolution_confidence = result.confidence.value
        db.commit()

    if tracked.resolved_icao24 is None:
        return _response("unavailable", resolution=tracked)

    settings = get_settings()
    now = utcnow()
    min_interval = settings.opensky_min_poll_interval_seconds
    if tracked.last_polled_at and (now - ensure_aware(tracked.last_polled_at)).total_seconds() < min_interval:
        cached_position = _latest_position(db, flight_id)
        if cached_position is None:
            return _response("unavailable", resolution=tracked)
        return _response("tracking", position=cached_position, resolution=tracked)

    state = opensky.get_states(tracked.resolved_icao24)
    tracked.last_polled_at = now
    db.commit()

    if state is None:
        return _response("unavailable", resolution=tracked)

    position = LivePosition(
        flight_id=flight_id,
        recorded_at=now,
        lat=state["latitude"],
        lon=state["longitude"],
        altitude_ft=meters_to_feet(state.get("baro_altitude")),
        ground_speed_kt=ms_to_knots(state.get("velocity")),
        heading_deg=state.get("true_track"),
        on_ground=bool(state.get("on_ground")),
        source="opensky",
    )
    db.add(position)
    db.commit()
    return _response("tracking", position=position, resolution=tracked)


def _latest_position(db: Session, flight_id: str) -> LivePosition | None:
    return (
        db.query(LivePosition)
        .filter(LivePosition.flight_id == flight_id)
        .order_by(LivePosition.recorded_at.desc())
        .first()
    )


def _response(
    state: str, *, position: LivePosition | None = None, resolution: TrackedFlight | None = None
) -> dict:
    return {
        "state": state,
        "position": None
        if position is None
        else {
            "lat": position.lat,
            "lon": position.lon,
            "altitude_ft": position.altitude_ft,
            "ground_speed_kt": position.ground_speed_kt,
            "heading_deg": position.heading_deg,
            "on_ground": position.on_ground,
            "recorded_at": position.recorded_at.isoformat() + "Z",
        },
        "resolution": None
        if resolution is None
        else {
            "method": resolution.resolution_method,
            "confidence": resolution.resolution_confidence,
        },
    }
