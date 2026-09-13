"""Airport reference data — effectively a permanent cache (docs/DATA_SOURCES.md#cost-control)."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.clients.aeroapi_client import AeroAPIClient, AeroAPINotFoundError
from app.core.time import utcnow
from app.db.models import Airport


def get_airport(db: Session, aeroapi: AeroAPIClient, code: str) -> Airport | None:
    code = code.upper()
    airport = db.get(Airport, code)
    if airport is not None:
        return airport

    try:
        raw = aeroapi.get_airport(code)
    except AeroAPINotFoundError:
        return None

    airport = Airport(
        code=code,
        name=raw.get("name"),
        city=raw.get("city"),
        country=raw.get("country_code"),
        lat=raw.get("latitude"),
        lon=raw.get("longitude"),
        timezone=raw.get("timezone"),
        updated_at=utcnow(),
    )
    db.add(airport)
    try:
        db.commit()
    except IntegrityError:
        # Two requests can both see no cached row for a never-before-looked-up airport and race to
        # insert it -- e.g. the status card's plain airport-info fetch and its weather fetch (SC-D2) now
        # resolve the same airport concurrently. The loser just re-reads what the winner wrote instead
        # of erroring.
        db.rollback()
        airport = db.get(Airport, code)
    else:
        db.refresh(airport)
    return airport
