"""Cache-hit vs. cache-expired decision logic — the core of the AeroAPI cost-control rule. See
docs/DATA_SOURCES.md#cost-control.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

from app.core.time import utcnow
from app.db.models import FlightSnapshot, FlightStatus
from app.services import flight_status_service


def _make_snapshot(flight_id="UAL123-2026-09-12", **overrides) -> FlightSnapshot:
    defaults = dict(
        flight_id=flight_id,
        ident="UAL123",
        scheduled_date=datetime(2026, 9, 12).date(),
        status=FlightStatus.ACTIVE,
        fetched_at=utcnow(),
        expires_at=utcnow() + timedelta(minutes=10),
    )
    defaults.update(overrides)
    return FlightSnapshot(**defaults)


def test_returns_cached_snapshot_without_calling_aeroapi_when_fresh(sqlite_session):
    snapshot = _make_snapshot()
    sqlite_session.add(snapshot)
    sqlite_session.commit()
    aeroapi = MagicMock()

    result = flight_status_service.get_status(sqlite_session, aeroapi, snapshot.flight_id)

    assert result.flight_id == snapshot.flight_id
    aeroapi.get_flight.assert_not_called()


def test_refreshes_from_aeroapi_when_ttl_expired(sqlite_session):
    snapshot = _make_snapshot(expires_at=utcnow() - timedelta(minutes=1))
    sqlite_session.add(snapshot)
    sqlite_session.commit()
    aeroapi = MagicMock()
    aeroapi.get_flight.return_value = {
        "origin": {"code": "SFO"},
        "destination": {"code": "ORD"},
        "registration": "N12345",
        "status": "landed",
        "scheduled_out": "2026-09-12T14:30:00Z",
        "actual_out": "2026-09-12T14:47:00Z",
        "scheduled_in": "2026-09-12T20:10:00Z",
        "actual_in": "2026-09-12T20:25:00Z",
    }

    result = flight_status_service.get_status(sqlite_session, aeroapi, snapshot.flight_id)

    aeroapi.get_flight.assert_called_once_with("UAL123", "2026-09-12")
    assert result.status == FlightStatus.LANDED


def test_returns_none_for_unknown_flight_id(sqlite_session):
    aeroapi = MagicMock()

    result = flight_status_service.get_status(sqlite_session, aeroapi, "does-not-exist")

    assert result is None
    aeroapi.get_flight.assert_not_called()


def test_updates_last_viewed_at_on_every_call(sqlite_session):
    snapshot = _make_snapshot(last_viewed_at=None)
    sqlite_session.add(snapshot)
    sqlite_session.commit()
    aeroapi = MagicMock()

    flight_status_service.get_status(sqlite_session, aeroapi, snapshot.flight_id)

    assert snapshot.last_viewed_at is not None
