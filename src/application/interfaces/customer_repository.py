import uuid
from typing import Protocol

from src.application.dto import Page, Pagination
from src.domain.entities.customer import Customer


class CustomerRepository(Protocol):
    """Хранилище покупателей"""

    async def add(self, customer: Customer) -> None:
        """Сохраняет нового покупателя"""
        ...

    async def save(self, customer: Customer) -> None:
        """Сохраняет изменения существующего покупателя"""
        ...

    async def get(self, customer_id: uuid.UUID, *, for_update: bool = False) -> Customer | None:
        """Находит покупателя по идентификатору"""
        ...

    async def get_by_phone(self, phone: str) -> Customer | None:
        """Находит покупателя по телефону"""
        ...

    async def list(self, phone: str | None, page: Pagination) -> Page[Customer]:
        """Возвращает страницу покупателей, новые сверху"""
        ...
