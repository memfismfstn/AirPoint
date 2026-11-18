from fastapi import FastAPI

from src.application.interfaces import Clock, UnitOfWork
from src.infrastructure.clock import SystemClock
from src.infrastructure.config import settings
from src.infrastructure.db.session import build_engine, build_session_factory
from src.infrastructure.uow import SqlAlchemyUnitOfWork
from src.presentation.api.dependencies import get_clock, get_uow
from src.presentation.api.routers import api_router

app = FastAPI(title=settings.app_title, version=settings.app_version, docs_url=settings.docs_url)

engine = build_engine(settings.database_url, echo=settings.sql_echo)
session_factory = build_session_factory(engine)


def provide_uow() -> UnitOfWork:
    """Единица работы на SQLAlchemy для каждого запроса"""
    return SqlAlchemyUnitOfWork(session_factory)


def provide_clock() -> Clock:
    """Системные часы"""
    return SystemClock()


app.dependency_overrides[get_uow] = provide_uow
app.dependency_overrides[get_clock] = provide_clock
app.include_router(api_router)
