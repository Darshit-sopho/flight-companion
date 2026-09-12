from unittest.mock import MagicMock

from app.clients.opensky_client import OpenSkyClient, parse_state_vector

_RAW_STATE = [
    "a1b2c3",  # icao24
    "UAL123  ",  # callsign (padded, as OpenSky returns it)
    "United States",
    1700000000,
    1700000005,
    -87.9048,  # longitude
    41.9786,  # latitude
    10363.2,  # baro_altitude
    False,  # on_ground
    123.5,  # velocity
    92.0,  # true_track
    0.0,
    None,
    10400.0,  # geo_altitude
    "1200",
    False,
    0,
]


def test_parse_state_vector_extracts_expected_fields():
    parsed = parse_state_vector(_RAW_STATE)

    assert parsed["icao24"] == "a1b2c3"
    assert parsed["callsign"] == "UAL123"  # whitespace stripped
    assert parsed["longitude"] == -87.9048
    assert parsed["latitude"] == 41.9786
    assert parsed["on_ground"] is False
    assert parsed["true_track"] == 92.0


def _make_states_response(states: list) -> MagicMock:
    response = MagicMock()
    response.json.return_value = {"states": states}
    return response


def test_find_state_by_callsigns_matches_any_candidate_in_a_single_request():
    http_client = MagicMock()
    http_client.get.return_value = _make_states_response([_RAW_STATE])
    client = OpenSkyClient(client_id=None, client_secret=None, client=http_client)

    # "UA3513" (marketing ident) doesn't match, but "UAL123" (this state's actual callsign) does —
    # both must be checked in the same call, matching the codeshare fallback use case.
    result = client.find_state_by_callsigns(["UA3513", "UAL123"])

    assert result is not None
    assert result["icao24"] == "a1b2c3"
    http_client.get.assert_called_once()


def test_find_state_by_callsigns_returns_none_without_a_request_when_all_candidates_are_blank():
    http_client = MagicMock()
    client = OpenSkyClient(client_id=None, client_secret=None, client=http_client)

    result = client.find_state_by_callsigns(["", "   "])

    assert result is None
    http_client.get.assert_not_called()


def test_find_state_by_callsigns_returns_none_when_no_candidate_matches():
    http_client = MagicMock()
    http_client.get.return_value = _make_states_response([_RAW_STATE])
    client = OpenSkyClient(client_id=None, client_secret=None, client=http_client)

    result = client.find_state_by_callsigns(["ZZZ999"])

    assert result is None
