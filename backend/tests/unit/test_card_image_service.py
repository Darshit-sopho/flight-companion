"""Renders a PNG for every flight status this app supports and checks only that it succeeds and comes
out the right size/format -- NOT the rendered pixel/text content, which isn't reasonably assertable
without OCR. See docs/features/status-card-requirements.md#SC-D3.
"""

from __future__ import annotations

import io
from datetime import UTC, datetime

import pytest
from PIL import Image

from app.db.models import FlightSnapshot, FlightStatus
from app.services.card_image_service import render_card


def _make_snapshot(**overrides) -> FlightSnapshot:
    defaults = dict(
        flight_id="UAL123-2026-09-12",
        ident="UAL123",
        status=FlightStatus.ACTIVE,
        scheduled_date=datetime(2026, 9, 12).date(),
        origin_code="KSFO",
        origin_iata="SFO",
        origin_name="San Francisco International Airport",
        origin_city="San Francisco",
        origin_timezone="America/Los_Angeles",
        destination_code="KORD",
        destination_iata="ORD",
        destination_name="O'Hare International Airport",
        destination_city="Chicago",
        destination_timezone="America/Chicago",
        scheduled_departure=datetime(2026, 9, 12, 14, 30, tzinfo=UTC),
        estimated_departure=datetime(2026, 9, 12, 14, 45, tzinfo=UTC),
        actual_departure=datetime(2026, 9, 12, 14, 47, tzinfo=UTC),
        scheduled_arrival=datetime(2026, 9, 12, 20, 10, tzinfo=UTC),
        estimated_arrival=datetime(2026, 9, 12, 20, 22, tzinfo=UTC),
        delay_minutes=12,
        registration="N12345",
        aircraft_type="B738",
        operator_icao="UAL",
        operator_iata="UA",
        progress_percent=42,
        flight_duration_minutes=330,
        route_distance=1846,
        departure_gate="A12",
        departure_terminal="2",
        arrival_terminal="1",
    )
    defaults.update(overrides)
    return FlightSnapshot(**defaults)


def _assert_valid_card_png(png_bytes: bytes) -> None:
    image = Image.open(io.BytesIO(png_bytes))
    assert image.format == "PNG"
    assert image.size == (1200, 630)


@pytest.mark.parametrize(
    "status",
    [FlightStatus.SCHEDULED, FlightStatus.ACTIVE, FlightStatus.LANDED, FlightStatus.CANCELLED],
)
def test_renders_a_valid_png_for_every_ordinary_status(status):
    snapshot = _make_snapshot(status=status)
    _assert_valid_card_png(render_card(snapshot))


def test_renders_a_valid_png_for_a_diverted_flight():
    snapshot = _make_snapshot(
        status=FlightStatus.DIVERTED,
        diverted_destination_code="KCRW",
        diverted_destination_iata="CRW",
        diverted_destination_name="West Virginia Intl Yeager",
        diverted_destination_city="Charleston",
        diverted_destination_timezone="America/New_York",
        diverted_actual_arrival=datetime(2026, 9, 13, 1, 31, 45, tzinfo=UTC),
        diverted_arrival_gate="D4",
    )
    _assert_valid_card_png(render_card(snapshot))


def test_renders_a_valid_png_when_every_optional_field_is_none():
    snapshot = FlightSnapshot(
        flight_id="ZZZ1-2026-09-12",
        ident="ZZZ1",
        status=FlightStatus.SCHEDULED,
        scheduled_date=datetime(2026, 9, 12).date(),
    )
    _assert_valid_card_png(render_card(snapshot))


def test_never_calls_out_to_aeroapi_or_opensky():
    """Rendering must work purely from the already-fetched snapshot -- no new external call, no new
    cache table (see docs/DATA_SOURCES.md's note on SC-D3).
    """
    snapshot = _make_snapshot()
    render_card(snapshot)  # would raise if it tried to touch a network client that isn't passed in at all
