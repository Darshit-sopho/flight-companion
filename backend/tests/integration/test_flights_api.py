"""Full request/response cycle tests against a real (ephemeral) Postgres DB, via FastAPI's TestClient.
HTTP calls to AeroAPI/OpenSky are replaced with the fixture clients (app/clients/fixtures.py) — the point
here is to exercise real service + DB + router wiring together, not to mock at the service layer.

Requires `docker compose up -d db` — see ../../README.md.
"""

import pytest
from fastapi.testclient import TestClient

from app.clients.aeroapi_client import AeroAPINotFoundError
from app.clients.fixtures import FixtureAeroAPIClient, FixtureOpenSkyClient
from app.db.session import get_db
from app.dependencies import get_aeroapi_client, get_opensky_client
from app.main import create_app


class _NotFoundAeroAPIClient(FixtureAeroAPIClient):
    def get_flight(self, ident, date_str):
        raise AeroAPINotFoundError(f"no flight {ident} on {date_str}")


@pytest.fixture()
def make_client(db_session):
    def _make(aeroapi=None, opensky=None):
        app = create_app()
        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_aeroapi_client] = lambda: aeroapi or FixtureAeroAPIClient()
        app.dependency_overrides[get_opensky_client] = lambda: opensky or FixtureOpenSkyClient()
        return TestClient(app)

    return _make


def test_search_flight_returns_200_and_flight_id(make_client):
    client = make_client()

    response = client.get("/api/flights/search", params={"ident": "FIX100", "date": "2026-09-12"})

    assert response.status_code == 200
    body = response.json()
    assert body["flight_id"] == "FIX100-2026-09-12"
    assert body["ident"] == "FIX100"
    assert body["origin"] == "SFO"


def test_search_unknown_flight_returns_404(make_client):
    client = make_client(aeroapi=_NotFoundAeroAPIClient())

    response = client.get("/api/flights/search", params={"ident": "ZZZ999", "date": "2026-09-12"})

    assert response.status_code == 404


def test_status_endpoint_returns_full_status_for_active_flight(make_client):
    client = make_client()
    client.get("/api/flights/search", params={"ident": "FIX100", "date": "2026-09-12"})

    response = client.get("/api/flights/FIX100-2026-09-12")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "active"
    assert body["origin"]["code"] == "SFO"
    assert body["origin"]["gate"] == "A12"


def test_status_endpoint_unknown_flight_returns_404(make_client):
    client = make_client()

    response = client.get("/api/flights/DOES-NOT-EXIST")

    assert response.status_code == 404


def test_history_endpoint_returns_aggregate_stats(make_client):
    client = make_client()
    client.get("/api/flights/search", params={"ident": "FIX100", "date": "2026-09-12"})

    response = client.get("/api/flights/FIX100-2026-09-12/history")

    assert response.status_code == 200
    body = response.json()
    assert body["on_time_percentage"] is not None
    assert len(body["occurrences"]) == 10


def test_track_endpoint_reflects_airborne_state(make_client):
    client = make_client()
    client.get("/api/flights/search", params={"ident": "FIX100", "date": "2026-09-12"})

    response = client.get("/api/flights/FIX100-2026-09-12/track")

    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "tracking"
    assert body["position"]["lat"] is not None


def test_track_endpoint_landed_flight_is_not_tracking(make_client):
    client = make_client()
    client.get("/api/flights/search", params={"ident": "FIX200", "date": "2026-09-12"})

    response = client.get("/api/flights/FIX200-2026-09-12/track")

    assert response.status_code == 200
    assert response.json()["state"] == "landed"


def test_airport_endpoint_returns_reference_info(make_client):
    client = make_client()

    response = client.get("/api/airports/SFO")

    assert response.status_code == 200
    body = response.json()
    assert body["city"] == "San Francisco"
    assert body["timezone"] == "America/Los_Angeles"


def test_airport_endpoint_unknown_code_returns_404(make_client):
    client = make_client()

    response = client.get("/api/airports/ZZZ")

    assert response.status_code == 404


def test_status_endpoint_returns_status_card_fields(make_client):
    client = make_client()
    client.get("/api/flights/search", params={"ident": "FIX100", "date": "2026-09-12"})

    response = client.get("/api/flights/FIX100-2026-09-12")

    assert response.status_code == 200
    body = response.json()
    assert body["progress_percent"] == 35
    assert body["flight_duration_minutes"] == 330
    assert body["route_distance"] == 1846
    assert body["operator"]["icao"] == "SWO"
    assert body["origin"]["iata"] == "SFO"
    assert body["origin"]["name"] == "San Francisco International Airport"
    assert body["origin"]["timezone"] == "America/Los_Angeles"
    assert body["diverted"] is None


def test_status_endpoint_diverted_flight_shows_original_and_diverted_destination(make_client):
    client = make_client()
    client.get("/api/flights/search", params={"ident": "FIX300", "date": "2026-09-12"})

    response = client.get("/api/flights/FIX300-2026-09-12")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "diverted"
    # Original (filed) destination is untouched.
    assert body["destination"]["code"] == "DEN"
    # Actual diverted-to destination is a separate object.
    assert body["diverted"] is not None
    assert body["diverted"]["airport"]["code"] == "LAS"
    assert body["diverted"]["actual_arrival"] is not None


def test_cache_hit_does_not_call_aeroapi_again_within_ttl(make_client):
    call_count = {"n": 0}

    class CountingAeroAPIClient(FixtureAeroAPIClient):
        def get_flight(self, ident, date_str):
            call_count["n"] += 1
            return super().get_flight(ident, date_str)

    client = make_client(aeroapi=CountingAeroAPIClient())
    client.get("/api/flights/search", params={"ident": "FIX100", "date": "2026-09-12"})
    client.get("/api/flights/FIX100-2026-09-12")

    assert call_count["n"] == 1
