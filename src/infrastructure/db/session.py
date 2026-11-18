from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine


def _py_lower(value: str | None) -> str | None:
    """Приводит строку к нижнему регистру по правилам Python (в том числе кириллицу)"""
    return None if value is None else value.lower()


def _on_connect(dbapi_connection: Any, connection_record: Any) -> None:
    """Настраивает каждое новое соединение SQLite"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
    dbapi_connection.create_function("lower", 1, _py_lower, deterministic=True)


def build_engine(database_url: str, *, echo: bool = False, **kwargs: Any) -> AsyncEngine:
    """Создаёт асинхронный движок"""
    engine = create_async_engine(database_url, echo=echo, **kwargs)
    if engine.dialect.name == "sqlite":
        event.listen(engine.sync_engine, "connect", _on_connect)
    return engine


def build_session_factory(engine: AsyncEngine) -> async_sessionmaker:
    """Создаёт фабрику сессий"""
    return async_sessionmaker(engine, expire_on_commit=False)
