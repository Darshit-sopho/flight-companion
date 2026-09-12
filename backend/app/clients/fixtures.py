"""Canned-data stand-ins for AeroAPIClient/OpenSkyClient, used when FIXTURE_MODE=true.

Purpose: let the e2e suite (and local dev) exercise the full app without spending real AeroAPI credit or
depending on a real flight being airborne. See docs/TESTING.md#layer-4-end-to-end-workflow-tests.

Exactly two demo flights are recognized, by ident:
  FIX100  — an "active" (airborne) flight with a moving live position and a rich history.
  FIX200  — a "landed" flight, to exercise the non-tracking UI states.
Any other ident raises AeroAPINotFoundError, same as the real client would for an unknown flight — this
is deliberate so the "flight not found" path is exercisable in fixture mode / e2e tests too.
"""

from __future__ import annotations

from datetime import date, timedelta

from app.clients.aeroapi_client import AeroAPINotFoundError

_LANDED_IDENTS = {"FIX200"}
_KNOWN_IDENTS = {"FIX100", "FIX200"}


class FixtureAeroAPIClient:
    def get_flight(self, ident: str, date_str: str) -> dict:
        ident = ident.upper()
        if ident not in _KNOWN_IDENTS:
            raise AeroAPINotFoundError(f"No fixture flight for {ident} on {date_str}")
        landed = ident in _LANDED_IDENTS
        base = {
            "ident": ident,
            "origin": {"code": "SFO"},
            "destination": {"code": "ORD"},
            "registration": "N12345",
            "aircraft_type": "B738",
            "scheduled_out": f"{date_str}T14:30:00Z",
            "estimated_out": f"{date_str}T14:45:00Z",
            "actual_out": f"{date_str}T14:47:00Z",
            "scheduled_in": f"{date_str}T20:10:00Z",
            "gate_origin": "A12",
            "terminal_origin": "2",
            "gate_destination": "B4",
            "terminal_destination": "1",
        }
        if landed:
            base.update(
                {
                    "status": "landed",
                    "estimated_in": f"{date_str}T20:22:00Z",
                    "actual_in": f"{date_str}T20:25:00Z",
                }
            )
        else:
            base.update(
                {
                    "status": "active",
                    "estimated_in": f"{date_str}T20:22:00Z",
                    "actual_in": None,
                }
            )
        return base

    def get_flight_history(self, ident: str, limit: int = 10) -> list[dict]:
        today = date.today()
        history = []
        for i in range(1, limit + 1):
            d = today - timedelta(days=7 * i)
            delay = 5 if i % 3 else 35
            total_minutes = 30 + delay
            hour, minute = 14 + total_minutes // 60, total_minutes % 60
            history.append(
                {
                    "origin": {"code": "SFO"},
                    "destination": {"code": "ORD"},
                    "scheduled_out": f"{d.isoformat()}T14:30:00Z",
                    "actual_out": f"{d.isoformat()}T{hour:02d}:{minute:02d}:00Z",
                }
            )
        return history

    def get_airport(self, code: str) -> dict:
        airports = {
            "SFO": {
                "name": "San Francisco International Airport",
                "city": "San Francisco",
                "country_code": "US",
                "latitude": 37.6213,
                "longitude": -122.379,
                "timezone": "America/Los_Angeles",
            },
            "ORD": {
                "name": "O'Hare International Airport",
                "city": "Chicago",
                "country_code": "US",
                "latitude": 41.9742,
                "longitude": -87.9073,
                "timezone": "America/Chicago",
            },
        }
        code = code.upper()
        if code not in airports:
            raise AeroAPINotFoundError(f"Unknown fixture airport {code}")
        return airports[code]

    def close(self) -> None:
        pass


class FixtureOpenSkyClient:
    """Simulates gentle eastward movement each time get_states is polled, so e2e tests can assert the
    map position actually changes across polling cycles.
    """

    _START_LAT = 40.5
    _START_LON = -95.0

    def __init__(self) -> None:
        self._poll_count = 0

    def get_states(self, icao24: str) -> dict | None:
        self._poll_count += 1
        return {
            "icao24": icao24,
            "callsign": "FIX100",
            "longitude": self._START_LON + self._poll_count * 0.5,
            "latitude": self._START_LAT + self._poll_count * 0.1,
            "baro_altitude": 10363.2,  # ~34,000 ft in meters
            "on_ground": False,
            "velocity": 247.0,  # ~480 kt in m/s
            "true_track": 92.0,
            "geo_altitude": 10363.2,
        }

    def find_state_by_callsigns(self, callsigns: list[str]) -> dict | None:
        return self.get_states("a1b2c3")

    def close(self) -> None:
        pass
