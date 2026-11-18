from datetime import date

from sqlalchemy import update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db.models import LicenseDailyCounterOrm


class SqlDailyIssueCounter:
    """Дневной счётчик выдач в SQL-базе"""

    def __init__(self, session: AsyncSession) -> None:
        """Создаёт счётчик в рамках сессии единицы работы"""
        self._session = session

    async def try_reserve(self, day: date, limit: int) -> bool:
        """Атомарно занимает одну из выдач на день"""
        await self._session.execute(
            sqlite_insert(LicenseDailyCounterOrm).values(day=day, issued=0).on_conflict_do_nothing()
        )
        result = await self._session.execute(
            update(LicenseDailyCounterOrm)
            .where(LicenseDailyCounterOrm.day == day, LicenseDailyCounterOrm.issued < limit)
            .values(issued=LicenseDailyCounterOrm.issued + 1)
        )
        return result.rowcount > 0
