"""Raw HTTP wrapper around FlightAware AeroAPI. No caching or business logic lives here — that's the
job of the services layer (see app/services/flight_status_service.py for the cost-control rules this
client's calls are gated behind).

Field-name mapping below is based on AeroAPI v4's documented flight-schedule response shape as of
writing. If FlightAware changes their schema, this is the one place to update — everything downstream
consumes the dict this returns, not the raw AeroAPI response.
"""

from __future__ import annotations

from datetime import date as date_cls
from datetime import timedelta

import httpx

from app.config import get_settings
from app.core.rate_limit import aeroapi_budget


class AeroAPIError(Exception):
    """Base class for AeroAPI client errors."""


class AeroAPINotFoundError(AeroAPIError):
    """Raised when AeroAPI has no data for the requested flight/airport."""


class AeroAPIClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        client: httpx.Client | None = None,
    ):
        settings = get_settings()
        self._api_key = api_key if api_key is not None else settings.aeroapi_key
        self._base_url = base_url or settings.aeroapi_base_url
        self._client = client or httpx.Client(
            base_url=self._base_url, headers={"x-apikey": self._api_key}, timeout=10.0
        )

    def get_flight(self, ident: str, date: str) -> dict:
        """Fetch the flight-instance data for a specific ident on a specific (local) date.

        AeroAPI requires `end` to be strictly later than `start` (a same-day range is rejected with
        400 INVALID_ARGUMENT), so we query the full day: [date 00:00, date+1 00:00).
        """
        aeroapi_budget.record_call()
        start_date = date_cls.fromisoformat(date)
        end_date = start_date + timedelta(days=1)
        response = self._client.get(
            f"/flights/{ident}", params={"start": start_date.isoformat(), "end": end_date.isoformat()}
        )
        if response.status_code == 404:
            raise AeroAPINotFoundError(f"No flight found for {ident} on {date}")
        response.raise_for_status()
        flights = (response.json() or {}).get("flights") or []
        if not flights:
            raise AeroAPINotFoundError(f"No flight found for {ident} on {date}")
        return flights[0]

    def get_flight_by_id(self, fa_flight_id: str) -> dict:
        """Fetch a specific flight instance by AeroAPI's own identifier, used exclusively for the
        diverted-flight case (docs/features/status-card-requirements.md#SC-A4.3): querying by ident+date
        only ever returns the ORIGINALLY FILED record (`diverted: true`, destination = planned airport).
        The actual outcome (`diverted: false, status: "Arrived"`, destination = where it actually landed)
        is a SEPARATE record sharing the same `fa_flight_id`, only retrievable this way.

        Multiple records can share one fa_flight_id; this returns whichever one has real arrival data
        (`actual_on` populated), falling back to a non-diverted record, then to the first result — see
        SC-A4.3 for the confirmed real-world shape this is based on.
        """
        aeroapi_budget.record_call()
        response = self._client.get(f"/flights/{fa_flight_id}")
        if response.status_code == 404:
            raise AeroAPINotFoundError(f"No flight found for fa_flight_id {fa_flight_id}")
        response.raise_for_status()
        flights = (response.json() or {}).get("flights") or []
        if not flights:
            raise AeroAPINotFoundError(f"No flight found for fa_flight_id {fa_flight_id}")
        for flight in flights:
            if flight.get("actual_on"):
                return flight
        for flight in flights:
            if not flight.get("diverted"):
                return flight
        return flights[0]

    def get_flight_history(self, ident: str, limit: int = 10) -> list[dict]:
        """Fetch recent past occurrences of this flight number."""
        aeroapi_budget.record_call()
        response = self._client.get(f"/flights/{ident}")
        response.raise_for_status()
        flights = (response.json() or {}).get("flights") or []
        return flights[:limit]

    def get_airport(self, code: str) -> dict:
        aeroapi_budget.record_call()
        response = self._client.get(f"/airports/{code}")
        if response.status_code == 404:
            raise AeroAPINotFoundError(f"Unknown airport {code}")
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._client.close()
