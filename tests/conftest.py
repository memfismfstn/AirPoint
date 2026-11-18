from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.infrastructure.db.base import Base
from src.infrastructure.db.session import build_engine, build_session_factory
from src.infrastructure.uow import SqlAlchemyUnitOfWork
from src.main import app
from src.presentation.api.dependencies import get_clock, get_uow


class Clock:
    """Управляемые часы: реализуют порт `Clock` и стоят там, где в проде SystemClock"""

    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now

    def set(self, *args: int) -> None:
        self._now = datetime(*args, tzinfo=UTC)


@pytest.fixture
def clock() -> Clock:
    return Clock(datetime(2026, 11, 3, 9, 0, tzinfo=UTC))


@pytest.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = build_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield build_session_factory(engine)
    await engine.dispose()


@pytest.fixture
async def session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as db_session:
        yield db_session


@pytest.fixture
async def client(
    session_factory: async_sessionmaker[AsyncSession], clock: Clock
) -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_uow] = lambda: SqlAlchemyUnitOfWork(session_factory)
    app.dependency_overrides[get_clock] = lambda: clock
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
        yield http_client
    app.dependency_overrides.clear()
