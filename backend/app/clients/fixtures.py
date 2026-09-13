"""Canned-data stand-ins for AeroAPIClient/OpenSkyClient, used when FIXTURE_MODE=true.

Purpose: let the e2e suite (and local dev) exercise the full app without spending real AeroAPI credit or
depending on a real flight being airborne. See docs/TESTING.md#layer-4-end-to-end-workflow-tests.

Three demo flights are recognized, by ident:
  FIX100  — an "active" (airborne) flight with a moving live position and a rich history.
  FIX200  — a "landed" flight, to exercise the non-tracking UI states.
  FIX300  — a "diverted" flight (ORD -> DEN, diverted to LAS), matching the real two-record AeroAPI
            shape confirmed in docs/features/status-card-requirements.md#SC-A4.3.
Any other ident raises AeroAPINotFoundError, same as the real client would for an unknown flight — this
is deliberate so the "flight not found" path is exercisable in fixture mode / e2e tests too.
"""

from __future__ import annotations

from datetime import date, timedelta

from app.clients.aeroapi_client import AeroAPINotFoundError

_LANDED_IDENTS = {"FIX200"}
_DIVERTED_IDENTS = {"FIX300"}
_KNOWN_IDENTS = {"FIX100", "FIX200", "FIX300"}

_AIRPORTS = {
    "SFO": {
        "code": "SFO",
        "code_iata": "SFO",
        "name": "San Francisco International Airport",
        "city": "San Francisco",
        "country_code": "US",
        "latitude": 37.6213,
        "longitude": -122.379,
        "timezone": "America/Los_Angeles",
    },
    "ORD": {
        "code": "ORD",
        "code_iata": "ORD",
        "name": "O'Hare International Airport",
        "city": "Chicago",
        "country_code": "US",
        "latitude": 41.9742,
        "longitude": -87.9073,
        "timezone": "America/Chicago",
    },
    "DEN": {
        "code": "DEN",
        "code_iata": "DEN",
        "name": "Denver International Airport",
        "city": "Denver",
        "country_code": "US",
        "latitude": 39.8561,
        "longitude": -104.6737,
        "timezone": "America/Denver",
    },
    "LAS": {
        "code": "LAS",
        "code_iata": "LAS",
        "name": "Harry Reid International Airport",
        "city": "Las Vegas",
        "country_code": "US",
        "latitude": 36.084,
        "longitude": -115.1537,
        "timezone": "America/Los_Angeles",
    },
}


def _airport_ref(code: str) -> dict:
    a = _AIRPORTS[code]
    return {
        "code": a["code"],
        "code_iata": a["code_iata"],
        "name": a["name"],
        "city": a["city"],
        "timezone": a["timezone"],
    }


class FixtureAeroAPIClient:
    def get_flight(self, ident: str, date_str: str) -> dict:
        ident = ident.upper()
        if ident not in _KNOWN_IDENTS:
            raise AeroAPINotFoundError(f"No fixture flight for {ident} on {date_str}")

        if ident in _DIVERTED_IDENTS:
            return self._diverted_flight(ident, date_str)

        landed = ident in _LANDED_IDENTS
        base = {
            "ident": ident,
            "fa_flight_id": f"{ident}-fixture-fa-id",
            "operator": "SWO",
            "operator_icao": "SWO",
            "operator_iata": "S1",
            "ident_icao": ident,
            "diverted": False,
            "origin": _airport_ref("SFO"),
            "destination": _airport_ref("ORD"),
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
            "progress_percent": 35 if not landed else 100,
            "filed_ete": 19800,  # 5.5 hours, in seconds
            "route_distance": 1846,
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

    def _diverted_flight(self, ident: str, date_str: str) -> dict:
        """The record returned by the normal ident+date search — matches the real shape confirmed in
        SC-A4.3: `diverted: true`, destination is the ORIGINALLY FILED airport, no actual arrival data.
        """
        return {
            "ident": ident,
            "fa_flight_id": f"{ident}-fixture-fa-id",
            "operator": "SWO",
            "operator_icao": "SWO",
            "operator_iata": "S1",
            "ident_icao": ident,
            "diverted": True,
            "status": "Diverted",
            "origin": _airport_ref("ORD"),
            "destination": _airport_ref("DEN"),
            "registration": "N54321",
            "aircraft_type": "A320",
            "scheduled_out": f"{date_str}T09:00:00Z",
            "estimated_out": f"{date_str}T09:00:00Z",
            "actual_out": f"{date_str}T09:05:00Z",
            "scheduled_in": f"{date_str}T11:15:00Z",
            "estimated_in": None,
            "actual_in": None,
            "gate_origin": "C10",
            "terminal_origin": "1",
            "gate_destination": None,
            "terminal_destination": None,
            "progress_percent": 100,
            "filed_ete": 8100,
            "route_distance": 888,
        }

    def get_flight_by_id(self, fa_flight_id: str) -> dict:
        """The SECOND record for a diverted flight (see SC-A4.3) — only returned for the fa_flight_id of
        a fixture-diverted flight; matches the "actual outcome" shape (diverted: false, status: Arrived,
        destination = where it actually landed, real actual_off/actual_on times).
        """
        for ident in _DIVERTED_IDENTS:
            if fa_flight_id == f"{ident}-fixture-fa-id":
                return {
                    "ident": ident,
                    "fa_flight_id": fa_flight_id,
                    "operator": "SWO",
                    "operator_icao": "SWO",
                    "operator_iata": "S1",
                    "diverted": False,
                    "status": "Arrived",
                    "origin": _airport_ref("ORD"),
                    "destination": _airport_ref("LAS"),
                    "registration": "N54321",
                    "aircraft_type": "A320",
                    "scheduled_out": None,
                    "estimated_out": None,
                    "actual_out": None,
                    "scheduled_in": None,
                    "estimated_in": None,
                    "actual_in": f"{date.today().isoformat()}T10:52:00Z",
                    "gate_origin": None,
                    "terminal_origin": None,
                    "gate_destination": "D4",
                    "terminal_destination": None,
                }
        raise AeroAPINotFoundError(f"No fixture flight for fa_flight_id {fa_flight_id}")

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
        code = code.upper()
        if code not in _AIRPORTS:
            raise AeroAPINotFoundError(f"Unknown fixture airport {code}")
        a = _AIRPORTS[code]
        return {
            "name": a["name"],
            "city": a["city"],
            "country_code": a["country_code"],
            "latitude": a["latitude"],
            "longitude": a["longitude"],
            "timezone": a["timezone"],
        }

    def close(self) -> None:
        pass


class FixtureOpenMeteoClient:
    """Returns one fixed, deterministic forecast regardless of lat/lon input -- fixture mode doesn't need
    per-airport variation, just a stable shape to render against (see StatusTimelineCard's weather row).
    """

    def get_forecast(self, lat: float, lon: float) -> dict:
        today = date.today()
        return {
            "current": {"time": f"{today.isoformat()}T12:00", "temp_f": 68.0, "weather_code": 2},
            "hourly": [
                {"time": f"{today.isoformat()}T{hour:02d}:00", "temp_f": 60.0 + hour, "weather_code": 2}
                for hour in range(24)
            ]
            + [
                {
                    "time": f"{(today + timedelta(days=1)).isoformat()}T{hour:02d}:00",
                    "temp_f": 60.0 + hour,
                    "weather_code": 2,
                }
                for hour in range(24)
            ],
        }

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
