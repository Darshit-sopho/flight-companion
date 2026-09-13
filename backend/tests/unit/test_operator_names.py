from app.services.operator_names import get_operator_name


def test_known_icao_code_returns_friendly_name():
    assert get_operator_name("UAL") == "United Airlines"
    assert get_operator_name("RPA") == "Republic Airways"


def test_lookup_is_case_insensitive_and_strips_whitespace():
    assert get_operator_name("ual") == "United Airlines"
    assert get_operator_name(" UAL ") == "United Airlines"


def test_unknown_code_returns_none_gracefully():
    assert get_operator_name("ZZZ") is None


def test_missing_code_returns_none():
    assert get_operator_name(None) is None
    assert get_operator_name("") is None
