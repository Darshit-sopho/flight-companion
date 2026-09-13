from unittest.mock import MagicMock

from app.clients.aeroapi_client import AeroAPINotFoundError
from app.db.models import FlightStatus
from app.services import flight_lookup_service


def _raw_flight(**overrides) -> dict:
    base = {
        "ident": "UA123",
        "fa_flight_id": "UAL123-fa-id",
        "operator_icao": "UAL",
        "operator_iata": "UA",
        "ident_icao": "UAL123",
        "diverted": False,
        "status": "En Route / On Time",
        "origin": {
            "code": "KSFO",
            "code_iata": "SFO",
            "name": "San Francisco International",
            "city": "San Francisco",
            "timezone": "America/Los_Angeles",
        },
        "destination": {
            "code": "KORD",
            "code_iata": "ORD",
            "name": "O'Hare International",
            "city": "Chicago",
            "timezone": "America/Chicago",
        },
        "registration": "N12345",
        "aircraft_type": "B738",
        "scheduled_out": "2026-09-12T14:30:00Z",
        "estimated_out": "2026-09-12T14:45:00Z",
        "actual_out": "2026-09-12T14:47:00Z",
        "scheduled_in": "2026-09-12T20:10:00Z",
        "estimated_in": "2026-09-12T20:22:00Z",
        "actual_in": None,
        "gate_origin": "A12",
        "terminal_origin": "2",
        "gate_destination": "B4",
        "terminal_destination": "1",
        "progress_percent": 42,
        "filed_ete": 19800,  # 330 minutes
        "route_distance": 1846,
    }
    base.update(overrides)
    return base


class TestNewFieldMapping:
    def test_maps_progress_operator_duration_distance(self, sqlite_session):
        aeroapi = MagicMock()

        snapshot = flight_lookup_service.upsert_snapshot_from_aeroapi(
            sqlite_session, aeroapi, "UA123-2026-09-12", "UA123", "2026-09-12", _raw_flight()
        )

        assert snapshot.progress_percent == 42
        assert snapshot.operator_icao == "UAL"
        assert snapshot.operator_iata == "UA"
        assert snapshot.flight_duration_minutes == 330
        assert snapshot.route_distance == 1846
        aeroapi.get_flight_by_id.assert_not_called()

    def test_maps_origin_and_destination_identity_fields(self, sqlite_session):
        aeroapi = MagicMock()

        snapshot = flight_lookup_service.upsert_snapshot_from_aeroapi(
            sqlite_session, aeroapi, "UA123-2026-09-12", "UA123", "2026-09-12", _raw_flight()
        )

        assert snapshot.origin_code == "KSFO"
        assert snapshot.origin_iata == "SFO"
        assert snapshot.origin_name == "San Francisco International"
        assert snapshot.origin_city == "San Francisco"
        assert snapshot.origin_timezone == "America/Los_Angeles"
        assert snapshot.destination_code == "KORD"
        assert snapshot.destination_iata == "ORD"
        assert snapshot.destination_timezone == "America/Chicago"

    def test_flight_duration_is_none_when_filed_ete_missing(self, sqlite_session):
        aeroapi = MagicMock()
        raw = _raw_flight()
        del raw["filed_ete"]

        snapshot = flight_lookup_service.upsert_snapshot_from_aeroapi(
            sqlite_session, aeroapi, "UA123-2026-09-12", "UA123", "2026-09-12", raw
        )

        assert snapshot.flight_duration_minutes is None

    def test_stores_fa_flight_id(self, sqlite_session):
        aeroapi = MagicMock()

        snapshot = flight_lookup_service.upsert_snapshot_from_aeroapi(
            sqlite_session, aeroapi, "UA123-2026-09-12", "UA123", "2026-09-12", _raw_flight()
        )

        assert snapshot.fa_flight_id == "UAL123-fa-id"


class TestDivertedFlightHandling:
    """See docs/features/status-card-requirements.md#SC-A4.3."""

    def test_diverted_flight_triggers_second_lookup_and_populates_diverted_fields(self, sqlite_session):
        aeroapi = MagicMock()
        aeroapi.get_flight_by_id.return_value = {
            "destination": {
                "code": "KCRW",
                "code_iata": "CRW",
                "name": "West Virginia Intl Yeager",
                "city": "Charleston",
                "timezone": "America/New_York",
            },
            "scheduled_in": "2026-09-13T01:10:00Z",
            "estimated_in": "2026-09-13T01:31:45Z",
            "actual_in": "2026-09-13T01:31:45Z",
            "gate_destination": "D4",
            "terminal_destination": None,
        }
        raw = _raw_flight(diverted=True, status="Diverted")

        snapshot = flight_lookup_service.upsert_snapshot_from_aeroapi(
            sqlite_session, aeroapi, "UA123-2026-09-12", "UA123", "2026-09-12", raw
        )

        aeroapi.get_flight_by_id.assert_called_once_with("UAL123-fa-id")
        assert snapshot.status == FlightStatus.DIVERTED
        # Original destination fields must NOT be overwritten by the diverted-to airport.
        assert snapshot.destination_code == "KORD"
        # Diverted-to info lives in the separate diverted_* columns.
        assert snapshot.diverted_destination_code == "KCRW"
        assert snapshot.diverted_destination_iata == "CRW"
        assert snapshot.diverted_destination_city == "Charleston"
        assert snapshot.diverted_arrival_gate == "D4"
        assert snapshot.diverted_actual_arrival is not None

    def test_diverted_flight_without_fa_flight_id_skips_second_lookup(self, sqlite_session):
        aeroapi = MagicMock()
        raw = _raw_flight(diverted=True, status="Diverted", fa_flight_id=None)

        snapshot = flight_lookup_service.upsert_snapshot_from_aeroapi(
            sqlite_session, aeroapi, "UA123-2026-09-12", "UA123", "2026-09-12", raw
        )

        aeroapi.get_flight_by_id.assert_not_called()
        assert snapshot.diverted_destination_code is None

    def test_diverted_flight_second_lookup_not_found_leaves_diverted_fields_none(self, sqlite_session):
        aeroapi = MagicMock()
        aeroapi.get_flight_by_id.side_effect = AeroAPINotFoundError("gone")
        raw = _raw_flight(diverted=True, status="Diverted")

        snapshot = flight_lookup_service.upsert_snapshot_from_aeroapi(
            sqlite_session, aeroapi, "UA123-2026-09-12", "UA123", "2026-09-12", raw
        )

        assert snapshot.status == FlightStatus.DIVERTED
        assert snapshot.diverted_destination_code is None

    def test_non_diverted_flight_never_calls_get_flight_by_id(self, sqlite_session):
        aeroapi = MagicMock()
        raw = _raw_flight(diverted=False)

        flight_lookup_service.upsert_snapshot_from_aeroapi(
            sqlite_session, aeroapi, "UA123-2026-09-12", "UA123", "2026-09-12", raw
        )

        aeroapi.get_flight_by_id.assert_not_called()
