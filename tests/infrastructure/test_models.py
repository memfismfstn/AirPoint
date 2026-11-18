from datetime import UTC, date, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.enums import DronePurpose, DroneStatus, FlightRank, LicenseStatus
from src.infrastructure.db.models import CustomerOrm as Customer
from src.infrastructure.db.models import DroneOrm as Drone
from src.infrastructure.db.models import LicenseOrm as License
from src.infrastructure.db.models import PartOrm as Part


def make_customer(phone: str = "+79161234567") -> Customer:
    return Customer(full_name="Иванов Иван", phone=phone, birth_date=date(1995, 4, 12))


def make_drone(sku: str = "DJI-1", **overrides) -> Drone:
    data = dict(
        sku=sku,
        name="Mini",
        manufacturer="DJI",
        purpose=DronePurpose.CAMERA,
        rank=FlightRank.PILOT,
        weight_g=249,
        max_flight_time_min=34,
        max_range_m=20000,
        price=100,
    )
    return Drone(**(data | overrides))


def make_license(customer_id, **overrides) -> License:
    data = dict(
        customer_id=customer_id,
        rank=FlightRank.PRO,
        issued_at=datetime(2026, 11, 1, 16, 40, tzinfo=UTC),
        valid_until=date(2027, 11, 1),
    )
    return License(**(data | overrides))


async def test_defaults_and_roundtrip(session: AsyncSession):
    customer = make_customer()
    session.add(customer)
    await session.flush()
    license_ = make_license(customer.id)
    drone = make_drone()
    session.add_all([license_, drone])
    await session.commit()

    got = await session.scalar(select(License))
    assert got.status is LicenseStatus.ACTIVE
    assert got.key.startswith("drl_") and len(got.key) == 36
    assert got.issued_at.tzinfo is not None and got.issued_at.hour == 16

    drone = await session.scalar(select(Drone))
    assert drone.status is DroneStatus.IN_STOCK and drone.has_camera is False
    assert drone.customer_id is None and drone.created_at.tzinfo is not None


async def test_unique_sku(session: AsyncSession):
    session.add_all([make_drone("A"), make_drone("A")])
    with pytest.raises(IntegrityError):
        await session.commit()


@pytest.mark.parametrize("field", ["weight_g", "max_flight_time_min", "max_range_m", "price"])
async def test_positive_numbers(session: AsyncSession, field: str):
    session.add(make_drone(**{field: 0}))
    with pytest.raises(IntegrityError):
        await session.commit()


async def test_sold_fields_must_be_consistent(session: AsyncSession):
    customer = make_customer()
    session.add(customer)
    await session.flush()
    """sold без sold_at/sold_price/sold_license_id — запрещено"""
    session.add(make_drone(status=DroneStatus.SOLD, customer_id=customer.id))
    with pytest.raises(IntegrityError):
        await session.commit()


async def test_owner_without_sold_status_forbidden(session: AsyncSession):
    customer = make_customer()
    session.add(customer)
    await session.flush()
    session.add(make_drone(customer_id=customer.id))
    with pytest.raises(IntegrityError):
        await session.commit()


async def test_revoked_requires_reason(session: AsyncSession):
    customer = make_customer()
    session.add(customer)
    await session.flush()
    session.add(make_license(customer.id, status=LicenseStatus.REVOKED))
    with pytest.raises(IntegrityError):
        await session.commit()


async def test_foreign_keys_enforced(session: AsyncSession):
    import uuid

    session.add(Part(name="Prop", purpose=DronePurpose.FPV, price=10, drone_id=uuid.uuid4()))
    with pytest.raises(IntegrityError):
        await session.commit()


async def test_naive_datetime_rejected(session: AsyncSession):
    customer = make_customer()
    session.add(customer)
    await session.flush()
    session.add(make_license(customer.id, issued_at=datetime(2026, 11, 1, 16, 40)))
    with pytest.raises(Exception, match="часовым поясом"):
        await session.commit()
