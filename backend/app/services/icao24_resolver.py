"""Resolves the link between an AeroAPI flight instance and its OpenSky live-position feed.

This is the trickiest logic in the backend — see docs/ARCHITECTURE.md#aeroapi--opensky-linking for the
full write-up. Summary of the pipeline:

  1. Registration (tail number) from AeroAPI -> icao24 via the locally-synced aircraft_registry table.
  2. If that fails, fall back to matching OpenSky's live callsign field against the flight's ident(s).
  3. If both fail, return an explicit "unresolved" result — callers must never treat this as an error.

Never cache a resolution result by bare flight number — only by flight_id (ident + date), since the same
flight number flies a different tail aircraft on different days.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.opensky_client import OpenSkyClient
from app.db.models import AircraftRegistry, ResolutionConfidence, ResolutionMethod


@dataclass(frozen=True)
class ResolutionResult:
    icao24: str | None
    method: ResolutionMethod
    confidence: ResolutionConfidence


def resolve_icao24(
    db: Session,
    *,
    registration: str | None,
    candidate_idents: list[str],
    opensky_client: OpenSkyClient,
) -> ResolutionResult:
    """Resolve a flight instance to an OpenSky icao24 address.

    `candidate_idents` should include every ident that might appear as the aircraft's broadcast
    callsign — typically just the searched flight number, but pass both marketing and operating idents
    for codeshares if both are known.
    """
    if registration:
        registry_row = db.scalar(
            select(AircraftRegistry).where(AircraftRegistry.registration == registration.upper())
        )
        if registry_row is not None:
            return ResolutionResult(
                icao24=registry_row.icao24,
                method=ResolutionMethod.REGISTRATION_LOOKUP,
                confidence=ResolutionConfidence.HIGH,
            )

    match = opensky_client.find_state_by_callsigns(candidate_idents)
    if match:
        return ResolutionResult(
            icao24=match["icao24"],
            method=ResolutionMethod.CALLSIGN_FALLBACK,
            confidence=ResolutionConfidence.LOW,
        )

    return ResolutionResult(
        icao24=None, method=ResolutionMethod.UNRESOLVED, confidence=ResolutionConfidence.NONE
    )
