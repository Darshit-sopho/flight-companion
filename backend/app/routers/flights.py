from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.clients.aeroapi_client import AeroAPIClient, AeroAPINotFoundError
from app.db.models import FlightSnapshot
from app.db.session import get_db
from app.dependencies import get_aeroapi_client
from app.schemas.flight import FlightHistoryResponse, FlightSearchResponse, FlightStatusResponse
from app.services import (
    card_image_service,
    flight_history_service,
    flight_lookup_service,
    flight_status_service,
)

router = APIRouter(prefix="/api/flights", tags=["flights"])


@router.get("/search", response_model=FlightSearchResponse)
def search_flight(
    ident: str,
    date: str,
    db: Session = Depends(get_db),
    aeroapi: AeroAPIClient = Depends(get_aeroapi_client),
) -> FlightSearchResponse:
    try:
        snapshot = flight_lookup_service.search_flight(db, aeroapi, ident, date)
    except AeroAPINotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FlightSearchResponse.from_snapshot(snapshot)


@router.get("/{flight_id}", response_model=FlightStatusResponse)
def get_flight_status(
    flight_id: str,
    db: Session = Depends(get_db),
    aeroapi: AeroAPIClient = Depends(get_aeroapi_client),
) -> FlightStatusResponse:
    snapshot = flight_status_service.get_status(db, aeroapi, flight_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail=f"Unknown flight_id {flight_id}")
    return FlightStatusResponse.from_snapshot(snapshot)


@router.get("/{flight_id}/history", response_model=FlightHistoryResponse)
def get_flight_history(
    flight_id: str,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    aeroapi: AeroAPIClient = Depends(get_aeroapi_client),
) -> FlightHistoryResponse:
    snapshot = db.get(FlightSnapshot, flight_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail=f"Unknown flight_id {flight_id}")
    history = flight_history_service.get_history(db, aeroapi, snapshot.ident, limit=limit)
    return FlightHistoryResponse(flight_id=flight_id, **history)


@router.get("/{flight_id}/card.png")
def get_flight_card_image(
    flight_id: str,
    db: Session = Depends(get_db),
    aeroapi: AeroAPIClient = Depends(get_aeroapi_client),
) -> Response:
    """Shareable "card" PNG for casual sharing into a chat app (SC-D3). Re-uses the same cached
    FlightSnapshot the JSON status endpoint serves -- no separate cache, see card_image_service.py.
    """
    snapshot = flight_status_service.get_status(db, aeroapi, flight_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail=f"Unknown flight_id {flight_id}")
    png_bytes = card_image_service.render_card(snapshot)
    headers = {"Cache-Control": "private, max-age=120"}
    return Response(content=png_bytes, media_type="image/png", headers=headers)
