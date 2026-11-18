from typing import Any

from httpx import AsyncClient

API = "/api/v1"

DRONE = {
    "sku": "DJI-MINI4-0001",
    "name": "DJI Mini 4 Pro",
    "manufacturer": "DJI",
    "purpose": "camera",
    "rank": "PILOT",
    "weight_g": 249,
    "max_flight_time_min": 34,
    "max_range_m": 20000,
    "has_camera": True,
    "price": 8999000,
}


async def make_drone(client: AsyncClient, **overrides: Any) -> dict[str, Any]:
    response = await client.post(f"{API}/drones", json=DRONE | overrides)
    assert response.status_code == 201, response.text
    return response.json()


async def make_customer(
    client: AsyncClient,
    phone: str = "+79161234567",
    birth_date: str = "1995-04-12",
    **overrides: Any,
) -> dict[str, Any]:
    body = {
        "full_name": "Иванов Иван Иванович",
        "phone": phone,
        "birth_date": birth_date,
    } | overrides
    response = await client.post(f"{API}/customers", json=body)
    assert response.status_code == 201, response.text
    return response.json()


async def make_license(client: AsyncClient, customer_id: str, rank: str = "PRO") -> dict[str, Any]:
    response = await client.post(f"{API}/licenses", json={"customer_id": customer_id, "rank": rank})
    assert response.status_code == 201, response.text
    return response.json()


def code(response: Any) -> str:
    return response.json()["detail"]["code"]
