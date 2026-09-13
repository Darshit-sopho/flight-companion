import pytest

from app.services.wmo_weather_codes import bucket_for_wmo_code

_EXPECTED_BUCKETS = {
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


@pytest.mark.parametrize("code,expected_bucket", sorted(_EXPECTED_BUCKETS.items()))
def test_every_known_wmo_code_maps_to_exactly_one_bucket(code, expected_bucket):
    assert bucket_for_wmo_code(code) == expected_bucket


def test_unknown_code_returns_none():
    assert bucket_for_wmo_code(12345) is None


def test_missing_code_returns_none():
    assert bucket_for_wmo_code(None) is None
