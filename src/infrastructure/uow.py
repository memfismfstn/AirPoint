from types import TracebackType
from typing import Self

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.infrastructure.repositories.customers import SqlCustomerRepository
from src.infrastructure.repositories.daily_counter import SqlDailyIssueCounter
from src.infrastructure.repositories.drones import SqlDroneRepository
from src.infrastructure.repositories.licenses import SqlLicenseRepository
from src.infrastructure.repositories.parts import SqlPartRepository


class SqlAlchemyUnitOfWork:
    """Реализация порта `UnitOfWork`"""

    customers: SqlCustomerRepository
    licenses: SqlLicenseRepository
    drones: SqlDroneRepository
    parts: SqlPartRepository
    issue_counter: SqlDailyIssueCounter

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """Создаёт единицу работы"""
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> Self:
        """Открывает сессию и создаёт репозитории"""
        self._session = self._session_factory()
        self.customers = SqlCustomerRepository(self._session)
        self.licenses = SqlLicenseRepository(self._session)
        self.drones = SqlDroneRepository(self._session)
        self.parts = SqlPartRepository(self._session)
        self.issue_counter = SqlDailyIssueCounter(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Откатывает незафиксированное и закрывает сессию"""
        session = self._require_session()
        try:
            await session.rollback()
        finally:
            await session.close()

    async def begin_write(self) -> None:
        """Начинает транзакцию записи, сразу занимая право писать"""
        session = self._require_session()
        if session.get_bind().dialect.name == "sqlite":
            await session.execute(text("BEGIN IMMEDIATE"))

    async def commit(self) -> None:
        """Фиксирует транзакцию"""
        await self._require_session().commit()

    def _require_session(self) -> AsyncSession:
        """Возвращает открытую сессию"""
        if self._session is None:
            raise RuntimeError("UnitOfWork нужно использовать через `async with`")
        return self._session
