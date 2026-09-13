"""FastAPI dependency providers for the external API clients. Swaps in the fixture clients when
FIXTURE_MODE is enabled (see app/clients/fixtures.py and docs/TESTING.md) so tests and fixture-mode dev
runs never make real network calls.
"""

from __future__ import annotations

from functools import lru_cache

from app.clients.aeroapi_client import AeroAPIClient
from app.clients.fixtures import FixtureAeroAPIClient, FixtureOpenMeteoClient, FixtureOpenSkyClient
from app.clients.openmeteo_client import OpenMeteoClient
from app.clients.opensky_client import OpenSkyClient
from app.config import get_settings


@lru_cache
def _aeroapi_singleton() -> AeroAPIClient | FixtureAeroAPIClient:
    if get_settings().fixture_mode:
        return FixtureAeroAPIClient()
    return AeroAPIClient()


@lru_cache
def _opensky_singleton() -> OpenSkyClient | FixtureOpenSkyClient:
    if get_settings().fixture_mode:
        return FixtureOpenSkyClient()
    return OpenSkyClient()


@lru_cache
def _openmeteo_singleton() -> OpenMeteoClient | FixtureOpenMeteoClient:
    if get_settings().fixture_mode:
        return FixtureOpenMeteoClient()
    return OpenMeteoClient()


def get_aeroapi_client() -> AeroAPIClient | FixtureAeroAPIClient:
    return _aeroapi_singleton()


def get_opensky_client() -> OpenSkyClient | FixtureOpenSkyClient:
    return _opensky_singleton()


def get_openmeteo_client() -> OpenMeteoClient | FixtureOpenMeteoClient:
    return _openmeteo_singleton()
