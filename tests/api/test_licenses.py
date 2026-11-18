import asyncio
import re
from datetime import UTC, datetime

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db.base import Base
from src.infrastructure.db.models import LicenseDailyCounterOrm
from src.infrastructure.db.session import build_engine, build_session_factory
from src.infrastructure.uow import SqlAlchemyUnitOfWork
from src.main import app
from src.presentation.api.dependencies import get_clock, get_uow
from tests.conftest import Clock
from tests.helpers import API, code, make_customer, make_drone, make_license


async def test_issue_license_basics(client: AsyncClient, clock: Clock):
    customer = await make_customer(client)
    issued_license = await make_license(client, customer["id"], "PRO")
    assert re.fullmatch(r"drl_[0-9a-f]{32}", issued_license["key"])
    assert issued_license["status"] == "active" and issued_license["revoke_reason"] is None
    assert (
        issued_license["valid_until"] == "2027-11-03"
        and issued_license["issued_at"] == "2026-11-03T12:00:00+03:00"
    )

    response = await client.post(
        f"{API}/licenses", json={"customer_id": customer["id"], "rank": "PRO"}
    )
    assert response.status_code == 409 and code(response) == "ACTIVE_LICENSE_EXISTS"
    response = await client.post(
        f"{API}/licenses", json={"customer_id": customer["id"], "rank": "ROOKIE"}
    )
    assert code(response) == "ACTIVE_LICENSE_EXISTS"
    for invalid in ({"rank": "GOD"}, {"key": "drl_x"}, {"customer_id": "nope"}):
        body = {"customer_id": customer["id"], "rank": "ACE"} | invalid
        assert (await client.post(f"{API}/licenses", json=body)).status_code == 422
    response = await client.post(
        f"{API}/licenses",
        json={"customer_id": "3f2a9c1e-7b4d-4e0a-9f1c-2b3d4e5f6a7b", "rank": "ACE"},
    )
    assert response.status_code == 404 and code(response) == "CUSTOMER_NOT_FOUND"


async def test_underage_and_birthday_boundary(client: AsyncClient, clock: Clock):
    minor = await make_customer(client, phone="+79990000001", birth_date="2008-11-04")
    response = await client.post(
        f"{API}/licenses", json={"customer_id": minor["id"], "rank": "ROOKIE"}
    )
    assert response.status_code == 409 and code(response) == "CUSTOMER_UNDERAGE"
    adult = await make_customer(client, phone="+79990000002", birth_date="2008-11-03")
    response = await client.post(
        f"{API}/licenses", json={"customer_id": adult["id"], "rank": "ROOKIE"}
    )
    assert response.status_code == 201


async def test_upgrade_revokes_old_license(client: AsyncClient, clock: Clock):
    customer = await make_customer(client)
    old = await make_license(client, customer["id"], "PILOT")
    clock.set(2026, 11, 3, 10, 0)
    new = await make_license(client, customer["id"], "ACE")
    got = (await client.get(f"{API}/licenses/{old['id']}")).json()
    assert got["status"] == "revoked" and got["revoke_reason"] == "заменена новой лицензией"
    assert new["status"] == "active"
    assert (await client.get(f"{API}/customers/{customer['id']}")).json()["rank"] == "ACE"
    listing = (await client.get(f"{API}/customers/{customer['id']}/licenses")).json()
    assert [item["id"] for item in listing["items"]] == [new["id"], old["id"]]


async def test_suspended_license_blocks_reissue_and_is_replaced_on_upgrade(
    client: AsyncClient, clock: Clock
):
    customer = await make_customer(client)
    issued_license = await make_license(client, customer["id"], "PILOT")
    await client.post(f"{API}/licenses/{issued_license['id']}/suspend")
    response = await client.post(
        f"{API}/licenses", json={"customer_id": customer["id"], "rank": "PILOT"}
    )
    assert code(response) == "ACTIVE_LICENSE_EXISTS"
    await make_license(client, customer["id"], "PRO")
    assert (await client.get(f"{API}/licenses/{issued_license['id']}")).json()[
        "status"
    ] == "revoked"


async def test_daily_limit_moscow_day(client: AsyncClient, clock: Clock):
    people = [await make_customer(client, phone=f"+7999000000{i}") for i in range(6)]
    clock.set(2026, 11, 3, 20, 59)  # 23:59 по Москве, ещё 3 ноября
    for person in people[:3]:
        await make_license(client, person["id"], "ROOKIE")
    response = await client.post(
        f"{API}/licenses", json={"customer_id": people[3]["id"], "rank": "ROOKIE"}
    )
    assert response.status_code == 409 and code(response) == "DAILY_LIMIT_REACHED"
    clock.set(2026, 11, 3, 21, 1)  # 00:01 по Москве, уже 4 ноября
    await make_license(client, people[3]["id"], "ROOKIE")


async def test_failed_validation_does_not_consume_daily_slot(client: AsyncClient, clock: Clock):
    minor = await make_customer(client, phone="+79990000009", birth_date="2020-01-01")
    for _ in range(5):
        response = await client.post(
            f"{API}/licenses", json={"customer_id": minor["id"], "rank": "ROOKIE"}
        )
        assert code(response) == "CUSTOMER_UNDERAGE"
    for i in range(3):
        person = await make_customer(client, phone=f"+7999000001{i}")
        await make_license(client, person["id"], "ROOKIE")


async def test_upgrade_counts_in_daily_limit(client: AsyncClient, clock: Clock):
    customer_a = await make_customer(client, phone="+79990000001")
    customer_b = await make_customer(client, phone="+79990000002")
    await make_license(client, customer_a["id"], "ROOKIE")
    await make_license(client, customer_b["id"], "ROOKIE")
    await make_license(client, customer_a["id"], "PILOT")
    response = await client.post(
        f"{API}/licenses", json={"customer_id": customer_b["id"], "rank": "PILOT"}
    )
    assert code(response) == "DAILY_LIMIT_REACHED"
    """отказ не должен отозвать старую лицензию"""
    assert (await client.get(f"{API}/customers/{customer_b['id']}")).json()["rank"] == "ROOKIE"


async def test_expiry_is_lazy_and_consistent(client: AsyncClient, clock: Clock):
    customer = await make_customer(client)
    issued_license = await make_license(client, customer["id"], "PRO")
    drone = await make_drone(client, rank="ROOKIE", purpose="toy")

    clock.set(2027, 11, 3, 20, 0)  # 23:00 по Москве, последний день
    assert (await client.get(f"{API}/licenses/{issued_license['id']}")).json()["status"] == "active"

    clock.set(2027, 11, 3, 21, 0)  # 00:00 по Москве, 4 ноября 2027
    assert (await client.get(f"{API}/licenses/{issued_license['id']}")).json()[
        "status"
    ] == "expired"
    assert (await client.get(f"{API}/licenses", params={"status": "expired"})).json()["total"] == 1
    assert (await client.get(f"{API}/licenses", params={"status": "active"})).json()["total"] == 0
    assert (await client.get(f"{API}/customers/{customer['id']}")).json()["rank"] is None
    response = await client.post(
        f"{API}/drones/{drone['id']}/purchase", json={"customer_id": customer["id"]}
    )
    assert code(response) == "LICENSE_EXPIRED"
    for action, body in (
        ("suspend", None),
        ("resume", None),
        ("revoke", {"reason": "x"}),
        ("renew", None),
    ):
        response = await client.post(f"{API}/licenses/{issued_license['id']}/{action}", json=body)
        assert response.status_code == 409 and code(response) == "INVALID_LICENSE_TRANSITION", (
            action
        )
    """после истечения можно выдать новую лицензию"""
    assert (
        await client.post(f"{API}/licenses", json={"customer_id": customer["id"], "rank": "PRO"})
    ).status_code == 201


async def test_suspend_resume_revoke(client: AsyncClient, clock: Clock):
    customer = await make_customer(client)
    issued_license = await make_license(client, customer["id"], "PILOT")
    url = f"{API}/licenses/{issued_license['id']}"
    assert code(await client.post(f"{url}/resume")) == "INVALID_LICENSE_TRANSITION"
    assert (await client.post(f"{url}/suspend")).json()["status"] == "suspended"
    assert code(await client.post(f"{url}/suspend")) == "INVALID_LICENSE_TRANSITION"
    assert (await client.get(f"{API}/customers/{customer['id']}")).json()["rank"] is None
    assert (await client.post(f"{url}/resume")).json()["status"] == "active"
    assert (await client.post(f"{url}/revoke", json={})).status_code == 422
    assert (await client.post(f"{url}/revoke", json={"reason": "   "})).status_code == 422
    response = await client.post(f"{url}/revoke", json={"reason": "Нарушение правил полётов"})
    assert (
        response.json()["status"] == "revoked"
        and response.json()["revoke_reason"] == "Нарушение правил полётов"
    )
    assert (
        code(await client.post(f"{url}/revoke", json={"reason": "ещё раз"}))
        == "INVALID_LICENSE_TRANSITION"
    )
    assert code(await client.post(f"{url}/resume")) == "INVALID_LICENSE_TRANSITION"
    ghost = f"{API}/licenses/3f2a9c1e-7b4d-4e0a-9f1c-2b3d4e5f6a7b"
    assert (await client.get(ghost)).status_code == 404
    assert code(await client.post(f"{ghost}/suspend")) == "LICENSE_NOT_FOUND"


async def test_suspended_expiring_license_becomes_expired(client: AsyncClient, clock: Clock):
    customer = await make_customer(client)
    issued_license = await make_license(client, customer["id"], "PILOT")
    await client.post(f"{API}/licenses/{issued_license['id']}/suspend")
    clock.set(2027, 11, 5, 0, 0)
    assert (await client.get(f"{API}/licenses/{issued_license['id']}")).json()[
        "status"
    ] == "expired"
    assert (
        code(await client.post(f"{API}/licenses/{issued_license['id']}/resume"))
        == "INVALID_LICENSE_TRANSITION"
    )


async def test_renew(client: AsyncClient, clock: Clock):
    customer = await make_customer(client)
    issued_license = await make_license(client, customer["id"], "PRO")
    url = f"{API}/licenses/{issued_license['id']}/renew"
    response = await client.post(url)
    assert response.status_code == 409 and code(response) == "RENEWAL_TOO_EARLY"

    clock.set(2027, 10, 4, 9, 0)
    response = await client.post(url)
    assert response.status_code == 200
    assert (
        response.json()["valid_until"] == "2028-11-03"
        and response.json()["key"] == issued_license["key"]
    )
    assert response.json()["status"] == "active" and response.json()["rank"] == "PRO"
    assert code(await client.post(url)) == "RENEWAL_TOO_EARLY"

    await client.post(f"{API}/licenses/{issued_license['id']}/suspend")
    assert code(await client.post(url)) == "INVALID_LICENSE_TRANSITION"
    assert (
        code(await client.post(f"{API}/licenses/3f2a9c1e-7b4d-4e0a-9f1c-2b3d4e5f6a7b/renew"))
        == "LICENSE_NOT_FOUND"
    )


async def test_renew_does_not_use_daily_limit(client: AsyncClient, clock: Clock):
    customer = await make_customer(client)
    issued_license = await make_license(client, customer["id"], "PRO")
    for i in range(2):
        person = await make_customer(client, phone=f"+7999000002{i}")
        await make_license(client, person["id"], "ROOKIE")
    clock.set(2027, 10, 10, 9, 0)
    assert (await client.post(f"{API}/licenses/{issued_license['id']}/renew")).status_code == 200


async def test_license_list_filters(client: AsyncClient, clock: Clock):
    customer_a = await make_customer(client, phone="+79990000001")
    customer_b = await make_customer(client, phone="+79990000002")
    license_a = await make_license(client, customer_a["id"], "PILOT")
    clock.set(2026, 11, 3, 10, 0)
    license_b = await make_license(client, customer_b["id"], "PRO")
    await client.post(f"{API}/licenses/{license_b['id']}/suspend")

    response = await client.get(f"{API}/licenses")
    assert [item["id"] for item in response.json()["items"]] == [
        license_b["id"],
        license_a["id"],
    ] and response.json()["total"] == 2
    assert (await client.get(f"{API}/licenses", params={"key": license_a["key"]})).json()["items"][
        0
    ]["id"] == license_a["id"]
    assert (await client.get(f"{API}/licenses", params={"key": "drl_nope"})).json()["total"] == 0
    assert (await client.get(f"{API}/licenses", params={"customer_id": customer_b["id"]})).json()[
        "total"
    ] == 1
    assert (await client.get(f"{API}/licenses", params={"status": "suspended"})).json()[
        "total"
    ] == 1
    assert (await client.get(f"{API}/licenses", params={"status": "bogus"})).status_code == 422


async def test_database_itself_rejects_fourth_license(
    session: AsyncSession, client: AsyncClient, clock: Clock
):
    """CHECK в таблице счётчика — страховка, даже если код проверки сломается"""
    import pytest
    from sqlalchemy.exc import IntegrityError

    session.add(LicenseDailyCounterOrm(day=datetime(2026, 11, 3, tzinfo=UTC).date(), issued=4))
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()


async def test_concurrent_issuance_never_exceeds_limit(tmp_path, clock: Clock):
    engine = build_engine(f"sqlite+aiosqlite:///{tmp_path / 'race.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = build_session_factory(engine)
    app.dependency_overrides[get_uow] = lambda: SqlAlchemyUnitOfWork(maker)
    app.dependency_overrides[get_clock] = lambda: clock
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            people = [await make_customer(client, phone=f"+7999000003{i}") for i in range(8)]
            results = await asyncio.gather(
                *[
                    client.post(
                        f"{API}/licenses", json={"customer_id": person["id"], "rank": "ROOKIE"}
                    )
                    for person in people
                ]
            )
            statuses = sorted(response.status_code for response in results)
            assert statuses == [201] * 3 + [409] * 5, [response.text for response in results]
            assert all(
                code(response) == "DAILY_LIMIT_REACHED"
                for response in results
                if response.status_code == 409
            )

            """один покупатель, два параллельных запроса: выдаётся ровно одна лицензия"""
            customer = await make_customer(client, phone="+79990000099")
            clock.set(2026, 11, 4, 9, 0)
            pair = await asyncio.gather(
                *[
                    client.post(
                        f"{API}/licenses", json={"customer_id": customer["id"], "rank": "PRO"}
                    )
                    for _ in range(2)
                ]
            )
            assert sorted(response.status_code for response in pair) == [201, 409]
            assert (
                code(next(response for response in pair if response.status_code == 409))
                == "ACTIVE_LICENSE_EXISTS"
            )

            """один дрон, две параллельные покупки: продаётся ровно один раз"""
            buyers = [await make_customer(client, phone=f"+7999000004{i}") for i in range(2)]
            for customer_b in buyers:
                await make_license(client, customer_b["id"], "PRO")
            drone = await make_drone(client)
            buys = await asyncio.gather(
                *[
                    client.post(
                        f"{API}/drones/{drone['id']}/purchase",
                        json={"customer_id": customer_b["id"]},
                    )
                    for customer_b in buyers
                ]
            )
            assert sorted(response.status_code for response in buys) == [200, 409]
            assert (
                code(next(response for response in buys if response.status_code == 409))
                == "DRONE_NOT_AVAILABLE"
            )

        async with maker() as session:
            rows = {
                counter.day.isoformat(): counter.issued
                for counter in (await session.scalars(select(LicenseDailyCounterOrm))).all()
            }
        assert rows == {"2026-11-03": 3, "2026-11-04": 3}
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
