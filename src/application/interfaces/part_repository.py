import uuid
from typing import Protocol

from src.application.dto import Page, Pagination
from src.domain.entities.part import Part
from src.domain.enums import DronePurpose


class PartRepository(Protocol):
    """Хранилище запчастей"""

    async def add(self, part: Part) -> None:
        """Сохраняет новую запчасть"""
        ...

    async def save(self, part: Part) -> None:
        """Сохраняет изменения существующей запчасти"""
        ...

    async def delete(self, part: Part) -> None:
        """Удаляет запчасть"""
        ...

    async def get(self, part_id: uuid.UUID, *, for_update: bool = False) -> Part | None:
        """Находит запчасть по идентификатору"""
        ...

    async def list(
        self, purpose: DronePurpose | None, attached: bool | None, page: Pagination
    ) -> Page[Part]:
        """Возвращает страницу запчастей, новые сверху"""
        ...

    async def list_by_drone(self, drone_id: uuid.UUID, page: Pagination) -> Page[Part]:
        """Возвращает страницу запчастей дрона"""
        ...

    async def all_by_drone(self, drone_id: uuid.UUID) -> list[Part]:
        """Возвращает все запчасти дрона без пагинации"""
        ...
