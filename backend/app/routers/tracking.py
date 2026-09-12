from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.clients.opensky_client import OpenSkyClient
from app.db.session import get_db
from app.dependencies import get_opensky_client
from app.schemas.flight import TrackResponse
from app.services import live_tracking_service

router = APIRouter(prefix="/api/flights", tags=["tracking"])


@router.get("/{flight_id}/track", response_model=TrackResponse)
def get_track(
    flight_id: str,
    db: Session = Depends(get_db),
    opensky: OpenSkyClient = Depends(get_opensky_client),
) -> TrackResponse:
    result = live_tracking_service.get_live_track(db, opensky, flight_id)
    return TrackResponse(**result)
