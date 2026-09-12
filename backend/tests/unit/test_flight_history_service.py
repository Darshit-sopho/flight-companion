from datetime import date, timedelta
from unittest.mock import MagicMock

from app.services import flight_history_service


def _history_flight(days_ago: int, delay_minutes: int) -> dict:
    d = date.today() - timedelta(days=days_ago)
    total_minutes = 30 + delay_minutes
    hour = 14 + total_minutes // 60
    minute = total_minutes % 60
    return {
        "origin": {"code": "SFO"},
        "destination": {"code": "ORD"},
        "scheduled_out": f"{d.isoformat()}T14:30:00Z",
        "actual_out": f"{d.isoformat()}T{hour:02d}:{minute:02d}:00Z",
    }


def test_computes_on_time_percentage_and_average_delay(sqlite_session):
    aeroapi = MagicMock()
    aeroapi.get_flight_history.return_value = [
        _history_flight(7, 5),
        _history_flight(14, 5),
        _history_flight(21, 40),
        _history_flight(28, 5),
    ]

    result = flight_history_service.get_history(sqlite_session, aeroapi, "UAL123", limit=4)

    assert result["on_time_percentage"] == 75.0
    assert result["average_delay_minutes"] == 13.8  # mean([5, 5, 40, 5]) = 13.75, rounded to 1 decimal
    assert len(result["occurrences"]) == 4


def test_empty_history_returns_stable_trend_and_no_stats(sqlite_session):
    aeroapi = MagicMock()
    aeroapi.get_flight_history.return_value = []

    result = flight_history_service.get_history(sqlite_session, aeroapi, "UAL123", limit=10)

    assert result["on_time_percentage"] is None
    assert result["average_delay_minutes"] is None
    assert result["trend"] == "stable"
    assert result["occurrences"] == []


def test_second_call_uses_cache_and_does_not_refetch(sqlite_session):
    aeroapi = MagicMock()
    aeroapi.get_flight_history.return_value = [_history_flight(7, 5), _history_flight(14, 5)]

    flight_history_service.get_history(sqlite_session, aeroapi, "UAL123", limit=2)
    flight_history_service.get_history(sqlite_session, aeroapi, "UAL123", limit=2)

    aeroapi.get_flight_history.assert_called_once()


def test_trend_detects_improving_delay():
    """Pure aggregation check via the public entrypoint using a fresh cache each time."""
    from app.db.models import FlightHistoryRecord
    from app.services.flight_history_service import _aggregate

    records = [
        FlightHistoryRecord(flight_date=date.today() - timedelta(days=7), delay_minutes=2, on_time=True),
        FlightHistoryRecord(flight_date=date.today() - timedelta(days=14), delay_minutes=3, on_time=True),
        FlightHistoryRecord(flight_date=date.today() - timedelta(days=21), delay_minutes=40, on_time=False),
        FlightHistoryRecord(flight_date=date.today() - timedelta(days=28), delay_minutes=45, on_time=False),
    ]

    result = _aggregate(records)

    assert result["trend"] == "improving"


def test_trend_detects_worsening_delay():
    from app.db.models import FlightHistoryRecord
    from app.services.flight_history_service import _aggregate

    records = [
        FlightHistoryRecord(flight_date=date.today() - timedelta(days=7), delay_minutes=45, on_time=False),
        FlightHistoryRecord(flight_date=date.today() - timedelta(days=14), delay_minutes=40, on_time=False),
        FlightHistoryRecord(flight_date=date.today() - timedelta(days=21), delay_minutes=3, on_time=True),
        FlightHistoryRecord(flight_date=date.today() - timedelta(days=28), delay_minutes=2, on_time=True),
    ]

    result = _aggregate(records)

    assert result["trend"] == "worsening"
