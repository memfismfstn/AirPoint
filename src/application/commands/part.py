import uuid
from dataclasses import dataclass

from src.domain.enums import DronePurpose


@dataclass(slots=True, frozen=True)
class NewPart:
    """Данные новой запчасти"""

    name: str
    purpose: DronePurpose
    price: int
    drone_id: uuid.UUID | None = None
