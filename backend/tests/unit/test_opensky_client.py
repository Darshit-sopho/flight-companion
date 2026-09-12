from app.clients.opensky_client import parse_state_vector

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
