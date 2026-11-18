from datetime import UTC, datetime


class SystemClock:
    """Часы, которые возвращают настоящее текущее время"""

    def now(self) -> datetime:
        """Возвращает текущий момент в UTC"""
        return datetime.now(UTC)
