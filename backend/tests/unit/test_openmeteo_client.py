from unittest.mock import MagicMock

from app.clients.openmeteo_client import OpenMeteoClient


def _make_response(payload: dict) -> MagicMock:
    response = MagicMock()
    response.json.return_value = payload
    return response


def _make_client(payload: dict) -> OpenMeteoClient:
    http_client = MagicMock()
    http_client.get.return_value = _make_response(payload)
    return OpenMeteoClient(client=http_client)


def test_requests_fahrenheit_and_seven_day_utc_forecast():
    http_client = MagicMock()
    http_client.get.return_value = _make_response(
        {"current": {}, "hourly": {"time": [], "temperature_2m": [], "weather_code": []}}
    )
    client = OpenMeteoClient(client=http_client)

    client.get_forecast(37.6213, -122.379)

    args, kwargs = http_client.get.call_args
    assert kwargs["params"]["latitude"] == 37.6213
    assert kwargs["params"]["longitude"] == -122.379
    assert kwargs["params"]["temperature_unit"] == "fahrenheit"
    assert kwargs["params"]["forecast_days"] == 7
    assert kwargs["params"]["timezone"] == "UTC"


def test_normalizes_current_conditions():
    client = _make_client(
        {
            "current": {"time": "2026-09-12T14:00", "temperature_2m": 68.0, "weather_code": 2},
            "hourly": {"time": [], "temperature_2m": [], "weather_code": []},
        }
    )

    result = client.get_forecast(0, 0)

    assert result["current"] == {"time": "2026-09-12T14:00", "temp_f": 68.0, "weather_code": 2}


def test_normalizes_parallel_hourly_arrays_into_list_of_dicts():
    client = _make_client(
        {
            "current": {},
            "hourly": {
                "time": ["2026-09-12T14:00", "2026-09-12T15:00"],
                "temperature_2m": [68.0, 70.0],
                "weather_code": [2, 3],
            },
        }
    )

    result = client.get_forecast(0, 0)

    assert result["hourly"] == [
        {"time": "2026-09-12T14:00", "temp_f": 68.0, "weather_code": 2},
        {"time": "2026-09-12T15:00", "temp_f": 70.0, "weather_code": 3},
    ]


def test_missing_current_or_hourly_blocks_do_not_raise():
    client = _make_client({})

    result = client.get_forecast(0, 0)

    assert result == {"current": {"time": None, "temp_f": None, "weather_code": None}, "hourly": []}
