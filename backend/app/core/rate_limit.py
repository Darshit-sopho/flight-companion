"""Dev-time safety net against runaway AeroAPI usage — NOT a production billing/quota system.

AeroAPI is billed per query (see docs/DATA_SOURCES.md#cost-control). This in-process daily counter
exists to catch bugs (an accidental polling loop, a test that forgot to mock the client) during local
development before they burn through the free-tier credit. It resets when the process restarts, which is
fine for its purpose.
"""

from __future__ import annotations

from datetime import date

from app.config import get_settings


class AeroAPIBudgetExceeded(Exception):
    pass


class _DailyCallBudget:
    def __init__(self) -> None:
        self._day: date | None = None
        self._count = 0

    def record_call(self) -> None:
        settings = get_settings()
        today = date.today()
        if self._day != today:
            self._day = today
            self._count = 0
        self._count += 1
        budget = settings.aeroapi_daily_call_budget
        if budget and self._count > budget:
            raise AeroAPIBudgetExceeded(
                f"AeroAPI daily call budget ({budget}) exceeded — see docs/DATA_SOURCES.md#cost-control"
            )

    @property
    def count_today(self) -> int:
        return self._count if self._day == date.today() else 0

    def reset(self) -> None:
        """Test helper — production code should never need to call this."""
        self._day = None
        self._count = 0


aeroapi_budget = _DailyCallBudget()
