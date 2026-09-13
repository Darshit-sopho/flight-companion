from unittest.mock import MagicMock

from sqlalchemy.exc import IntegrityError

from app.clients.aeroapi_client import AeroAPINotFoundError
from app.db.models import Airport
from app.services import airport_service


def test_returns_cached_row_without_calling_aeroapi(sqlite_session):
    airport = Airport(code="SFO", name="San Francisco International Airport", lat=37.6213, lon=-122.379)
    sqlite_session.add(airport)
    sqlite_session.commit()
    aeroapi = MagicMock()

    result = airport_service.get_airport(sqlite_session, aeroapi, "SFO")

    assert result.code == "SFO"
    aeroapi.get_airport.assert_not_called()


def test_fetches_and_caches_on_first_lookup(sqlite_session):
    aeroapi = MagicMock()
    aeroapi.get_airport.return_value = {
        "name": "O'Hare International Airport",
        "city": "Chicago",
        "country_code": "US",
        "latitude": 41.9742,
        "longitude": -87.9073,
        "timezone": "America/Chicago",
    }

    result = airport_service.get_airport(sqlite_session, aeroapi, "ord")

    assert result.code == "ORD"
    assert result.city == "Chicago"
    assert sqlite_session.get(Airport, "ORD") is not None


def test_returns_none_for_unknown_airport(sqlite_session):
    aeroapi = MagicMock()
    aeroapi.get_airport.side_effect = AeroAPINotFoundError("unknown")

    result = airport_service.get_airport(sqlite_session, aeroapi, "ZZZ")

    assert result is None


def test_falls_back_to_the_winning_row_when_a_concurrent_lookup_wins_the_insert_race():
    """Two requests can both see no cached row for a never-before-looked-up airport and race to insert
    it -- e.g. the status card's plain airport-info fetch and its weather fetch (SC-D2) now resolve the
    same airport concurrently. The loser must not error; it should just return what the winner wrote.
    """
    winning_row = Airport(code="ZZZ", name="Winner", city="City")
    db = MagicMock()
    db.get.side_effect = [None, winning_row]
    db.commit.side_effect = IntegrityError("insert", {}, Exception("duplicate key"))
    aeroapi = MagicMock()
    aeroapi.get_airport.return_value = {"name": "Loser", "city": "City"}

    result = airport_service.get_airport(db, aeroapi, "zzz")

    assert result is winning_row
    db.rollback.assert_called_once()
