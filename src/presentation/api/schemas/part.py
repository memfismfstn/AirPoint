import uuid

from pydantic import BaseModel, ConfigDict

from src.domain.enums import DronePurpose
from src.presentation.api.schemas.common import NameStr, PatchModel, PositiveInt, StrictModel


class PartCreate(StrictModel):
    """Тело POST /parts"""

    name: NameStr
    purpose: DronePurpose
    price: PositiveInt
    drone_id: uuid.UUID | None = None


class PartUpdate(PatchModel):
    """Тело PATCH /parts/{id}: `drone_id: null` отвязывает запчасть"""

    nullable_fields = frozenset({"drone_id"})

    name: NameStr | None = None
    purpose: DronePurpose | None = None
    price: PositiveInt | None = None
    drone_id: uuid.UUID | None = None


class PartRead(BaseModel):
    """Запчасть в ответах"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    purpose: DronePurpose
    price: int
    drone_id: uuid.UUID | None
