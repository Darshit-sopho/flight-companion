from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.clients.aeroapi_client import AeroAPIClient
from app.clients.openmeteo_client import OpenMeteoClient
from app.db.session import get_db
from app.dependencies import get_aeroapi_client, get_openmeteo_client
from app.schemas.flight import AirportResponse
from app.schemas.weather import AirportWeatherResponse
from app.services import airport_service, weather_service

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


@router.get("/{code}/weather", response_model=AirportWeatherResponse)
def get_airport_weather(
    code: str,
    at: datetime | None = Query(None),
    db: Session = Depends(get_db),
    aeroapi: AeroAPIClient = Depends(get_aeroapi_client),
    openmeteo: OpenMeteoClient = Depends(get_openmeteo_client),
) -> AirportWeatherResponse:
    airport = airport_service.get_airport(db, aeroapi, code)
    if airport is None:
        raise HTTPException(status_code=404, detail=f"Unknown airport {code}")
    result = weather_service.get_airport_weather(db, openmeteo, airport, at=at)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No known coordinates for airport {code}")
    return result
