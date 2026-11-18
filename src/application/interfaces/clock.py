from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """Источник текущего времени"""

    def now(self) -> datetime:
        """Возвращает текущий момент"""
        ...
