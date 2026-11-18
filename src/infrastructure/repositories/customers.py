from sqlalchemy import select

from src.application.dto import Page, Pagination
from src.domain.entities.customer import Customer
from src.infrastructure.db.models import CustomerOrm
from src.infrastructure.repositories.base import SqlRepository


class SqlCustomerRepository(SqlRepository[Customer, CustomerOrm]):
    """Покупатели в SQL-базе"""

    entity_cls = Customer
    orm_cls = CustomerOrm

    async def get_by_phone(self, phone: str) -> Customer | None:
        """Находит покупателя по телефону"""
        return await self._one(select(CustomerOrm).where(CustomerOrm.phone == phone))

    async def list(self, phone: str | None, page: Pagination) -> Page[Customer]:
        """Возвращает страницу покупателей, новые сверху"""
        stmt = select(CustomerOrm)
        if phone is not None:
            stmt = stmt.where(CustomerOrm.phone == phone)
        return await self._page(stmt, (CustomerOrm.created_at.desc(), CustomerOrm.id), page)
