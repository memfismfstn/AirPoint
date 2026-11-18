import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Self

from src.domain.dates import add_one_year, msk_date
from src.domain.enums import FlightRank, LicenseStatus
from src.domain.errors import (
    InvalidLicenseTransition,
    RenewalTooEarly,
)
from src.domain.rules import RENEWAL_WINDOW_DAYS, REPLACED_REASON
from src.domain.services.license_key import generate_license_key

_LIVE = (LicenseStatus.ACTIVE, LicenseStatus.SUSPENDED)


def resolve_status(status: LicenseStatus, valid_until: date, today: date) -> LicenseStatus:
    """Возвращает актуальный статус лицензии с учётом истечения срока

    В хранилище у просроченной лицензии может быть ещё `active` или `suspended`:
    срок вышел со следующего дня после `valid_until`, а запись никто не менял

    Args:
        status: Статус, сохранённый в хранилище
        valid_until: Последний день действия
        today: Сегодняшняя дата по Москве

    Returns:
        `expired`, если срок вышел у живой лицензии, иначе сохранённый статус
    """
    if status in _LIVE and today > valid_until:
        return LicenseStatus.EXPIRED
    return status


@dataclass(slots=True, kw_only=True)
class License:
    """Лицензия: разрешение покупателю на дроны определённого ранга

    Attributes:
        id: Идентификатор, UUID4
        key: Уникальный ключ лицензии
        customer_id: Владелец
        rank: Лётный ранг
        status: Сохранённый статус, актуальный считает `effective_status`
        issued_at: Момент выдачи
        valid_until: Последний день действия (дата выдачи + 1 год)
        revoke_reason: Причина отзыва, обязательна для `revoked`
    """

    id: uuid.UUID
    key: str
    customer_id: uuid.UUID
    rank: FlightRank
    status: LicenseStatus
    issued_at: datetime
    valid_until: date
    revoke_reason: str | None = None

    @classmethod
    def issue(cls, *, customer_id: uuid.UUID, rank: FlightRank, now: datetime) -> Self:
        """Выдаёт новую лицензию на год от московской даты выдачи

        Args:
            customer_id: Владелец
            rank: Ранг лицензии
            now: Момент выдачи

        Returns:
            Новая лицензия со статусом `active`
        """
        return cls(
            id=uuid.uuid4(),
            key=generate_license_key(),
            customer_id=customer_id,
            rank=rank,
            status=LicenseStatus.ACTIVE,
            issued_at=now,
            valid_until=add_one_year(msk_date(now)),
        )

    def effective_status(self, today: date) -> LicenseStatus:
        """Актуальный статус на сегодня: `expired`, если срок уже прошёл

        Args:
            today: Сегодняшняя дата по Москве

        Returns:
            Актуальный статус
        """
        return resolve_status(self.status, self.valid_until, today)

    def is_live(self, today: date) -> bool:
        """Живая лицензия: действующая или приостановленная, но не истёкшая

        Args:
            today: Сегодняшняя дата по Москве

        Returns:
            True, если лицензия `active` или `suspended` и срок не вышел
        """
        return self.effective_status(today) in _LIVE

    def suspend(self, today: date) -> None:
        """Приостанавливает действующую лицензию

        Args:
            today: Сегодняшняя дата по Москве

        Raises:
            DomainError: Лицензия не `active`
        """
        self._require(today, {LicenseStatus.ACTIVE}, LicenseStatus.SUSPENDED)
        self.status = LicenseStatus.SUSPENDED

    def resume(self, today: date) -> None:
        """Возобновляет приостановленную лицензию, если срок не вышел

        Args:
            today: Сегодняшняя дата по Москве

        Raises:
            DomainError: Лицензия не `suspended`
        """
        self._require(today, {LicenseStatus.SUSPENDED}, LicenseStatus.ACTIVE)
        self.status = LicenseStatus.ACTIVE

    def revoke(self, reason: str, today: date) -> None:
        """Отзывает лицензию навсегда

        Args:
            reason: Причина отзыва
            today: Сегодняшняя дата по Москве

        Raises:
            DomainError: Лицензия уже отозвана или истекла
        """
        self._require(today, set(_LIVE), LicenseStatus.REVOKED)
        self.status = LicenseStatus.REVOKED
        self.revoke_reason = reason

    def replace(self) -> None:
        """Отзывает живую лицензию при выдаче новой, более высокого ранга"""
        self.status = LicenseStatus.REVOKED
        self.revoke_reason = REPLACED_REASON

    def renew(self, today: date) -> None:
        """Продлевает действующую лицензию на год от текущей даты окончания

        Продлевать можно только `active` и не раньше чем за `RENEWAL_WINDOW_DAYS`
        дней до конца срока

        Args:
            today: Сегодняшняя дата по Москве

        Raises:
            DomainError: Лицензия не `active` или до конца срока ещё далеко
        """
        current = self.effective_status(today)
        if current != LicenseStatus.ACTIVE:
            raise InvalidLicenseTransition(
                f"Продлить можно только действующую лицензию, а эта в статусе {current.value}",
            )
        days_left = (self.valid_until - today).days
        if days_left > RENEWAL_WINDOW_DAYS:
            raise RenewalTooEarly(
                f"Продлить можно за {RENEWAL_WINDOW_DAYS} дней до конца срока, "
                f"до окончания ещё {days_left} дн",
            )
        self.valid_until = add_one_year(self.valid_until)

    def _require(self, today: date, allowed: set[LicenseStatus], target: LicenseStatus) -> None:
        """Проверяет, что переход в `target` возможен из актуального статуса

        Args:
            today: Сегодняшняя дата по Москве
            allowed: Актуальные статусы, из которых переход разрешён
            target: Новый статус

        Raises:
            DomainError: Переход невозможен
        """
        current = self.effective_status(today)
        if current not in allowed:
            raise InvalidLicenseTransition(
                f"Из статуса {current.value} нельзя перейти в {target.value}",
            )
