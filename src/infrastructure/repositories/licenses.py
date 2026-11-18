import uuid
from datetime import date, datetime

from sqlalchemy import and_, or_, select

from src.application.dto import LicenseFilter, Page, Pagination
from src.domain.entities.license import License
from src.domain.enums import FlightRank, LicenseStatus
from src.infrastructure.db.models import LicenseOrm
from src.infrastructure.repositories.base import SqlRepository

_LIVE = [LicenseStatus.ACTIVE, LicenseStatus.SUSPENDED]


def _status_condition(status: LicenseStatus, today: date) -> object:
    """Строит SQL-условие по актуальному статусу, с учётом истечения срока"""
    live = LicenseOrm.status.in_(_LIVE)
    if status == LicenseStatus.EXPIRED:
        return or_(
            LicenseOrm.status == LicenseStatus.EXPIRED,
            and_(live, LicenseOrm.valid_until < today),
        )
    if status == LicenseStatus.REVOKED:
        return LicenseOrm.status == LicenseStatus.REVOKED
    return and_(LicenseOrm.status == status, LicenseOrm.valid_until >= today)


class SqlLicenseRepository(SqlRepository[License, LicenseOrm]):
    """Лицензии в SQL-базе"""

    entity_cls = License
    orm_cls = LicenseOrm

    async def list(self, flt: LicenseFilter, today: date, page: Pagination) -> Page[License]:
        """Возвращает страницу лицензий, новые сверху"""
        stmt = select(LicenseOrm)
        if flt.customer_id is not None:
            stmt = stmt.where(LicenseOrm.customer_id == flt.customer_id)
        if flt.status is not None:
            stmt = stmt.where(_status_condition(flt.status, today))
        if flt.key is not None:
            stmt = stmt.where(LicenseOrm.key == flt.key)
        return await self._page(stmt, (LicenseOrm.issued_at.desc(), LicenseOrm.id), page)

    async def live_for_customer(self, customer_id: uuid.UUID, today: date) -> list[License]:
        """Возвращает живые лицензии покупателя под блокировкой записи"""
        return await self._all(
            select(LicenseOrm)
            .where(
                LicenseOrm.customer_id == customer_id,
                LicenseOrm.status.in_(_LIVE),
                LicenseOrm.valid_until >= today,
            )
            .with_for_update()
        )

    async def last_for_customer(self, customer_id: uuid.UUID) -> License | None:
        """Возвращает последнюю выданную лицензию покупателя"""
        return await self._one(
            select(LicenseOrm)
            .where(LicenseOrm.customer_id == customer_id)
            .order_by(LicenseOrm.issued_at.desc(), LicenseOrm.id.desc())
        )

    async def issue_moments(self, customer_id: uuid.UUID) -> list[datetime]:
        """Возвращает моменты выдачи всех лицензий покупателя"""
        rows = await self._session.scalars(
            select(LicenseOrm.issued_at).where(LicenseOrm.customer_id == customer_id)
        )
        return list(rows.all())

    async def active_ranks(
        self, customer_ids: list[uuid.UUID], today: date
    ) -> dict[uuid.UUID, FlightRank]:
        """Возвращает ранг действующей лицензии каждого покупателя"""
        if not customer_ids:
            return {}
        rows = await self._session.execute(
            select(LicenseOrm.customer_id, LicenseOrm.rank).where(
                LicenseOrm.customer_id.in_(customer_ids),
                LicenseOrm.status == LicenseStatus.ACTIVE,
                LicenseOrm.valid_until >= today,
            )
        )
        ranks: dict[uuid.UUID, FlightRank] = {}
        for customer_id, rank in rows.all():
            if customer_id not in ranks or rank.level > ranks[customer_id].level:
                ranks[customer_id] = rank
        return ranks
