from datetime import datetime

from app.db.models import FlightStatus
from app.services.utils import (
    compute_delay_minutes,
    is_on_time,
    map_status,
    meters_to_feet,
    ms_to_knots,
    parse_dt,
)


def test_parse_dt_handles_zulu_suffix():
    assert parse_dt("2026-09-12T14:30:00Z") == datetime.fromisoformat("2026-09-12T14:30:00+00:00")


def test_parse_dt_handles_none():
    assert parse_dt(None) is None


def test_map_status_known_values():
    assert map_status("En Route") == FlightStatus.ACTIVE
    assert map_status("Cancelled") == FlightStatus.CANCELLED
    assert map_status("Landed") == FlightStatus.LANDED


def test_map_status_handles_real_aeroapi_compound_strings():
    # AeroAPI's actual `status` field is free-text and often compound, e.g. "En Route / On Time" —
    # this is the exact string a real flight returned during manual testing.
    assert map_status("En Route / On Time") == FlightStatus.ACTIVE
    assert map_status("En Route / Delayed") == FlightStatus.ACTIVE
    assert map_status("Landed / Gate Arrival") == FlightStatus.LANDED
    assert map_status("Landed / Taxiing") == FlightStatus.LANDED


def test_map_status_prioritizes_cancelled_and_diverted_over_other_keywords():
    assert map_status("Cancelled / En Route") == FlightStatus.CANCELLED
    assert map_status("Diverted / Landed") == FlightStatus.DIVERTED


def test_map_status_unknown_or_missing_defaults_to_scheduled():
    assert map_status("something weird") == FlightStatus.SCHEDULED
    assert map_status(None) == FlightStatus.SCHEDULED


def test_compute_delay_minutes():
    scheduled = datetime.fromisoformat("2026-09-12T14:30:00+00:00")
    actual = datetime.fromisoformat("2026-09-12T14:47:00+00:00")
    assert compute_delay_minutes(scheduled, actual) == 17


def test_compute_delay_minutes_missing_data_returns_none():
    assert compute_delay_minutes(None, None) is None


def test_is_on_time_threshold():
    assert is_on_time(15) is True
    assert is_on_time(16) is False
    assert is_on_time(None) is None


def test_unit_conversions():
    assert meters_to_feet(10000) == 32808.4
    assert ms_to_knots(100) == 194.4


def test_unit_conversions_handle_none():
    assert meters_to_feet(None) is None
    assert ms_to_knots(None) is None
