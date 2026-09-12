import pytest

from app.config import get_settings
from app.core.rate_limit import AeroAPIBudgetExceeded, _DailyCallBudget


def test_allows_calls_under_budget():
    budget = _DailyCallBudget()
    for _ in range(5):
        budget.record_call()
    assert budget.count_today == 5


def test_raises_once_budget_exceeded(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("AEROAPI_DAILY_CALL_BUDGET", "2")
    get_settings.cache_clear()
    try:
        budget = _DailyCallBudget()
        budget.record_call()
        budget.record_call()
        with pytest.raises(AeroAPIBudgetExceeded):
            budget.record_call()
    finally:
        monkeypatch.delenv("AEROAPI_DAILY_CALL_BUDGET", raising=False)
        get_settings.cache_clear()


def test_zero_budget_disables_guard(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("AEROAPI_DAILY_CALL_BUDGET", "0")
    get_settings.cache_clear()
    try:
        budget = _DailyCallBudget()
        for _ in range(50):
            budget.record_call()
        assert budget.count_today == 50
    finally:
        monkeypatch.delenv("AEROAPI_DAILY_CALL_BUDGET", raising=False)
        get_settings.cache_clear()
