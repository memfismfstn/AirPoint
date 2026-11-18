import uuid
from typing import Protocol

from src.application.dto import DroneFilter, Page, Pagination
from src.domain.entities.drone import Drone


class DroneRepository(Protocol):
    """Хранилище дронов"""

    async def add(self, drone: Drone) -> None:
        """Сохраняет новый дрон"""
        ...

    async def save(self, drone: Drone) -> None:
        """Сохраняет изменения существующего дрона"""
        ...

    async def get(self, drone_id: uuid.UUID, *, for_update: bool = False) -> Drone | None:
        """Находит дрон по идентификатору"""
        ...

    async def get_by_sku(self, sku: str) -> Drone | None:
        """Находит дрон по артикулу"""
        ...

    async def list(self, flt: DroneFilter, page: Pagination) -> Page[Drone]:
        """Возвращает страницу дронов, новые сверху"""
        ...
