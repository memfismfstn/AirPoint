import uuid
from datetime import date, datetime
from typing import Protocol

from src.application.dto import LicenseFilter, Page, Pagination
from src.domain.entities.license import License
from src.domain.enums import FlightRank


class LicenseRepository(Protocol):
    """Хранилище лицензий"""

    async def add(self, lic: License) -> None:
        """Сохраняет новую лицензию"""
        ...

    async def save(self, lic: License) -> None:
        """Сохраняет изменения существующей лицензии"""
        ...

    async def get(self, license_id: uuid.UUID, *, for_update: bool = False) -> License | None:
        """Находит лицензию по идентификатору"""
        ...

    async def list(self, flt: LicenseFilter, today: date, page: Pagination) -> Page[License]:
        """Возвращает страницу лицензий, новые сверху"""
        ...

    async def live_for_customer(self, customer_id: uuid.UUID, today: date) -> list[License]:
        """Возвращает живые лицензии покупателя (`active` или `suspended`, срок не вышел)"""
        ...

    async def last_for_customer(self, customer_id: uuid.UUID) -> License | None:
        """Возвращает последнюю выданную лицензию покупателя"""
        ...

    async def issue_moments(self, customer_id: uuid.UUID) -> list[datetime]:
        """Возвращает моменты выдачи всех лицензий покупателя"""
        ...

    async def active_ranks(
        self, customer_ids: list[uuid.UUID], today: date
    ) -> dict[uuid.UUID, FlightRank]:
        """Возвращает ранг действующей лицензии (`active`, срок не вышел) каждого покупателя"""
        ...
