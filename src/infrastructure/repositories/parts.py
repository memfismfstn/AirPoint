import uuid

from sqlalchemy import delete, select

from src.application.dto import Page, Pagination
from src.domain.entities.part import Part
from src.domain.enums import DronePurpose
from src.infrastructure.db.models import PartOrm
from src.infrastructure.repositories.base import SqlRepository


class SqlPartRepository(SqlRepository[Part, PartOrm]):
    """Запчасти в SQL-базе"""

    entity_cls = Part
    orm_cls = PartOrm

    async def delete(self, part: Part) -> None:
        """Удаляет запчасть"""
        await self._session.execute(delete(PartOrm).where(PartOrm.id == part.id))

    async def list(
        self, purpose: DronePurpose | None, attached: bool | None, page: Pagination
    ) -> Page[Part]:
        """Возвращает страницу запчастей, новые сверху"""
        stmt = select(PartOrm)
        if purpose is not None:
            stmt = stmt.where(PartOrm.purpose == purpose)
        if attached is True:
            stmt = stmt.where(PartOrm.drone_id.is_not(None))
        elif attached is False:
            stmt = stmt.where(PartOrm.drone_id.is_(None))
        return await self._page(stmt, (PartOrm.created_at.desc(), PartOrm.id), page)

    async def list_by_drone(self, drone_id: uuid.UUID, page: Pagination) -> Page[Part]:
        """Возвращает страницу запчастей дрона"""
        stmt = select(PartOrm).where(PartOrm.drone_id == drone_id)
        return await self._page(stmt, (PartOrm.created_at.desc(), PartOrm.id), page)

    async def all_by_drone(self, drone_id: uuid.UUID) -> list[Part]:
        """Возвращает все запчасти дрона без пагинации"""
        return await self._all(select(PartOrm).where(PartOrm.drone_id == drone_id))
