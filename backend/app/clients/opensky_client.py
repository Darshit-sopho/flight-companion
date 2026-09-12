"""Raw HTTP wrapper around the OpenSky Network REST API. Handles OAuth2 client-credentials auth and
parses the raw state-vector array format into a dict. No caching/business logic here — see
app/services/live_tracking_service.py and app/services/icao24_resolver.py for that.
"""

from __future__ import annotations

import time

import httpx

from app.config import get_settings

TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
STATES_URL = "https://opensky-network.org/api/states/all"

# Index positions in OpenSky's raw state-vector array. See
# https://openskynetwork.github.io/opensky-api/rest.html#response
_ICAO24 = 0
_CALLSIGN = 1
_LONGITUDE = 5
_LATITUDE = 6
_BARO_ALTITUDE = 7
_ON_GROUND = 8
_VELOCITY = 9
_TRUE_TRACK = 10
_GEO_ALTITUDE = 13


def parse_state_vector(state: list) -> dict:
    return {
        "icao24": state[_ICAO24],
        "callsign": (state[_CALLSIGN] or "").strip(),
        "longitude": state[_LONGITUDE],
        "latitude": state[_LATITUDE],
        "baro_altitude": state[_BARO_ALTITUDE],
        "on_ground": bool(state[_ON_GROUND]),
        "velocity": state[_VELOCITY],
        "true_track": state[_TRUE_TRACK],
        "geo_altitude": state[_GEO_ALTITUDE],
    }


class OpenSkyClient:
    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        client: httpx.Client | None = None,
    ):
        settings = get_settings()
        self._client_id = client_id if client_id is not None else settings.opensky_client_id
        self._client_secret = client_secret if client_secret is not None else settings.opensky_client_secret
        self._client = client or httpx.Client(timeout=10.0)
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    def _get_token(self) -> str | None:
        """Anonymous access is allowed (with much lower rate limits) — skip auth if no creds configured."""
        if not self._client_id or not self._client_secret:
            return None
        if self._token and time.time() < self._token_expires_at - 30:
            return self._token

        response = self._client.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
        )
        response.raise_for_status()
        payload = response.json()
        self._token = payload["access_token"]
        self._token_expires_at = time.time() + payload.get("expires_in", 1800)
        return self._token

    def _auth_headers(self) -> dict:
        token = self._get_token()
        return {"Authorization": f"Bearer {token}"} if token else {}

    def get_states(self, icao24: str) -> dict | None:
        """Latest known state for a specific aircraft, or None if it has no current state vector."""
        response = self._client.get(
            STATES_URL, params={"icao24": icao24.lower()}, headers=self._auth_headers()
        )
        response.raise_for_status()
        states = (response.json() or {}).get("states") or []
        return parse_state_vector(states[0]) if states else None

    def find_state_by_callsigns(self, callsigns: list[str]) -> dict | None:
        """Fallback lookup used by icao24_resolver when registration-based resolution fails.

        Scans all current state vectors ONCE for a match against any of the given candidate callsigns
        (e.g. both a codeshare's marketing and operating idents) — deliberately not one `/states/all`
        fetch per candidate, since that's a full-table sweep each time and candidates are checked
        against the exact same snapshot of live states anyway. Noisier than the icao24 lookup (callsigns
        aren't always populated), so callers should treat a match here as lower-confidence.
        """
        normalized_candidates = {c.strip().upper() for c in callsigns if c and c.strip()}
        if not normalized_candidates:
            return None
        response = self._client.get(STATES_URL, headers=self._auth_headers())
        response.raise_for_status()
        for state in (response.json() or {}).get("states") or []:
            if (state[_CALLSIGN] or "").strip().upper() in normalized_candidates:
                return parse_state_vector(state)
        return None

    def close(self) -> None:
        self._client.close()
