from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.clients.aeroapi_client import AeroAPIClient
from app.db.session import get_db
from app.dependencies import get_aeroapi_client
from app.schemas.flight import AirportResponse
from app.services import airport_service

router = APIRouter(prefix="/api/airports", tags=["airports"])


@router.get("/{code}", response_model=AirportResponse)
def get_airport(
    code: str,
    db: Session = Depends(get_db),
    aeroapi: AeroAPIClient = Depends(get_aeroapi_client),
) -> AirportResponse:
    airport = airport_service.get_airport(db, aeroapi, code)
    if airport is None:
        raise HTTPException(status_code=404, detail=f"Unknown airport {code}")
    return AirportResponse.from_model(airport)
