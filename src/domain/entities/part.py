import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Self

from src.domain.enums import DronePurpose
from src.domain.errors import PartAlreadyAttached, PartPurposeMismatch
from src.domain.rules import PART_EDITABLE_FIELDS

if TYPE_CHECKING:
    from src.domain.entities.drone import Drone


@dataclass(slots=True, kw_only=True)
class Part:
    """Запчасть: аксессуар к конкретному дрону (пропеллеры, аккумулятор, пульт)

    У дрона может быть много запчастей, у запчасти не больше одного дрона

    Attributes:
        id: Идентификатор, UUID4
        name: Название
        purpose: Тип запчасти, должен совпадать с типом дрона при привязке
        price: Цена в копейках
        drone_id: Дрон, к которому привязана запчасть, или None
        created_at: Момент создания
    """

    id: uuid.UUID
    name: str
    purpose: DronePurpose
    price: int
    drone_id: uuid.UUID | None
    created_at: datetime

    @classmethod
    def register(cls, *, name: str, purpose: DronePurpose, price: int, now: datetime) -> Self:
        """Создаёт свободную запчасть

        Args:
            name: Название
            purpose: Тип
            price: Цена в копейках
            now: Текущий момент

        Returns:
            Новая запчасть без дрона
        """
        return cls(
            id=uuid.uuid4(), name=name, purpose=purpose, price=price, drone_id=None, created_at=now
        )

    def attach_to(self, drone: Drone) -> None:
        """Привязывает свободную запчасть к дрону того же типа

        Args:
            drone: Дрон

        Raises:
            DomainError: Типы не совпадают
        """
        self._ensure_matches(self.purpose, drone)
        self.drone_id = drone.id

    def detach(self) -> None:
        """Отвязывает запчасть от дрона"""
        self.drone_id = None

    def apply_update(self, changes: Mapping[str, Any], target_drone: Drone | None) -> None:
        """Применяет изменения, включая привязку и отвязку

        Перенести запчасть на другой дрон одним запросом нельзя: сначала отвязать

        Args:
            changes: Меняемые поля (`name`, `purpose`, `price`, `drone_id`)
            target_drone: Дрон, к которому запчасть будет привязана после изменений,
                или None, если она останется свободной

        Raises:
            DomainError: Запчасть уже привязана к другому дрону или типы не совпадают
        """
        if target_drone is not None:
            if self.drone_id is not None and self.drone_id != target_drone.id:
                raise PartAlreadyAttached()
            self._ensure_matches(changes.get("purpose", self.purpose), target_drone)
        for field, value in changes.items():
            if field not in PART_EDITABLE_FIELDS:
                raise ValueError(f"Поле {field} нельзя менять")
            setattr(self, field, value)

    @staticmethod
    def _ensure_matches(purpose: DronePurpose, drone: Drone) -> None:
        """Проверяет совпадение типа запчасти и типа дрона

        Args:
            purpose: Тип запчасти
            drone: Дрон

        Raises:
            DomainError: Типы не совпадают
        """
        if purpose != drone.purpose:
            raise PartPurposeMismatch(
                f"Запчасть типа {purpose.value} нельзя привязать "
                f"к дрону типа {drone.purpose.value}",
            )
