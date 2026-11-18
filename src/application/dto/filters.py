import uuid
from dataclasses import dataclass

from src.domain.enums import DronePurpose, DroneStatus, FlightRank, LicenseStatus


@dataclass(slots=True, frozen=True)
class DroneFilter:
    """Фильтры списка дронов, комбинируются через «И»"""

    purpose: DronePurpose | None = None
    rank: FlightRank | None = None
    max_rank: FlightRank | None = None
    status: DroneStatus | None = None
    manufacturer: str | None = None
    has_camera: bool | None = None
    min_price: int | None = None
    max_price: int | None = None
    customer_id: uuid.UUID | None = None


@dataclass(slots=True, frozen=True)
class LicenseFilter:
    """Фильтры списка лицензий"""

    customer_id: uuid.UUID | None = None
    status: LicenseStatus | None = None
    key: str | None = None
