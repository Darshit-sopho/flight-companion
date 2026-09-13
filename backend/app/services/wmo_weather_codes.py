"""Maps Open-Meteo's ~30 WMO weather codes down to a small set of icon buckets for the compact weather
glyph (docs/features/status-card-requirements.md#SC-D2). Kept server-side so the frontend never needs
its own copy of this table — the API returns a bucket name, not a raw code.
"""

from __future__ import annotations

from typing import Literal

WeatherBucket = Literal["clear", "partly_cloudy", "overcast", "fog", "rain", "snow", "thunderstorm"]

# See https://open-meteo.com/en/docs#weathervariables for the full WMO code table.
_BUCKET_BY_CODE: dict[int, WeatherBucket] = {
    0: "clear",
    1: "partly_cloudy",
    2: "partly_cloudy",
    3: "overcast",
    45: "fog",
    48: "fog",
    51: "rain",
    53: "rain",
    55: "rain",
    56: "rain",
    57: "rain",
    61: "rain",
    63: "rain",
    65: "rain",
    66: "rain",
    67: "rain",
    80: "rain",
    81: "rain",
    82: "rain",
    71: "snow",
    73: "snow",
    75: "snow",
    77: "snow",
    85: "snow",
    86: "snow",
    95: "thunderstorm",
    96: "thunderstorm",
    99: "thunderstorm",
}


def bucket_for_wmo_code(code: int | None) -> WeatherBucket | None:
    if code is None:
        return None
    return _BUCKET_BY_CODE.get(code)
