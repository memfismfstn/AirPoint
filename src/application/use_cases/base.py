import uuid
from datetime import date, datetime

from src.application.interfaces import Clock, UnitOfWork
from src.domain.dates import msk_date
from src.domain.entities.customer import Customer
from src.domain.entities.drone import Drone
from src.domain.entities.part import Part
from src.domain.errors import CustomerNotFound, DroneNotFound, PartNotFound


class UseCase:
    """Основа сценария: единица работы и часы приходят снаружи (внедрение зависимостей)

    Attributes:
        uow: Единица работы со всеми репозиториями
        clock: Источник времени
    """

    __slots__ = ("clock", "uow")

    def __init__(self, uow: UnitOfWork, clock: Clock) -> None:
        """Создаёт сценарий

        Args:
            uow: Единица работы
            clock: Источник времени
        """
        self.uow = uow
        self.clock = clock

    def moment(self) -> tuple[datetime, date]:
        """Возвращает текущий момент и сегодняшнюю дату по Москве

        Returns:
            Пара из момента и московской даты
        """
        now = self.clock.now()
        return now, msk_date(now)


async def require_customer(
    uow: UnitOfWork, customer_id: uuid.UUID, *, for_update: bool = False
) -> Customer:
    """Возвращает покупателя или бросает `CUSTOMER_NOT_FOUND`

    Args:
        uow: Единица работы
        customer_id: Идентификатор покупателя
        for_update: Заблокировать запись до конца транзакции

    Returns:
        Найденный покупатель

    Raises:
        DomainError: Покупателя нет
    """
    customer = await uow.customers.get(customer_id, for_update=for_update)
    if customer is None:
        raise CustomerNotFound()
    return customer


async def require_drone(uow: UnitOfWork, drone_id: uuid.UUID, *, for_update: bool = False) -> Drone:
    """Возвращает дрон или бросает `DRONE_NOT_FOUND`

    Args:
        uow: Единица работы
        drone_id: Идентификатор дрона
        for_update: Заблокировать запись до конца транзакции

    Returns:
        Найденный дрон

    Raises:
        DomainError: Дрона нет
    """
    drone = await uow.drones.get(drone_id, for_update=for_update)
    if drone is None:
        raise DroneNotFound()
    return drone


async def require_part(uow: UnitOfWork, part_id: uuid.UUID, *, for_update: bool = False) -> Part:
    """Возвращает запчасть или бросает `PART_NOT_FOUND`

    Args:
        uow: Единица работы
        part_id: Идентификатор запчасти
        for_update: Заблокировать запись до конца транзакции

    Returns:
        Найденная запчасть

    Raises:
        DomainError: Запчасти нет
    """
    part = await uow.parts.get(part_id, for_update=for_update)
    if part is None:
        raise PartNotFound()
    return part
