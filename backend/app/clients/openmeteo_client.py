"""Raw HTTP wrapper around Open-Meteo's forecast API. No caching/business logic here — that's
app/services/weather_service.py. Unlike AeroAPI/OpenSky, this needs no API key/auth and has no
per-query cost (docs/DATA_SOURCES.md#open-meteo), so there's no call-budget guard here.
"""

from __future__ import annotations

import httpx

BASE_URL = "https://api.open-meteo.com/v1/forecast"


class OpenMeteoClient:
    def __init__(self, client: httpx.Client | None = None):
        self._client = client or httpx.Client(timeout=10.0)

    def get_forecast(self, lat: float, lon: float) -> dict:
        """Current conditions plus a 7-day hourly forecast for one airport's coordinates.

        Requesting the full 7 days in one call (rather than re-fetching per lookup) means the
        "nearest hour to this leg's scheduled/estimated time" calculation in weather_service can be
        redone cheaply from the same cached payload whenever AeroAPI revises those times, without a
        second Open-Meteo call. `timezone=UTC` keeps every returned timestamp directly comparable to
        this app's UTC-aware datetimes with no conversion.
        """
        response = self._client.get(
            BASE_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,weather_code",
                "hourly": "temperature_2m,weather_code",
                "forecast_days": 7,
                "temperature_unit": "fahrenheit",
                "timezone": "UTC",
            },
        )
        response.raise_for_status()
        raw = response.json()

        current = raw.get("current") or {}
        hourly = raw.get("hourly") or {}
        hourly_times = hourly.get("time") or []
        hourly_temps = hourly.get("temperature_2m") or []
        hourly_codes = hourly.get("weather_code") or []

        return {
            "current": {
                "time": current.get("time"),
                "temp_f": current.get("temperature_2m"),
                "weather_code": current.get("weather_code"),
            },
            "hourly": [
                {"time": t, "temp_f": temp, "weather_code": code}
                for t, temp, code in zip(hourly_times, hourly_temps, hourly_codes, strict=False)
            ],
        }

    def close(self) -> None:
        self._client.close()
