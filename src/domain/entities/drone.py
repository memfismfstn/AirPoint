import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Self

from src.domain.entities.license import License
from src.domain.enums import DronePurpose, DroneStatus, FlightRank, LicenseStatus
from src.domain.errors import (
    DroneNotAvailable,
    DroneSold,
    InvalidDroneStatus,
    LicenseExpired,
    LicenseRankTooLow,
    LicenseSuspended,
    NoLicense,
)
from src.domain.rules import DRONE_EDITABLE_FIELDS


@dataclass(slots=True, kw_only=True)
class Drone:
    """Конкретный дрон на складе или уже проданный

    После продажи дрон навсегда привязан к покупателю, а `sold_price`
    фиксирует цену на момент покупки

    Attributes:
        id: Идентификатор, UUID4
        sku: Артикул, уникальный
        name: Название
        manufacturer: Производитель
        purpose: Назначение
        rank: Лётный ранг дрона
        weight_g: Вес в граммах
        max_flight_time_min: Время полёта в минутах
        max_range_m: Дальность в метрах
        has_camera: Есть ли камера
        price: Цена в копейках
        status: Статус
        customer_id: Владелец, пусто до продажи
        sold_at: Момент продажи
        sold_price: Цена продажи в копейках
        sold_license_id: Лицензия, по которой куплен дрон
        created_at: Момент создания
        updated_at: Момент последнего изменения
    """

    id: uuid.UUID
    sku: str
    name: str
    manufacturer: str
    purpose: DronePurpose
    rank: FlightRank
    weight_g: int
    max_flight_time_min: int
    max_range_m: int
    has_camera: bool
    price: int
    status: DroneStatus
    customer_id: uuid.UUID | None
    sold_at: datetime | None
    sold_price: int | None
    sold_license_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def register(
        cls,
        *,
        sku: str,
        name: str,
        manufacturer: str,
        purpose: DronePurpose,
        rank: FlightRank,
        weight_g: int,
        max_flight_time_min: int,
        max_range_m: int,
        has_camera: bool,
        price: int,
        now: datetime,
    ) -> Self:
        """Принимает дрон на склад

        Args:
            sku: Артикул
            name: Название
            manufacturer: Производитель
            purpose: Назначение
            rank: Лётный ранг
            weight_g: Вес в граммах
            max_flight_time_min: Время полёта в минутах
            max_range_m: Дальность в метрах
            has_camera: Есть ли камера
            price: Цена в копейках
            now: Текущий момент

        Returns:
            Новый дрон со статусом `in_stock`
        """
        return cls(
            id=uuid.uuid4(),
            sku=sku,
            name=name,
            manufacturer=manufacturer,
            purpose=purpose,
            rank=rank,
            weight_g=weight_g,
            max_flight_time_min=max_flight_time_min,
            max_range_m=max_range_m,
            has_camera=has_camera,
            price=price,
            status=DroneStatus.IN_STOCK,
            customer_id=None,
            sold_at=None,
            sold_price=None,
            sold_license_id=None,
            created_at=now,
            updated_at=now,
        )

    def apply_update(self, changes: Mapping[str, Any], now: datetime) -> bool:
        """Применяет изменения полей

        Args:
            changes: Меняемые поля
            now: Текущий момент

        Returns:
            True, если изменилось назначение: тогда запчасти другого типа надо отвязать

        Raises:
            DomainError: Дрон продан или пытаются выставить статус `sold`
        """
        if self.status == DroneStatus.SOLD:
            raise DroneSold()
        if changes.get("status") == DroneStatus.SOLD:
            raise InvalidDroneStatus()
        purpose_changed = "purpose" in changes and changes["purpose"] != self.purpose
        for field, value in changes.items():
            if field not in DRONE_EDITABLE_FIELDS:
                raise ValueError(f"Поле {field} нельзя менять")
            setattr(self, field, value)
        self.updated_at = now
        return purpose_changed

    def sell(
        self,
        *,
        customer_id: uuid.UUID,
        last_license: License | None,
        now: datetime,
        today: date,
    ) -> None:
        """Продаёт дрон покупателю по его последней выданной лицензии

        Порядок проверок: дрон в наличии, затем лицензия (есть, не приостановлена,
        не истекла, ранг не ниже ранга дрона)

        Args:
            customer_id: Покупатель
            last_license: Последняя выданная лицензия покупателя или None
            now: Момент продажи
            today: Сегодняшняя дата по Москве

        Raises:
            DomainError: Дрон недоступен или лицензия не подходит
        """
        if self.status != DroneStatus.IN_STOCK:
            raise DroneNotAvailable()
        lic = self._license_allowing_purchase(last_license, today)
        self.status = DroneStatus.SOLD
        self.customer_id = customer_id
        self.sold_at = now
        self.sold_price = self.price
        self.sold_license_id = lic.id
        self.updated_at = now

    def _license_allowing_purchase(self, lic: License | None, today: date) -> License:
        """Определяет по последней лицензии, можно ли купить этот дрон

        Args:
            lic: Последняя выданная лицензия покупателя или None
            today: Сегодняшняя дата по Москве

        Returns:
            Лицензия, по которой разрешена покупка

        Raises:
            DomainError: Нет лицензии, она приостановлена, истекла или ранг ниже
        """
        status = None if lic is None else lic.effective_status(today)
        if lic is None or status == LicenseStatus.REVOKED:
            raise NoLicense()
        if status == LicenseStatus.SUSPENDED:
            raise LicenseSuspended()
        if status == LicenseStatus.EXPIRED:
            raise LicenseExpired()
        if lic.rank.level < self.rank.level:
            raise LicenseRankTooLow(
                f"Для дрона ранга {self.rank.value} нужна лицензия ранга {self.rank.value} "
                f"или выше, у покупателя — {lic.rank.value}",
            )
        return lic
