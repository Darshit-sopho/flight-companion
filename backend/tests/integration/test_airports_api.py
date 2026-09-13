"""Full request/response cycle tests for the airport weather endpoint, against a real (ephemeral)
Postgres DB — see test_flights_api.py for the shared pattern this mirrors.
"""

import pytest
from fastapi.testclient import TestClient

from app.clients.fixtures import FixtureAeroAPIClient, FixtureOpenMeteoClient, FixtureOpenSkyClient
from app.db.session import get_db
from app.dependencies import get_aeroapi_client, get_openmeteo_client, get_opensky_client
from app.main import create_app


@pytest.fixture()
def make_client(db_session):
    def _make(aeroapi=None, opensky=None, openmeteo=None):
        app = create_app()
        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_aeroapi_client] = lambda: aeroapi or FixtureAeroAPIClient()
        app.dependency_overrides[get_opensky_client] = lambda: opensky or FixtureOpenSkyClient()
        app.dependency_overrides[get_openmeteo_client] = lambda: openmeteo or FixtureOpenMeteoClient()
        return TestClient(app)

    return _make


def test_airport_weather_returns_now_and_outlook(make_client):
    client = make_client()

    response = client.get("/api/airports/SFO/weather")

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == "SFO"
    assert body["now"]["bucket"] == "partly_cloudy"
    assert body["now"]["temp_f"] == 68.0
    assert body["outlook"] is not None


def test_airport_weather_accepts_an_at_query_param(make_client):
    client = make_client()

    response = client.get("/api/airports/SFO/weather", params={"at": "2026-09-12T20:00:00Z"})

    assert response.status_code == 200


def test_airport_weather_unknown_airport_returns_404(make_client):
    client = make_client()

    response = client.get("/api/airports/ZZZ/weather")

    assert response.status_code == 404


def test_second_call_within_ttl_does_not_call_openmeteo_again(make_client):
    call_count = {"n": 0}

    class CountingOpenMeteoClient(FixtureOpenMeteoClient):
        def get_forecast(self, lat, lon):
            call_count["n"] += 1
            return super().get_forecast(lat, lon)

    client = make_client(openmeteo=CountingOpenMeteoClient())
    client.get("/api/airports/SFO/weather")
    client.get("/api/airports/SFO/weather")

    assert call_count["n"] == 1
