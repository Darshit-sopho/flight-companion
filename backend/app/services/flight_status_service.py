"""Owns the AeroAPI cost-control rule for current-status data: only refresh a flight's status while
someone is actively viewing it, and only once its cache TTL has actually expired. See
docs/DATA_SOURCES.md#cost-control.

This is deliberately *not* a background job — there is no scheduler in this project. A flight's status is
refreshed exactly when (and only when) GET /api/flights/{flight_id} is called, which only happens when a
user has that flight's detail page open.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.clients.aeroapi_client import AeroAPIClient
from app.core.time import ensure_aware, utcnow
from app.db.models import FlightSnapshot
from app.services.flight_lookup_service import upsert_snapshot_from_aeroapi


def get_status(db: Session, aeroapi: AeroAPIClient, flight_id: str) -> FlightSnapshot | None:
    snapshot = db.get(FlightSnapshot, flight_id)
    if snapshot is None:
        return None

    snapshot.last_viewed_at = utcnow()

    if ensure_aware(snapshot.expires_at) <= utcnow():
        raw = aeroapi.get_flight(snapshot.ident, snapshot.scheduled_date.isoformat())
        return upsert_snapshot_from_aeroapi(
            db, flight_id, snapshot.ident, snapshot.scheduled_date.isoformat(), raw
        )

    db.commit()
    db.refresh(snapshot)
    return snapshot
