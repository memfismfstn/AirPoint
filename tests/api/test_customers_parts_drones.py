import pytest
from httpx import AsyncClient

from tests.helpers import API, code, make_customer, make_drone, make_license


async def test_customer_crud_and_validation(client: AsyncClient):
    customer = await make_customer(client, email="a@b.ru")
    assert customer["rank"] is None and customer["created_at"].endswith("+03:00")

    response = await client.post(
        f"{API}/customers",
        json={"full_name": "X", "phone": customer["phone"], "birth_date": "1990-01-01"},
    )
    assert response.status_code == 409 and code(response) == "PHONE_ALREADY_EXISTS"

    for invalid in (
        {"phone": "89161234567"},
        {"phone": "+7916123456"},
        {"birth_date": "2999-01-01"},
        {"extra": 1},
    ):
        body = {"full_name": "X", "phone": "+79990000000", "birth_date": "1990-01-01"} | invalid
        assert (await client.post(f"{API}/customers", json=body)).status_code == 422

    response = await client.get(f"{API}/customers", params={"phone": "+70000000000"})
    assert (
        response.status_code == 200
        and response.json()["items"] == []
        and response.json()["total"] == 0
    )
    response = await client.get(f"{API}/customers", params={"phone": customer["phone"]})
    assert response.json()["items"][0]["id"] == customer["id"]

    assert (await client.get(f"{API}/customers/{customer['id']}")).json()["email"] == "a@b.ru"
    response = await client.get(f"{API}/customers/3f2a9c1e-7b4d-4e0a-9f1c-2b3d4e5f6a7b")
    assert response.status_code == 404 and code(response) == "CUSTOMER_NOT_FOUND"

    response = await client.patch(
        f"{API}/customers/{customer['id']}", json={"email": None, "full_name": "Новое"}
    )
    assert response.json()["email"] is None and response.json()["full_name"] == "Новое"
    assert (
        await client.patch(f"{API}/customers/{customer['id']}", json={"full_name": None})
    ).status_code == 422
    other = await make_customer(client, phone="+79990000001")
    response = await client.patch(
        f"{API}/customers/{other['id']}", json={"phone": customer["phone"]}
    )
    assert code(response) == "PHONE_ALREADY_EXISTS"


async def test_customer_rank_and_birth_date_patch(client: AsyncClient):
    customer = await make_customer(client, birth_date="2000-01-01")
    await make_license(client, customer["id"], "PRO")
    assert (await client.get(f"{API}/customers/{customer['id']}")).json()["rank"] == "PRO"
    assert (await client.get(f"{API}/customers")).json()["items"][0]["rank"] == "PRO"
    response = await client.patch(
        f"{API}/customers/{customer['id']}", json={"birth_date": "2015-01-01"}
    )
    assert response.status_code == 409 and code(response) == "CUSTOMER_UNDERAGE"
    response = await client.patch(
        f"{API}/customers/{customer['id']}", json={"birth_date": "1990-05-05"}
    )
    assert response.status_code == 200
    response = await client.get(f"{API}/customers/{customer['id']}/licenses")
    assert response.json()["total"] == 1
    assert (
        await client.get(f"{API}/customers/3f2a9c1e-7b4d-4e0a-9f1c-2b3d4e5f6a7b/licenses")
    ).status_code == 404


async def test_drone_crud_filters_and_pagination(client: AsyncClient):
    drone = await make_drone(client)
    response = await client.post(
        f"{API}/drones", json={**drone, "id": "x"} | {"sku": "DJI-MINI4-0001"}
    )
    assert response.status_code == 422
    from tests.helpers import DRONE

    response = await client.post(f"{API}/drones", json=DRONE)
    assert response.status_code == 409 and code(response) == "SKU_ALREADY_EXISTS"
    assert (
        drone["status"] == "in_stock" and drone["customer_id"] is None and drone["sold_at"] is None
    )
    await make_drone(
        client,
        sku="B",
        purpose="fpv",
        rank="PRO",
        price=100,
        manufacturer="Геоскан",
        has_camera=False,
    )
    await make_drone(
        client,
        sku="C",
        purpose="toy",
        rank="ROOKIE",
        price=50,
        manufacturer="DJI",
        has_camera=False,
    )

    def ids(response):
        return {item["sku"] for item in response.json()["items"]}

    assert ids(await client.get(f"{API}/drones", params={"max_rank": "PILOT"})) == {
        "DJI-MINI4-0001",
        "C",
    }
    assert ids(await client.get(f"{API}/drones", params={"rank": "PRO"})) == {"B"}
    assert ids(await client.get(f"{API}/drones", params={"manufacturer": "dji"})) == {
        "DJI-MINI4-0001",
        "C",
    }
    assert ids(await client.get(f"{API}/drones", params={"manufacturer": "геоскан"})) == {"B"}
    assert ids(await client.get(f"{API}/drones", params={"has_camera": "false"})) == {"B", "C"}
    assert ids(await client.get(f"{API}/drones", params={"min_price": 50, "max_price": 100})) == {
        "B",
        "C",
    }
    response = await client.get(f"{API}/drones", params={"limit": 1, "offset": 1})
    assert (
        response.json()["total"] == 3
        and len(response.json()["items"]) == 1
        and response.json()["limit"] == 1
    )
    for invalid in (
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
        {"min_price": 10, "max_price": 5},
        {"rank": "X"},
    ):
        assert (await client.get(f"{API}/drones", params=invalid)).status_code == 422

    response = await client.patch(
        f"{API}/drones/{drone['id']}", json={"price": 7999000, "status": "withdrawn"}
    )
    assert response.json()["price"] == 7999000 and response.json()["status"] == "withdrawn"
    response = await client.patch(f"{API}/drones/{drone['id']}", json={"status": "sold"})
    assert code(response) == "INVALID_DRONE_STATUS"
    response = await client.patch(f"{API}/drones/{drone['id']}", json={"sku": "C"})
    assert code(response) == "SKU_ALREADY_EXISTS"
    assert (await client.patch(f"{API}/drones/{drone['id']}", json={"price": 0})).status_code == 422
    assert (
        await client.patch(f"{API}/drones/{drone['id']}", json={"price": None})
    ).status_code == 422
    response = await client.get(f"{API}/drones/3f2a9c1e-7b4d-4e0a-9f1c-2b3d4e5f6a7b")
    assert response.status_code == 404 and code(response) == "DRONE_NOT_FOUND"


async def test_parts_rules(client: AsyncClient):
    fpv_drone = await make_drone(client, sku="F", purpose="fpv", rank="PRO")
    camera_drone = await make_drone(client, sku="K")
    base = {"name": "Пропеллеры", "purpose": "fpv", "price": 59000}

    response = await client.post(f"{API}/parts", json=base | {"drone_id": camera_drone["id"]})
    assert code(response) == "PART_PURPOSE_MISMATCH"
    response = await client.post(
        f"{API}/parts", json=base | {"drone_id": "3f2a9c1e-7b4d-4e0a-9f1c-2b3d4e5f6a7b"}
    )
    assert response.status_code == 404 and code(response) == "DRONE_NOT_FOUND"
    part = (await client.post(f"{API}/parts", json=base | {"drone_id": fpv_drone["id"]})).json()
    free = (await client.post(f"{API}/parts", json=base)).json()
    assert free["drone_id"] is None

    assert (await client.get(f"{API}/parts", params={"attached": "true"})).json()["total"] == 1
    assert (await client.get(f"{API}/parts", params={"attached": "false"})).json()["total"] == 1
    assert (await client.get(f"{API}/drones/{fpv_drone['id']}/parts")).json()["total"] == 1

    response = await client.patch(
        f"{API}/parts/{part['id']}", json={"drone_id": camera_drone["id"]}
    )
    assert code(response) == "PART_ALREADY_ATTACHED"
    response = await client.patch(
        f"{API}/parts/{free['id']}", json={"drone_id": camera_drone["id"]}
    )
    assert code(response) == "PART_PURPOSE_MISMATCH"
    response = await client.patch(f"{API}/parts/{part['id']}", json={"purpose": "camera"})
    assert code(response) == "PART_PURPOSE_MISMATCH"
    response = await client.patch(f"{API}/parts/{part['id']}", json={"drone_id": None})
    assert response.json()["drone_id"] is None
    response = await client.patch(
        f"{API}/parts/{part['id']}", json={"drone_id": camera_drone["id"], "purpose": "camera"}
    )
    assert response.status_code == 200 and response.json()["drone_id"] == camera_drone["id"]

    response = await client.patch(f"{API}/parts/{part['id']}", json={"name": None})
    assert response.status_code == 422
    assert (await client.delete(f"{API}/parts/{free['id']}")).status_code == 204
    response = await client.get(f"{API}/parts/{free['id']}")
    assert response.status_code == 404 and code(response) == "PART_NOT_FOUND"
    assert code(await client.delete(f"{API}/parts/{free['id']}")) == "PART_NOT_FOUND"


async def test_purpose_change_detaches_mismatching_parts(client: AsyncClient):
    drone = await make_drone(client, purpose="fpv", rank="PRO")
    first_part = (
        await client.post(
            f"{API}/parts",
            json={"name": "a", "purpose": "fpv", "price": 1, "drone_id": drone["id"]},
        )
    ).json()
    response = await client.patch(f"{API}/drones/{drone['id']}", json={"purpose": "inspection"})
    assert response.status_code == 200
    assert (await client.get(f"{API}/parts/{first_part['id']}")).json()["drone_id"] is None


@pytest.mark.parametrize(
    "rank,drone_rank,expected_ok",
    [("PRO", "PRO", True), ("ACE", "PRO", True), ("PILOT", "PRO", False)],
)
async def test_purchase_rank(client: AsyncClient, rank: str, drone_rank: str, expected_ok: bool):
    customer = await make_customer(client)
    issued_license = await make_license(client, customer["id"], rank)
    drone = await make_drone(client, rank=drone_rank, price=500)
    response = await client.post(
        f"{API}/drones/{drone['id']}/purchase", json={"customer_id": customer["id"]}
    )
    if expected_ok:
        body = response.json()
        assert (
            response.status_code == 200
            and body["status"] == "sold"
            and body["customer_id"] == customer["id"]
        )
        assert (
            body["sold_price"] == 500
            and body["sold_license_id"] == issued_license["id"]
            and body["sold_at"]
        )
        assert (
            code(await client.patch(f"{API}/drones/{drone['id']}", json={"price": 1}))
            == "DRONE_SOLD"
        )
        assert (await client.get(f"{API}/drones", params={"customer_id": customer["id"]})).json()[
            "total"
        ] == 1
        assert (
            code(
                await client.post(
                    f"{API}/drones/{drone['id']}/purchase", json={"customer_id": customer["id"]}
                )
            )
            == "DRONE_NOT_AVAILABLE"
        )
    else:
        assert response.status_code == 409 and code(response) == "LICENSE_RANK_TOO_LOW"
        assert (
            "PRO" in response.json()["detail"]["message"]
            and "PILOT" in response.json()["detail"]["message"]
        )
        assert (await client.get(f"{API}/drones/{drone['id']}")).json()["status"] == "in_stock"


async def test_purchase_license_problems(client: AsyncClient):
    customer = await make_customer(client)
    drone = await make_drone(client, rank="ROOKIE", purpose="toy")
    url = f"{API}/drones/{drone['id']}/purchase"
    body = {"customer_id": customer["id"]}
    assert code(await client.post(url, json=body)) == "NO_LICENSE"
    issued_license = await make_license(client, customer["id"], "PRO")
    await client.post(f"{API}/licenses/{issued_license['id']}/suspend")
    assert code(await client.post(url, json=body)) == "LICENSE_SUSPENDED"
    await client.post(f"{API}/licenses/{issued_license['id']}/revoke", json={"reason": "нарушение"})
    assert code(await client.post(url, json=body)) == "NO_LICENSE"
    response = await client.post(
        f"{API}/drones/3f2a9c1e-7b4d-4e0a-9f1c-2b3d4e5f6a7b/purchase", json=body
    )
    assert code(response) == "DRONE_NOT_FOUND"
    response = await client.post(url, json={"customer_id": "3f2a9c1e-7b4d-4e0a-9f1c-2b3d4e5f6a7b"})
    assert code(response) == "CUSTOMER_NOT_FOUND"
    await client.patch(f"{API}/drones/{drone['id']}", json={"status": "withdrawn"})
    assert code(await client.post(url, json=body)) == "DRONE_NOT_AVAILABLE"
