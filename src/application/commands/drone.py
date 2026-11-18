from dataclasses import dataclass

from src.domain.enums import DronePurpose, FlightRank


@dataclass(slots=True, frozen=True)
class NewDrone:
    """Данные нового дрона"""

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
