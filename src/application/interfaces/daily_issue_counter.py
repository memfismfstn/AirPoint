from datetime import date
from typing import Protocol


class DailyIssueCounter(Protocol):
    """Счётчик выданных лицензий по московским дням"""

    async def try_reserve(self, day: date, limit: int) -> bool:
        """Атомарно занимает одну из выдач на день"""
        ...
