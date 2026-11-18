from sqlalchemy import func, select

from src.application.dto import DroneFilter, Page, Pagination
from src.domain.entities.drone import Drone
from src.domain.enums import FlightRank
from src.infrastructure.db.models import DroneOrm
from src.infrastructure.repositories.base import SqlRepository


class SqlDroneRepository(SqlRepository[Drone, DroneOrm]):
    """Дроны в SQL-базе"""

    entity_cls = Drone
    orm_cls = DroneOrm

    async def get_by_sku(self, sku: str) -> Drone | None:
        """Находит дрон по артикулу"""
        return await self._one(select(DroneOrm).where(DroneOrm.sku == sku))

    async def list(self, flt: DroneFilter, page: Pagination) -> Page[Drone]:
        """Возвращает страницу дронов, новые сверху"""
        stmt = select(DroneOrm)
        if flt.purpose is not None:
            stmt = stmt.where(DroneOrm.purpose == flt.purpose)
        if flt.rank is not None:
            stmt = stmt.where(DroneOrm.rank == flt.rank)
        if flt.max_rank is not None:
            allowed = [r for r in FlightRank if r.level <= flt.max_rank.level]
            stmt = stmt.where(DroneOrm.rank.in_(allowed))
        if flt.status is not None:
            stmt = stmt.where(DroneOrm.status == flt.status)
        if flt.manufacturer is not None:
            stmt = stmt.where(func.lower(DroneOrm.manufacturer) == flt.manufacturer.lower())
        if flt.has_camera is not None:
            stmt = stmt.where(DroneOrm.has_camera == flt.has_camera)
        if flt.min_price is not None:
            stmt = stmt.where(DroneOrm.price >= flt.min_price)
        if flt.max_price is not None:
            stmt = stmt.where(DroneOrm.price <= flt.max_price)
        if flt.customer_id is not None:
            stmt = stmt.where(DroneOrm.customer_id == flt.customer_id)
        return await self._page(stmt, (DroneOrm.created_at.desc(), DroneOrm.id), page)
