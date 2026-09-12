"""The highest-value tests in the repo — see docs/ARCHITECTURE.md#aeroapi--opensky-linking and
CLAUDE.md. Covers every branch of the resolution pipeline in isolation, with a mocked OpenSky client.
"""

from unittest.mock import MagicMock

from app.db.models import AircraftRegistry, ResolutionConfidence, ResolutionMethod
from app.services.icao24_resolver import resolve_icao24


def test_resolves_via_registration_lookup_without_calling_opensky(sqlite_session):
    sqlite_session.add(AircraftRegistry(icao24="a1b2c3", registration="N12345", model="B738"))
    sqlite_session.commit()
    opensky = MagicMock()

    result = resolve_icao24(
        sqlite_session, registration="n12345", candidate_idents=["UAL123"], opensky_client=opensky
    )

    assert result.icao24 == "a1b2c3"
    assert result.method == ResolutionMethod.REGISTRATION_LOOKUP
    assert result.confidence == ResolutionConfidence.HIGH
    opensky.find_state_by_callsign.assert_not_called()


def test_falls_back_to_callsign_when_registration_not_in_registry(sqlite_session):
    opensky = MagicMock()
    opensky.find_state_by_callsign.return_value = {"icao24": "d4e5f6", "callsign": "UAL123"}

    result = resolve_icao24(
        sqlite_session, registration="N99999", candidate_idents=["UAL123"], opensky_client=opensky
    )

    assert result.icao24 == "d4e5f6"
    assert result.method == ResolutionMethod.CALLSIGN_FALLBACK
    assert result.confidence == ResolutionConfidence.LOW


def test_falls_back_to_callsign_when_registration_missing(sqlite_session):
    opensky = MagicMock()
    opensky.find_state_by_callsign.return_value = {"icao24": "112233"}

    result = resolve_icao24(
        sqlite_session, registration=None, candidate_idents=["UAL123"], opensky_client=opensky
    )

    assert result.icao24 == "112233"
    assert result.method == ResolutionMethod.CALLSIGN_FALLBACK


def test_tries_every_candidate_ident_for_codeshares(sqlite_session):
    opensky = MagicMock()
    opensky.find_state_by_callsign.side_effect = [None, {"icao24": "abcdef"}]

    result = resolve_icao24(
        sqlite_session,
        registration=None,
        candidate_idents=["UAL123", "SKW456"],
        opensky_client=opensky,
    )

    assert result.icao24 == "abcdef"
    assert result.method == ResolutionMethod.CALLSIGN_FALLBACK
    assert opensky.find_state_by_callsign.call_count == 2


def test_returns_unresolved_when_nothing_matches(sqlite_session):
    opensky = MagicMock()
    opensky.find_state_by_callsign.return_value = None

    result = resolve_icao24(
        sqlite_session,
        registration="N00000",
        candidate_idents=["UAL123", "SKW456"],
        opensky_client=opensky,
    )

    assert result.icao24 is None
    assert result.method == ResolutionMethod.UNRESOLVED
    assert result.confidence == ResolutionConfidence.NONE


def test_blank_candidate_idents_are_skipped_without_calling_opensky(sqlite_session):
    opensky = MagicMock()

    result = resolve_icao24(
        sqlite_session, registration=None, candidate_idents=["", "   "], opensky_client=opensky
    )

    assert result.method == ResolutionMethod.UNRESOLVED
    opensky.find_state_by_callsign.assert_not_called()
