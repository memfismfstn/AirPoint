import uuid

from pydantic import BaseModel, ConfigDict, StrictBool

from src.domain.enums import DronePurpose, DroneStatus, FlightRank
from src.presentation.api.schemas.common import (
    ManufacturerStr,
    MskDatetime,
    NameStr,
    PatchModel,
    PositiveInt,
    SkuStr,
    StrictModel,
)


class DroneCreate(StrictModel):
    """Тело POST /drones"""

    sku: SkuStr
    name: NameStr
    manufacturer: ManufacturerStr
    purpose: DronePurpose
    rank: FlightRank
    weight_g: PositiveInt
    max_flight_time_min: PositiveInt
    max_range_m: PositiveInt
    has_camera: StrictBool = False
    price: PositiveInt


class DroneUpdate(PatchModel):
    """Тело PATCH /drones/{id}"""

    sku: SkuStr | None = None
    name: NameStr | None = None
    manufacturer: ManufacturerStr | None = None
    purpose: DronePurpose | None = None
    rank: FlightRank | None = None
    weight_g: PositiveInt | None = None
    max_flight_time_min: PositiveInt | None = None
    max_range_m: PositiveInt | None = None
    has_camera: StrictBool | None = None
    price: PositiveInt | None = None
    status: DroneStatus | None = None


class PurchaseRequest(StrictModel):
    """Тело POST /drones/{id}/purchase"""

    customer_id: uuid.UUID


class DroneRead(BaseModel):
    """Дрон в ответах"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sku: str
    name: str
    manufacturer: str
    purpose: DronePurpose
    rank: FlightRank
    weight_g: int
    max_flight_time_min: int
    max_range_m: int
    has_camera: bool
    price: int
    status: DroneStatus
    customer_id: uuid.UUID | None
    sold_at: MskDatetime | None
    sold_price: int | None
    sold_license_id: uuid.UUID | None
    created_at: MskDatetime
    updated_at: MskDatetime
