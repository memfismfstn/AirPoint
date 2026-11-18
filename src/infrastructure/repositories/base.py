import uuid
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto import Page, Pagination
from src.infrastructure.db.mappers import to_entity, to_orm


class SqlRepository[E, O]:
    """Репозиторий сущности `E`, хранящейся в ORM-модели `O`"""

    entity_cls: type[E]
    orm_cls: type[O]

    def __init__(self, session: AsyncSession) -> None:
        """Создаёт репозиторий в рамках сессии единицы работы"""
        self._session = session

    async def add(self, entity: E) -> None:
        """Сохраняет новую сущность и сразу отправляет INSERT в базу"""
        self._session.add(to_orm(self.orm_cls, entity))
        await self._session.flush()

    async def save(self, entity: E) -> None:
        """Сохраняет изменения существующей сущности"""
        await self._session.merge(to_orm(self.orm_cls, entity))

    async def get(self, entity_id: uuid.UUID, *, for_update: bool = False) -> E | None:
        """Находит сущность по идентификатору"""
        stmt = select(self.orm_cls).where(self.orm_cls.id == entity_id)
        if for_update:
            stmt = stmt.with_for_update()
        return await self._one(stmt)

    async def _one(self, stmt: Select[Any]) -> E | None:
        """Выполняет запрос и возвращает первую сущность"""
        row = await self._session.scalar(stmt.limit(1))
        return None if row is None else to_entity(self.entity_cls, row)

    async def _all(self, stmt: Select[Any]) -> list[E]:
        """Выполняет запрос и возвращает все сущности"""
        rows = await self._session.scalars(stmt)
        return [to_entity(self.entity_cls, row) for row in rows.all()]

    async def _page(
        self, stmt: Select[Any], order_by: tuple[Any, ...], page: Pagination
    ) -> Page[E]:
        """Выполняет запрос с сортировкой и пагинацией и считает общее число строк"""
        total = await self._session.scalar(
            select(func.count()).select_from(stmt.order_by(None).subquery())
        )
        items = await self._all(stmt.order_by(*order_by).limit(page.limit).offset(page.offset))
        return Page(items=items, total=total or 0, pagination=page)
