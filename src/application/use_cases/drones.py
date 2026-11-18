import uuid
from dataclasses import asdict
from typing import Any

from src.application.commands import NewDrone
from src.application.dto import DroneFilter, Page, Pagination
from src.application.use_cases.base import UseCase, require_customer, require_drone
from src.domain.entities.drone import Drone
from src.domain.entities.part import Part
from src.domain.errors import SkuAlreadyExists


class CreateDrone(UseCase):
    """Добавляет дрон на склад"""

    async def execute(self, cmd: NewDrone) -> Drone:
        """Создаёт дрон со статусом `in_stock`

        Args:
            cmd: Данные дрона

        Returns:
            Созданный дрон

        Raises:
            DomainError: Артикул уже занят
        """
        now, _ = self.moment()
        async with self.uow as uow:
            await uow.begin_write()
            if await uow.drones.get_by_sku(cmd.sku) is not None:
                raise SkuAlreadyExists(f"Дрон с артикулом {cmd.sku} уже есть")
            drone = Drone.register(**asdict(cmd), now=now)
            await uow.drones.add(drone)
            await uow.commit()
        return drone


class GetDrone(UseCase):
    """Возвращает один дрон"""

    async def execute(self, drone_id: uuid.UUID) -> Drone:
        """Находит дрон

        Args:
            drone_id: Идентификатор дрона

        Returns:
            Дрон

        Raises:
            DomainError: Дрона нет
        """
        async with self.uow as uow:
            return await require_drone(uow, drone_id)


class ListDrones(UseCase):
    """Возвращает страницу дронов"""

    async def execute(self, flt: DroneFilter, page: Pagination) -> Page[Drone]:
        """Ищет дроны по фильтрам

        Args:
            flt: Фильтры
            page: Параметры пагинации

        Returns:
            Страница дронов
        """
        async with self.uow as uow:
            return await uow.drones.list(flt, page)


class UpdateDrone(UseCase):
    """Меняет дрон"""

    async def execute(self, drone_id: uuid.UUID, changes: dict[str, Any]) -> Drone:
        """Применяет изменения; при смене `purpose` отвязывает запчасти другого типа

        Args:
            drone_id: Идентификатор дрона
            changes: Меняемые поля (только переданные в запросе)

        Returns:
            Обновлённый дрон

        Raises:
            DomainError: Дрона нет, он продан, пытаются выставить `sold`, артикул занят
        """
        now, _ = self.moment()
        async with self.uow as uow:
            await uow.begin_write()
            drone = await require_drone(uow, drone_id, for_update=True)
            purpose_changed = drone.apply_update(changes, now)
            if "sku" in changes:
                other = await uow.drones.get_by_sku(drone.sku)
                if other is not None and other.id != drone.id:
                    raise SkuAlreadyExists(f"Дрон с артикулом {drone.sku} уже есть")
            await uow.drones.save(drone)
            if purpose_changed:
                for part in await uow.parts.all_by_drone(drone.id):
                    if part.purpose != drone.purpose:
                        part.detach()
                        await uow.parts.save(part)
            await uow.commit()
        return drone


class ListDroneParts(UseCase):
    """Возвращает запчасти дрона"""

    async def execute(self, drone_id: uuid.UUID, page: Pagination) -> Page[Part]:
        """Отдаёт страницу запчастей дрона

        Args:
            drone_id: Идентификатор дрона
            page: Параметры пагинации

        Returns:
            Страница запчастей

        Raises:
            DomainError: Дрона нет
        """
        async with self.uow as uow:
            await require_drone(uow, drone_id)
            return await uow.parts.list_by_drone(drone_id, page)


class PurchaseDrone(UseCase):
    """Продаёт дрон покупателю"""

    async def execute(self, drone_id: uuid.UUID, customer_id: uuid.UUID) -> Drone:
        """Проверяет последнюю лицензию покупателя и переводит дрон в `sold`

        Args:
            drone_id: Покупаемый дрон
            customer_id: Покупатель

        Returns:
            Проданный дрон с заполненными полями продажи

        Raises:
            DomainError: Дрона или покупателя нет, дрон недоступен, лицензия не подходит
        """
        now, today = self.moment()
        async with self.uow as uow:
            await uow.begin_write()
            drone = await require_drone(uow, drone_id, for_update=True)
            customer = await require_customer(uow, customer_id)
            last_license = await uow.licenses.last_for_customer(customer.id)
            drone.sell(customer_id=customer.id, last_license=last_license, now=now, today=today)
            await uow.drones.save(drone)
            await uow.commit()
        return drone
