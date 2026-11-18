import uuid
from datetime import UTC, date, datetime

import pytest

from src.domain.dates import add_one_year, age_on, msk_date
from src.domain.entities.customer import Customer
from src.domain.entities.drone import Drone
from src.domain.entities.license import License, resolve_status
from src.domain.entities.part import Part
from src.domain.enums import DronePurpose, DroneStatus, FlightRank, LicenseStatus
from src.domain.errors import (
    ActiveLicenseExists,
    CustomerUnderage,
    DomainError,
    DroneNotAvailable,
    DroneSold,
    InvalidDroneStatus,
    InvalidLicenseTransition,
    LicenseExpired,
    LicenseRankTooLow,
    LicenseSuspended,
    NoLicense,
    PartAlreadyAttached,
    PartPurposeMismatch,
    RenewalTooEarly,
)
from src.domain.services.license_issue import ensure_can_issue

NOW = datetime(2026, 11, 3, 9, 0, tzinfo=UTC)
TODAY = date(2026, 11, 3)


def make_license(rank=FlightRank.PRO, **overrides) -> License:
    base = License.issue(customer_id=uuid.uuid4(), rank=rank, now=NOW)
    for field, value in overrides.items():
        setattr(base, field, value)
    return base


def make_drone(**overrides) -> Drone:
    data = dict(
        sku="S",
        name="n",
        manufacturer="m",
        purpose=DronePurpose.FPV,
        rank=FlightRank.PRO,
        weight_g=1,
        max_flight_time_min=1,
        max_range_m=1,
        has_camera=False,
        price=500,
        now=NOW,
    )
    return Drone.register(**(data | overrides))


def error_type(exc: pytest.ExceptionInfo[DomainError]) -> type[DomainError]:
    return type(exc.value)


def test_dates():
    assert add_one_year(date(2028, 2, 29)) == date(2029, 2, 28)
    assert age_on(date(2008, 11, 3), date(2026, 11, 3)) == 18
    assert age_on(date(2008, 11, 4), date(2026, 11, 3)) == 17
    assert age_on(date(2008, 2, 29), date(2026, 2, 28)) == 17
    assert msk_date(datetime(2026, 11, 3, 21, 30, tzinfo=UTC)) == date(2026, 11, 4)


def test_license_issue_and_expiry_boundary():
    license_ = make_license()
    assert license_.key.startswith("drl_") and len(license_.key) == 36
    assert license_.valid_until == date(2027, 11, 3) and license_.status is LicenseStatus.ACTIVE
    assert license_.effective_status(date(2027, 11, 3)) is LicenseStatus.ACTIVE
    assert license_.effective_status(date(2027, 11, 4)) is LicenseStatus.EXPIRED
    assert resolve_status(LicenseStatus.REVOKED, date(2020, 1, 1), TODAY) is LicenseStatus.REVOKED
    assert license_.is_live(TODAY) and not license_.is_live(date(2027, 11, 4))


def test_license_transitions():
    license_ = make_license()
    license_.suspend(TODAY)
    assert license_.status is LicenseStatus.SUSPENDED
    with pytest.raises(DomainError) as error:
        license_.suspend(TODAY)
    assert error_type(error) is InvalidLicenseTransition
    license_.resume(TODAY)
    license_.revoke("нарушение", TODAY)
    assert license_.status is LicenseStatus.REVOKED and license_.revoke_reason == "нарушение"
    with pytest.raises(DomainError):
        license_.resume(TODAY)


def test_license_renew_window():
    license_ = make_license()
    with pytest.raises(DomainError) as error:
        license_.renew(TODAY)
    assert error_type(error) is RenewalTooEarly
    license_.renew(date(2027, 10, 4))   
    assert license_.valid_until == date(2028, 11, 3)
    with pytest.raises(DomainError) as error:
        make_license(valid_until=date(2026, 11, 1)).renew(TODAY)
    assert error_type(error) is InvalidLicenseTransition


def test_ensure_can_issue():
    ensure_can_issue(True, [], FlightRank.ROOKIE)
    ensure_can_issue(True, [make_license(FlightRank.PILOT)], FlightRank.PRO)
    with pytest.raises(DomainError) as error:
        ensure_can_issue(False, [], FlightRank.ROOKIE)
    assert error_type(error) is CustomerUnderage
    for existing in (FlightRank.PRO, FlightRank.ACE):
        with pytest.raises(DomainError) as error:
            ensure_can_issue(True, [make_license(existing)], FlightRank.PRO)
        assert error_type(error) is ActiveLicenseExists


def test_customer_adulthood():
    customer = Customer.register(
        full_name="x", phone="+79990000000", email=None, birth_date=date(2008, 11, 3), now=NOW
    )
    assert customer.is_adult_on(TODAY) and not customer.is_adult_on(date(2026, 11, 2))


@pytest.mark.parametrize(
    "license_,code",
    [
        (None, NoLicense),
        (make_license(status=LicenseStatus.REVOKED, revoke_reason="x"), NoLicense),
        (make_license(status=LicenseStatus.SUSPENDED), LicenseSuspended),
        (make_license(valid_until=date(2026, 11, 2)), LicenseExpired),
        (make_license(FlightRank.PILOT), LicenseRankTooLow),
    ],
)
def test_drone_sell_rejections(license_, code):
    drone = make_drone()
    with pytest.raises(DomainError) as error:
        drone.sell(customer_id=uuid.uuid4(), last_license=license_, now=NOW, today=TODAY)
    assert (
        error_type(error) is code
        and drone.status is DroneStatus.IN_STOCK
        and drone.customer_id is None
    )


def test_drone_sell_success_fixes_price_and_license():
    drone, license_, buyer = make_drone(price=777), make_license(FlightRank.ACE), uuid.uuid4()
    drone.sell(customer_id=buyer, last_license=license_, now=NOW, today=TODAY)
    assert (
        drone.status,
        drone.customer_id,
        drone.sold_price,
        drone.sold_license_id,
        drone.sold_at,
    ) == (
        DroneStatus.SOLD,
        buyer,
        777,
        license_.id,
        NOW,
    )
    drone.price = 1 
    assert drone.sold_price == 777
    with pytest.raises(DomainError) as error:
        drone.sell(customer_id=buyer, last_license=license_, now=NOW, today=TODAY)
    assert error_type(error) is DroneNotAvailable


def test_drone_apply_update_rules():
    drone = make_drone()
    assert drone.apply_update({"purpose": DronePurpose.CAMERA, "price": 9}, NOW) is True
    assert drone.price == 9 and drone.purpose is DronePurpose.CAMERA
    assert drone.apply_update({"price": 10}, NOW) is False
    with pytest.raises(DomainError) as error:
        drone.apply_update({"status": DroneStatus.SOLD}, NOW)
    assert error_type(error) is InvalidDroneStatus
    with pytest.raises(ValueError):
        drone.apply_update({"customer_id": uuid.uuid4()}, NOW)
    drone.sell(customer_id=uuid.uuid4(), last_license=make_license(), now=NOW, today=TODAY)
    drone.purpose = DronePurpose.FPV
    with pytest.raises(DomainError) as error:
        drone.apply_update({"price": 1}, NOW)
    assert error_type(error) is DroneSold


def test_part_rules():
    fpv_drone, camera_drone = make_drone(), make_drone(purpose=DronePurpose.CAMERA)
    part = Part.register(name="p", purpose=DronePurpose.FPV, price=1, now=NOW)
    part.attach_to(fpv_drone)
    assert part.drone_id == fpv_drone.id
    with pytest.raises(DomainError) as error:
        part.apply_update({"drone_id": camera_drone.id}, camera_drone)
    assert error_type(error) is PartAlreadyAttached
    with pytest.raises(DomainError) as error:
        part.apply_update({"purpose": DronePurpose.CAMERA}, fpv_drone)
    assert error_type(error) is PartPurposeMismatch
    part.apply_update(
        {"drone_id": None, "purpose": DronePurpose.CAMERA}, None
    )
    assert part.drone_id is None and part.purpose is DronePurpose.CAMERA
    with pytest.raises(DomainError) as error:
        Part.register(name="q", purpose=DronePurpose.FPV, price=1, now=NOW).attach_to(camera_drone)
    assert error_type(error) is PartPurposeMismatch
