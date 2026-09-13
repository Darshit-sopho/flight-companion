from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolved relative to this file (backend/app/config.py -> repo root) rather than the process's CWD, so
# `.env` at the repo root is found the same way whether the backend is launched from `backend/` (per the
# quickstart) or from the repo root. Real OS environment variables still take precedence over this file.
_REPO_ROOT_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    """Central app configuration, loaded from environment variables / .env.

    See ../../.env.example for the documented list of every variable this reads.
    """

    model_config = SettingsConfigDict(env_file=str(_REPO_ROOT_ENV_FILE), extra="ignore", case_sensitive=False)

    aeroapi_key: str = ""
    aeroapi_base_url: str = "https://aeroapi.flightaware.com/aeroapi"

    opensky_client_id: str = ""
    opensky_client_secret: str = ""

    database_url: str = "postgresql+psycopg://flightcompanion:flightcompanion@localhost:5432/flightcompanion"

    env: str = "dev"
    # When true, both external API clients are swapped for canned fixture data.
    # Used by the e2e test suite and available for local dev without spending API credit.
    fixture_mode: bool = False

    aeroapi_status_cache_ttl_seconds: int = 600
    aeroapi_history_cache_ttl_seconds: int = 604800
    opensky_min_poll_interval_seconds: int = 8
    # 0 disables the budget guard entirely.
    aeroapi_daily_call_budget: int = 200

    # Open-Meteo is free/unmetered, so this is a freshness choice, not a cost-control one: shorter than
    # Airport's permanent cache (weather changes fast), longer than FlightSnapshot's 5-15 min (a compact
    # glyph doesn't need that freshness).
    airport_weather_cache_ttl_seconds: int = 1800

    cors_allow_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
