from types import TracebackType
from typing import Protocol, Self

from src.application.interfaces.customer_repository import CustomerRepository
from src.application.interfaces.daily_issue_counter import DailyIssueCounter
from src.application.interfaces.drone_repository import DroneRepository
from src.application.interfaces.license_repository import LicenseRepository
from src.application.interfaces.part_repository import PartRepository


class UnitOfWork(Protocol):
    """Единица работы: одна транзакция и все репозитории внутри неё"""

    customers: CustomerRepository
    licenses: LicenseRepository
    drones: DroneRepository
    parts: PartRepository
    issue_counter: DailyIssueCounter

    async def __aenter__(self) -> Self:
        """Открывает сессию"""
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Откатывает незафиксированное и закрывает сессию"""
        ...

    async def begin_write(self) -> None:
        """Начинает транзакцию записи, сразу занимая право писать"""
        ...

    async def commit(self) -> None:
        """Фиксирует транзакцию"""
        ...
