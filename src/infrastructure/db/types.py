from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator[datetime]):
    """Момент времени, который всегда хранится в UTC и всегда читается как aware"""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        """Приводит значение к UTC перед записью в базу"""
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Нужен datetime с часовым поясом")
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        """Возвращает tzinfo=UTC значению, прочитанному из базы"""
        if value is None:
            return None
        return value.replace(tzinfo=UTC)
