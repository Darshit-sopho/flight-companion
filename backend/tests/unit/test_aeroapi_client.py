from unittest.mock import MagicMock

import pytest

from app.clients.aeroapi_client import AeroAPIClient, AeroAPINotFoundError


def _make_response(status_code: int, payload: dict | None = None) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = payload or {}
    if status_code >= 400 and status_code != 404:
        response.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    return response


def _make_client(response: MagicMock) -> AeroAPIClient:
    http_client = MagicMock()
    http_client.get.return_value = response
    return AeroAPIClient(api_key="test-key", base_url="https://example.test", client=http_client)


class TestGetFlight:
    def test_queries_a_full_day_range_not_a_same_day_range(self):
        # Regression test: AeroAPI rejects start == end with 400 INVALID_ARGUMENT — see the fix in
        # this session's history. start/end must span [date, date+1).
        http_client = MagicMock()
        http_client.get.return_value = _make_response(200, {"flights": [{"ident": "UA123"}]})
        client = AeroAPIClient(api_key="k", base_url="https://example.test", client=http_client)

        client.get_flight("UA123", "2026-09-12")

        args, kwargs = http_client.get.call_args
        assert kwargs["params"]["start"] == "2026-09-12"
        assert kwargs["params"]["end"] == "2026-09-13"

    def test_returns_first_flight_from_response(self):
        client = _make_client(_make_response(200, {"flights": [{"ident": "UA123"}, {"ident": "UA124"}]}))
        assert client.get_flight("UA123", "2026-09-12")["ident"] == "UA123"

    def test_raises_not_found_on_404(self):
        client = _make_client(_make_response(404))
        with pytest.raises(AeroAPINotFoundError):
            client.get_flight("ZZZ999", "2026-09-12")

    def test_raises_not_found_on_empty_flights_list(self):
        client = _make_client(_make_response(200, {"flights": []}))
        with pytest.raises(AeroAPINotFoundError):
            client.get_flight("ZZZ999", "2026-09-12")


class TestGetFlightById:
    """See docs/features/status-card-requirements.md#SC-A4.3 — a diverted flight's fa_flight_id can
    return multiple records; this must pick the one representing the real outcome.
    """

    def test_prefers_the_record_with_actual_on_populated(self):
        records = [
            {"diverted": True, "actual_on": None, "destination": {"code": "KUNI"}},
            {"diverted": False, "actual_on": "2026-09-13T01:31:45Z", "destination": {"code": "KCRW"}},
        ]
        client = _make_client(_make_response(200, {"flights": records}))

        result = client.get_flight_by_id("EJA532-1789250714-sw-1131p")

        assert result["destination"]["code"] == "KCRW"

    def test_falls_back_to_non_diverted_record_when_none_has_actual_on(self):
        records = [
            {"diverted": True, "actual_on": None, "destination": {"code": "A"}},
            {"diverted": False, "actual_on": None, "destination": {"code": "B"}},
        ]
        client = _make_client(_make_response(200, {"flights": records}))

        result = client.get_flight_by_id("some-id")

        assert result["destination"]["code"] == "B"

    def test_falls_back_to_first_record_when_all_are_diverted_with_no_actual_data(self):
        records = [
            {"diverted": True, "actual_on": None, "destination": {"code": "A"}},
            {"diverted": True, "actual_on": None, "destination": {"code": "B"}},
        ]
        client = _make_client(_make_response(200, {"flights": records}))

        result = client.get_flight_by_id("some-id")

        assert result["destination"]["code"] == "A"

    def test_raises_not_found_on_404(self):
        client = _make_client(_make_response(404))
        with pytest.raises(AeroAPINotFoundError):
            client.get_flight_by_id("does-not-exist")

    def test_raises_not_found_on_empty_flights_list(self):
        client = _make_client(_make_response(200, {"flights": []}))
        with pytest.raises(AeroAPINotFoundError):
            client.get_flight_by_id("does-not-exist")
