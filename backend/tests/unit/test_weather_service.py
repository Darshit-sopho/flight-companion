"""Cache-hit vs. cache-expired decision logic for airport weather, plus the nearest-hour "outlook"
selection — see docs/features/status-card-requirements.md#SC-D2.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from app.core.time import utcnow
from app.db.models import Airport, AirportWeatherSnapshot
from app.services import weather_service

_HOURLY = [
    {"time": "2026-09-12T14:00", "temp_f": 68.0, "weather_code": 2},
    {"time": "2026-09-12T15:00", "temp_f": 70.0, "weather_code": 61},
    {"time": "2026-09-12T20:00", "temp_f": 55.0, "weather_code": 3},
]


def _make_airport(**overrides) -> Airport:
    defaults = dict(code="SFO", lat=37.6213, lon=-122.379)
    defaults.update(overrides)
    return Airport(**defaults)


def _make_forecast_response() -> dict:
    return {
        "current": {"time": "2026-09-12T14:05", "temp_f": 68.0, "weather_code": 2},
        "hourly": _HOURLY,
    }


def test_fetches_and_caches_on_first_lookup(sqlite_session):
    airport = _make_airport()
    sqlite_session.add(airport)
    sqlite_session.commit()
    openmeteo = MagicMock()
    openmeteo.get_forecast.return_value = _make_forecast_response()

    result = weather_service.get_airport_weather(
        sqlite_session, openmeteo, airport, at=datetime(2026, 9, 12, 15, 0, tzinfo=UTC)
    )

    openmeteo.get_forecast.assert_called_once_with(37.6213, -122.379)
    assert result.now.bucket == "partly_cloudy"
    assert result.now.temp_f == 68.0
    assert result.outlook.bucket == "rain"
    assert result.outlook.temp_f == 70.0


def test_does_not_call_openmeteo_again_within_ttl(sqlite_session):
    airport = _make_airport()
    sqlite_session.add(airport)
    snapshot = AirportWeatherSnapshot(
        airport_code="SFO",
        current_weather_code=0,
        current_temp_f=72.0,
        current_observed_at=utcnow(),
        hourly_forecast=_HOURLY,
        fetched_at=utcnow(),
        expires_at=utcnow() + timedelta(minutes=30),
    )
    sqlite_session.add(snapshot)
    sqlite_session.commit()
    openmeteo = MagicMock()

    result = weather_service.get_airport_weather(sqlite_session, openmeteo, airport)

    openmeteo.get_forecast.assert_not_called()
    assert result.now.temp_f == 72.0


def test_refetches_once_ttl_has_expired(sqlite_session):
    airport = _make_airport()
    sqlite_session.add(airport)
    snapshot = AirportWeatherSnapshot(
        airport_code="SFO",
        current_weather_code=0,
        current_temp_f=72.0,
        current_observed_at=utcnow(),
        hourly_forecast=_HOURLY,
        fetched_at=utcnow() - timedelta(hours=1),
        expires_at=utcnow() - timedelta(minutes=1),
    )
    sqlite_session.add(snapshot)
    sqlite_session.commit()
    openmeteo = MagicMock()
    openmeteo.get_forecast.return_value = _make_forecast_response()

    result = weather_service.get_airport_weather(sqlite_session, openmeteo, airport)

    openmeteo.get_forecast.assert_called_once()
    assert result.now.temp_f == 68.0


def test_returns_none_when_airport_has_no_coordinates(sqlite_session):
    airport = _make_airport(lat=None, lon=None)
    sqlite_session.add(airport)
    sqlite_session.commit()
    openmeteo = MagicMock()

    result = weather_service.get_airport_weather(sqlite_session, openmeteo, airport)

    assert result is None
    openmeteo.get_forecast.assert_not_called()


def test_outlook_is_none_when_no_hourly_entry_is_within_three_hours(sqlite_session):
    airport = _make_airport()
    sqlite_session.add(airport)
    sqlite_session.commit()
    openmeteo = MagicMock()
    openmeteo.get_forecast.return_value = _make_forecast_response()

    result = weather_service.get_airport_weather(
        sqlite_session, openmeteo, airport, at=datetime(2026, 9, 13, 4, 0, tzinfo=UTC)
    )

    assert result.outlook is None


def test_defaults_target_time_to_now_when_at_is_omitted(sqlite_session):
    airport = _make_airport()
    sqlite_session.add(airport)
    sqlite_session.commit()
    openmeteo = MagicMock()
    near_now = utcnow().replace(microsecond=0)
    openmeteo.get_forecast.return_value = {
        "current": {"time": "2026-09-12T14:05", "temp_f": 68.0, "weather_code": 2},
        "hourly": [{"time": near_now.strftime("%Y-%m-%dT%H:%M"), "temp_f": 61.0, "weather_code": 0}],
    }

    result = weather_service.get_airport_weather(sqlite_session, openmeteo, airport)

    assert result.outlook is not None
    assert result.outlook.bucket == "clear"
