import uuid
from datetime import UTC, date, datetime

import pytest

from src.application.commands import NewCustomer, NewDrone, NewPart
from src.application.dto import DroneFilter, LicenseFilter, Pagination
from src.application.use_cases.customers import CreateCustomer, GetCustomer, UpdateCustomer
from src.application.use_cases.drones import CreateDrone, PurchaseDrone, UpdateDrone
from src.application.use_cases.licenses import (
    IssueLicense,
    ListLicenses,
    RenewLicense,
    RevokeLicense,
)
from src.application.use_cases.parts import CreatePart
from src.domain.enums import DronePurpose, DroneStatus, FlightRank, LicenseStatus
from src.domain.errors import (
    ActiveLicenseExists,
    CustomerNotFound,
    CustomerUnderage,
    DailyLimitReached,
    DomainError,
    DroneNotAvailable,
    DroneNotFound,
    LicenseNotFound,
    NoLicense,
    PhoneAlreadyExists,
    RenewalTooEarly,
    SkuAlreadyExists,
)
from tests.unit.fakes import FixedClock, MemoryUnitOfWork

NOW = datetime(2026, 11, 3, 9, 0, tzinfo=UTC)
PAGE = Pagination(limit=20, offset=0)


@pytest.fixture
def uow() -> MemoryUnitOfWork:
    return MemoryUnitOfWork()


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(NOW)


async def new_customer(uow, clock, phone="+79990000000", birth=date(1990, 1, 1)):
    view = await CreateCustomer(uow, clock).execute(NewCustomer("Иван", phone, None, birth))
    return view.id


async def new_drone(uow, clock, **overrides):
    data = dict(
        sku="S1",
        name="n",
        manufacturer="m",
        purpose=DronePurpose.FPV,
        rank=FlightRank.PRO,
        weight_g=1,
        max_flight_time_min=1,
        max_range_m=1,
        has_camera=False,
        price=500,
    )
    return await CreateDrone(uow, clock).execute(NewDrone(**(data | overrides)))


async def code_of(coro) -> type[DomainError]:
    with pytest.raises(DomainError) as error:
        await coro
    return type(error.value)


async def test_phone_and_sku_must_be_unique(uow, clock):
    await new_customer(uow, clock)
    cmd = NewCustomer("Пётр", "+79990000000", None, date(1991, 1, 1))
    assert await code_of(CreateCustomer(uow, clock).execute(cmd)) is PhoneAlreadyExists
    await new_drone(uow, clock)
    cmd = NewDrone("S1", "n", "m", DronePurpose.FPV, FlightRank.PRO, 1, 1, 1, False, 1)
    assert await code_of(CreateDrone(uow, clock).execute(cmd)) is SkuAlreadyExists


async def test_issue_license_upgrade_and_daily_limit(uow, clock):
    customer_id = await new_customer(uow, clock)
    first = await IssueLicense(uow, clock).execute(customer_id, FlightRank.PILOT)
    assert (
        first.status is LicenseStatus.ACTIVE
        and (await GetCustomer(uow, clock).execute(customer_id)).rank is FlightRank.PILOT
    )

    second = await IssueLicense(uow, clock).execute(customer_id, FlightRank.ACE)
    old = uow.licenses.items[first.id]
    assert old.status is LicenseStatus.REVOKED and old.revoke_reason == "заменена новой лицензией"
    assert (await GetCustomer(uow, clock).execute(customer_id)).rank is FlightRank.ACE

    assert (
        await code_of(IssueLicense(uow, clock).execute(customer_id, FlightRank.PRO))
        is ActiveLicenseExists
    )
    other = await new_customer(uow, clock, "+79990000001")
    await IssueLicense(uow, clock).execute(
        other, FlightRank.ROOKIE
    )
    third = await new_customer(uow, clock, "+79990000002")
    assert (
        await code_of(IssueLicense(uow, clock).execute(third, FlightRank.ROOKIE))
        is DailyLimitReached
    )
    assert second.valid_until == date(2027, 11, 3)

    
    clock.set(datetime(2026, 11, 3, 21, 1, tzinfo=UTC))
    await IssueLicense(uow, clock).execute(third, FlightRank.ROOKIE)


async def test_underage_and_missing_customer_do_not_touch_counter(uow, clock):
    minor_id = await new_customer(uow, clock, birth=date(2015, 1, 1))
    assert (
        await code_of(IssueLicense(uow, clock).execute(minor_id, FlightRank.ROOKIE))
        is CustomerUnderage
    )
    assert (
        await code_of(IssueLicense(uow, clock).execute(uuid.uuid4(), FlightRank.ROOKIE))
        is CustomerNotFound
    )
    assert uow.issue_counter.days == {}


async def test_purchase_flow(uow, clock):
    buyer_id = await new_customer(uow, clock)
    drone = await new_drone(uow, clock)
    purchase = PurchaseDrone(uow, clock)
    assert await code_of(purchase.execute(drone.id, buyer_id)) is NoLicense
    issued_license = await IssueLicense(uow, clock).execute(buyer_id, FlightRank.PRO)
    sold = await purchase.execute(drone.id, buyer_id)
    assert (sold.status, sold.customer_id, sold.sold_price, sold.sold_license_id) == (
        DroneStatus.SOLD,
        buyer_id,
        500,
        issued_license.id,
    )
    assert uow.drones.items[drone.id].status is DroneStatus.SOLD
    assert await code_of(purchase.execute(drone.id, buyer_id)) is DroneNotAvailable
    assert await code_of(purchase.execute(uuid.uuid4(), buyer_id)) is DroneNotFound
    second_drone = await new_drone(uow, clock, sku="S2")
    assert await code_of(purchase.execute(second_drone.id, uuid.uuid4())) is CustomerNotFound


async def test_purpose_change_detaches_foreign_parts(uow, clock):
    drone = await new_drone(uow, clock)
    part = await CreatePart(uow, clock).execute(NewPart("p", DronePurpose.FPV, 1, drone.id))
    assert part.drone_id == drone.id
    await UpdateDrone(uow, clock).execute(drone.id, {"purpose": DronePurpose.CAMERA})
    assert uow.parts.items[part.id].drone_id is None


async def test_update_drone_sku_conflict(uow, clock):
    spare_drone = await new_drone(uow, clock)
    await new_drone(uow, clock, sku="S2")
    assert (
        await code_of(UpdateDrone(uow, clock).execute(spare_drone.id, {"sku": "S2"}))
        is SkuAlreadyExists
    )
    await UpdateDrone(uow, clock).execute(
        spare_drone.id, {"sku": "S1"}
    )  


async def test_birth_date_update_cannot_legalize_license(uow, clock):
    customer_id = await new_customer(uow, clock)
    await IssueLicense(uow, clock).execute(customer_id, FlightRank.ROOKIE)
    result = await code_of(
        UpdateCustomer(uow, clock).execute(customer_id, {"birth_date": date(2015, 1, 1)})
    )
    assert result is CustomerUnderage
    assert uow.customers.items[customer_id].birth_date == date(1990, 1, 1)


async def test_license_lifecycle_through_use_cases(uow, clock):
    customer_id = await new_customer(uow, clock)
    issued_license = await IssueLicense(uow, clock).execute(customer_id, FlightRank.PRO)
    assert await code_of(RenewLicense(uow, clock).execute(issued_license.id)) is RenewalTooEarly
    clock.set(datetime(2027, 10, 10, 9, 0, tzinfo=UTC))
    renewed = await RenewLicense(uow, clock).execute(issued_license.id)
    assert renewed.valid_until == date(2028, 11, 3) and renewed.key == issued_license.key
    revoked = await RevokeLicense(uow, clock).execute(issued_license.id, "причина")
    assert revoked.status is LicenseStatus.REVOKED
    page = await ListLicenses(uow, clock).execute(LicenseFilter(status=LicenseStatus.REVOKED), PAGE)
    assert page.total == 1 and page.items[0].id == issued_license.id
    assert await code_of(RevokeLicense(uow, clock).execute(uuid.uuid4(), "x")) is LicenseNotFound
    assert DroneFilter().purpose is None
