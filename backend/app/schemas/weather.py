"""Weather response DTOs (docs/features/status-card-requirements.md#SC-D2). Kept separate from
schemas/flight.py — this is airport+time data from Open-Meteo, not flight data derived from AeroAPI.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.services.wmo_weather_codes import WeatherBucket


class WeatherGlyph(BaseModel):
    bucket: WeatherBucket | None
    temp_f: float | None
    at: datetime


class AirportWeatherResponse(BaseModel):
    code: str
    now: WeatherGlyph
    # None when no cached hourly entry falls within 3 hours of the requested target time (e.g. a
    # far-future flight date beyond Open-Meteo's forecast horizon) — see weather_service.py.
    outlook: WeatherGlyph | None
