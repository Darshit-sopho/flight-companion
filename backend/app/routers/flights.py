from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.clients.aeroapi_client import AeroAPIClient, AeroAPINotFoundError
from app.db.models import FlightSnapshot
from app.db.session import get_db
from app.dependencies import get_aeroapi_client
from app.schemas.flight import FlightHistoryResponse, FlightSearchResponse, FlightStatusResponse
from app.services import flight_history_service, flight_lookup_service, flight_status_service

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
