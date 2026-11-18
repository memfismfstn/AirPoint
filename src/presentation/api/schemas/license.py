import uuid
from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from src.domain.enums import FlightRank, LicenseStatus
from src.presentation.api.schemas.common import MskDatetime, StrictModel


class LicenseCreate(StrictModel):
    """Тело POST /licenses"""

    customer_id: uuid.UUID
    rank: FlightRank


class LicenseRevoke(StrictModel):
    """Тело POST /licenses/{id}/revoke"""

    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class LicenseRead(BaseModel):
    """Лицензия в ответах: статус всегда актуальный, с учётом истечения срока"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    key: str
    customer_id: uuid.UUID
    rank: FlightRank
    status: LicenseStatus
    issued_at: MskDatetime
    valid_until: date
    revoke_reason: str | None
