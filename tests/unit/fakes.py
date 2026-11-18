import uuid
from dataclasses import replace
from datetime import date, datetime
from types import TracebackType
from typing import Any, Self

from src.application.dto import DroneFilter, LicenseFilter, Page, Pagination
from src.domain.entities.customer import Customer
from src.domain.entities.drone import Drone
from src.domain.entities.license import License
from src.domain.entities.part import Part
from src.domain.enums import DronePurpose, FlightRank, LicenseStatus


class MemoryRepo[E]:
    """Общая основа: хранит копии сущностей, как это делала бы база"""

    def __init__(self) -> None:
        self.items: dict[uuid.UUID, E] = {}

    async def add(self, entity: E) -> None:
        self.items[entity.id] = replace(entity)

    async def save(self, entity: E) -> None:
        self.items[entity.id] = replace(entity)

    async def get(self, entity_id: uuid.UUID, *, for_update: bool = False) -> E | None:
        found = self.items.get(entity_id)
        return None if found is None else replace(found)

    def page(self, rows: list[E], page: Pagination) -> Page[E]:
        return Page(rows[page.offset : page.offset + page.limit], len(rows), page)


class MemoryCustomers(MemoryRepo[Customer]):
    async def get_by_phone(self, phone: str) -> Customer | None:
        return next(
            (replace(customer) for customer in self.items.values() if customer.phone == phone), None
        )

    async def list(self, phone: str | None, page: Pagination) -> Page[Customer]:
        rows = [customer for customer in self.items.values() if phone in (None, customer.phone)]
        return self.page(rows, page)


class MemoryLicenses(MemoryRepo[License]):
    async def list(self, filters: LicenseFilter, today: date, page: Pagination) -> Page[License]:
        rows = [
            license_
            for license_ in self.items.values()
            if filters.customer_id in (None, license_.customer_id)
            and filters.key in (None, license_.key)
            and filters.status in (None, license_.effective_status(today))
        ]
        return self.page(rows, page)

    async def live_for_customer(self, customer_id: uuid.UUID, today: date) -> list[License]:
        return [
            replace(license_)
            for license_ in self.items.values()
            if license_.customer_id == customer_id and license_.is_live(today)
        ]

    async def last_for_customer(self, customer_id: uuid.UUID) -> License | None:
        own = [license_ for license_ in self.items.values() if license_.customer_id == customer_id]
        return replace(max(own, key=lambda license_: license_.issued_at)) if own else None

    async def issue_moments(self, customer_id: uuid.UUID) -> list[datetime]:
        return [
            license_.issued_at
            for license_ in self.items.values()
            if license_.customer_id == customer_id
        ]

    async def active_ranks(
        self, customer_ids: list[uuid.UUID], today: date
    ) -> dict[uuid.UUID, FlightRank]:
        return {
            license_.customer_id: license_.rank
            for license_ in self.items.values()
            if license_.customer_id in customer_ids
            and license_.effective_status(today) is LicenseStatus.ACTIVE
        }


class MemoryDrones(MemoryRepo[Drone]):
    async def get_by_sku(self, sku: str) -> Drone | None:
        return next((replace(drone) for drone in self.items.values() if drone.sku == sku), None)

    async def list(self, filters: DroneFilter, page: Pagination) -> Page[Drone]:
        return self.page(list(self.items.values()), page)


class MemoryParts(MemoryRepo[Part]):
    async def delete(self, part: Part) -> None:
        self.items.pop(part.id, None)

    async def list(
        self, purpose: DronePurpose | None, attached: bool | None, page: Pagination
    ) -> Page[Part]:
        return self.page(list(self.items.values()), page)

    async def list_by_drone(self, drone_id: uuid.UUID, page: Pagination) -> Page[Part]:
        return self.page([part for part in self.items.values() if part.drone_id == drone_id], page)

    async def all_by_drone(self, drone_id: uuid.UUID) -> list[Part]:
        return [replace(part) for part in self.items.values() if part.drone_id == drone_id]


class MemoryCounter:
    def __init__(self) -> None:
        self.days: dict[date, int] = {}

    async def try_reserve(self, day: date, limit: int) -> bool:
        if self.days.get(day, 0) >= limit:
            return False
        self.days[day] = self.days.get(day, 0) + 1
        return True


class MemoryUnitOfWork:
    """Единица работы в памяти: реализует тот же порт, что и SqlAlchemyUnitOfWork"""

    def __init__(self) -> None:
        self.customers = MemoryCustomers()
        self.licenses = MemoryLicenses()
        self.drones = MemoryDrones()
        self.parts = MemoryParts()
        self.issue_counter = MemoryCounter()
        self.commits = 0

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    async def begin_write(self) -> None:
        return None

    async def commit(self) -> None:
        self.commits += 1


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now

    def set(self, now: datetime) -> None:
        self._now = now


def dump(obj: Any) -> dict[str, Any]:
    return {k: getattr(obj, k) for k in obj.__slots__}
