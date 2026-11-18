import uuid
from collections.abc import Callable
from datetime import date

from src.application.dto import LicenseFilter, LicenseView, Page, Pagination
from src.application.use_cases.base import UseCase, require_customer
from src.domain.entities.license import License
from src.domain.enums import FlightRank
from src.domain.errors import DailyLimitReached, LicenseNotFound
from src.domain.rules import DAILY_LICENSE_LIMIT
from src.domain.services.license_issue import ensure_can_issue


class IssueLicense(UseCase):
    """Выдаёт лицензию"""

    async def execute(self, customer_id: uuid.UUID, rank: FlightRank) -> LicenseView:
        """Выдаёт лицензию; живая лицензия более низкого ранга заменяется

        Порядок проверок: покупатель существует, ему 18+, нет живой лицензии
        того же или более высокого ранга, не исчерпан дневной лимит

        Args:
            customer_id: Кому выдаём
            rank: Запрошенный ранг

        Returns:
            Новая лицензия со статусом `active`

        Raises:
            DomainError: Покупателя нет, он несовершеннолетний, живая лицензия
                не ниже запрошенной или исчерпан дневной лимит
        """
        now, today = self.moment()
        async with self.uow as uow:
            await uow.begin_write()
            customer = await require_customer(uow, customer_id, for_update=True)
            live = await uow.licenses.live_for_customer(customer.id, today)
            ensure_can_issue(customer.is_adult_on(today), live, rank)

            if not await uow.issue_counter.try_reserve(today, DAILY_LICENSE_LIMIT):
                raise DailyLimitReached(
                    f"За сегодня уже выдано {DAILY_LICENSE_LIMIT} лицензии, лимит исчерпан",
                )
            for old in live:
                old.replace()
                await uow.licenses.save(old)
            lic = License.issue(customer_id=customer.id, rank=rank, now=now)
            await uow.licenses.add(lic)
            await uow.commit()
        return LicenseView.of(lic, today)


class GetLicense(UseCase):
    """Возвращает одну лицензию"""

    async def execute(self, license_id: uuid.UUID) -> LicenseView:
        """Находит лицензию

        Args:
            license_id: Идентификатор лицензии

        Returns:
            Лицензия с актуальным статусом

        Raises:
            DomainError: Лицензии нет
        """
        _, today = self.moment()
        async with self.uow as uow:
            lic = await uow.licenses.get(license_id)
        if lic is None:
            raise LicenseNotFound()
        return LicenseView.of(lic, today)


class ListLicenses(UseCase):
    """Возвращает страницу лицензий"""

    async def execute(self, flt: LicenseFilter, page: Pagination) -> Page[LicenseView]:
        """Ищет лицензии по владельцу, актуальному статусу и ключу

        Args:
            flt: Фильтры
            page: Параметры пагинации

        Returns:
            Страница лицензий
        """
        _, today = self.moment()
        async with self.uow as uow:
            result = await uow.licenses.list(flt, today, page)
        return result.map(lambda lic: LicenseView.of(lic, today))


class _ChangeLicense(UseCase):
    """Основа сценариев, меняющих лицензию в одной транзакции"""

    async def _run(
        self, license_id: uuid.UUID, action: Callable[[License, date], None]
    ) -> LicenseView:
        """Загружает лицензию под блокировкой, применяет действие и сохраняет

        Args:
            license_id: Идентификатор лицензии
            action: Изменение лицензии, получает лицензию и сегодняшнюю дату

        Returns:
            Обновлённая лицензия

        Raises:
            DomainError: Лицензии нет или действие недопустимо
        """
        _, today = self.moment()
        async with self.uow as uow:
            await uow.begin_write()
            lic = await uow.licenses.get(license_id, for_update=True)
            if lic is None:
                raise LicenseNotFound()
            action(lic, today)
            await uow.licenses.save(lic)
            await uow.commit()
        return LicenseView.of(lic, today)


class SuspendLicense(_ChangeLicense):
    """Приостанавливает лицензию"""

    async def execute(self, license_id: uuid.UUID) -> LicenseView:
        """Приостанавливает действующую лицензию

        Args:
            license_id: Идентификатор лицензии

        Returns:
            Лицензия со статусом `suspended`
        """
        return await self._run(license_id, lambda lic, today: lic.suspend(today))


class ResumeLicense(_ChangeLicense):
    """Возобновляет лицензию"""

    async def execute(self, license_id: uuid.UUID) -> LicenseView:
        """Возобновляет приостановленную лицензию

        Args:
            license_id: Идентификатор лицензии

        Returns:
            Лицензия со статусом `active`
        """
        return await self._run(license_id, lambda lic, today: lic.resume(today))


class RevokeLicense(_ChangeLicense):
    """Отзывает лицензию"""

    async def execute(self, license_id: uuid.UUID, reason: str) -> LicenseView:
        """Отзывает лицензию навсегда с указанием причины

        Args:
            license_id: Идентификатор лицензии
            reason: Причина отзыва

        Returns:
            Лицензия со статусом `revoked`
        """
        return await self._run(license_id, lambda lic, today: lic.revoke(reason, today))


class RenewLicense(_ChangeLicense):
    """Продлевает лицензию"""

    async def execute(self, license_id: uuid.UUID) -> LicenseView:
        """Продлевает действующую лицензию на год

        Args:
            license_id: Идентификатор лицензии

        Returns:
            Лицензия с новым `valid_until`
        """
        return await self._run(license_id, lambda lic, today: lic.renew(today))
