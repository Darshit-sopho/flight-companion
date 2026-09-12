from datetime import datetime
from unittest.mock import MagicMock

from app.config import get_settings
from app.core.time import utcnow
from app.db.models import AircraftRegistry, FlightSnapshot, FlightStatus
from app.services import live_tracking_service


def _make_snapshot(**overrides) -> FlightSnapshot:
    defaults = dict(
        flight_id="UAL123-2026-09-12",
        ident="UAL123",
        scheduled_date=datetime(2026, 9, 12).date(),
        status=FlightStatus.ACTIVE,
        registration="N12345",
        fetched_at=utcnow(),
        expires_at=utcnow(),
    )
    defaults.update(overrides)
    return FlightSnapshot(**defaults)


def test_not_airborne_for_scheduled_flight(sqlite_session):
    snapshot = _make_snapshot(status=FlightStatus.SCHEDULED)
    sqlite_session.add(snapshot)
    sqlite_session.commit()

    result = live_tracking_service.get_live_track(sqlite_session, MagicMock(), snapshot.flight_id)

    assert result["state"] == "not_airborne"
    assert result["position"] is None


def test_landed_for_ended_flight(sqlite_session):
    snapshot = _make_snapshot(status=FlightStatus.LANDED)
    sqlite_session.add(snapshot)
    sqlite_session.commit()

    result = live_tracking_service.get_live_track(sqlite_session, MagicMock(), snapshot.flight_id)

    assert result["state"] == "landed"


def test_unavailable_for_unknown_flight_id(sqlite_session):
    result = live_tracking_service.get_live_track(sqlite_session, MagicMock(), "does-not-exist")

    assert result["state"] == "unavailable"


def test_tracking_resolves_icao24_and_persists_position(sqlite_session):
    sqlite_session.add(AircraftRegistry(icao24="a1b2c3", registration="N12345"))
    snapshot = _make_snapshot()
    sqlite_session.add(snapshot)
    sqlite_session.commit()

    opensky = MagicMock()
    opensky.get_states.return_value = {
        "latitude": 41.9786,
        "longitude": -87.9048,
        "baro_altitude": 10363.2,
        "velocity": 123.5,
        "true_track": 92.0,
        "on_ground": False,
    }

    result = live_tracking_service.get_live_track(sqlite_session, opensky, snapshot.flight_id)

    assert result["state"] == "tracking"
    assert result["position"]["lat"] == 41.9786
    assert result["resolution"]["method"] == "registration_lookup"
    opensky.get_states.assert_called_once_with("a1b2c3")


def test_unavailable_when_icao24_cannot_be_resolved(sqlite_session):
    snapshot = _make_snapshot(registration="N-UNKNOWN")
    sqlite_session.add(snapshot)
    sqlite_session.commit()

    opensky = MagicMock()
    opensky.find_state_by_callsign.return_value = None

    result = live_tracking_service.get_live_track(sqlite_session, opensky, snapshot.flight_id)

    assert result["state"] == "unavailable"
    opensky.get_states.assert_not_called()


def test_throttles_repeated_polls_within_min_interval(sqlite_session, monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("OPENSKY_MIN_POLL_INTERVAL_SECONDS", "3600")
    get_settings.cache_clear()
    try:
        sqlite_session.add(AircraftRegistry(icao24="a1b2c3", registration="N12345"))
        snapshot = _make_snapshot()
        sqlite_session.add(snapshot)
        sqlite_session.commit()

        opensky = MagicMock()
        opensky.get_states.return_value = {
            "latitude": 41.9786,
            "longitude": -87.9048,
            "baro_altitude": 10363.2,
            "velocity": 123.5,
            "true_track": 92.0,
            "on_ground": False,
        }

        first = live_tracking_service.get_live_track(sqlite_session, opensky, snapshot.flight_id)
        second = live_tracking_service.get_live_track(sqlite_session, opensky, snapshot.flight_id)

        assert first["state"] == "tracking"
        assert second["state"] == "tracking"
        assert second["position"] == first["position"]
        opensky.get_states.assert_called_once()
    finally:
        monkeypatch.delenv("OPENSKY_MIN_POLL_INTERVAL_SECONDS", raising=False)
        get_settings.cache_clear()
