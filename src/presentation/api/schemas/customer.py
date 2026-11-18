import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from src.domain.enums import FlightRank
from src.domain.rules import MSK
from src.presentation.api.schemas.common import (
    FullNameStr,
    MskDatetime,
    PatchModel,
    Phone,
    StrictModel,
)


def _check_not_future(value: date) -> date:
    """Запрещает дату рождения в будущем"""
    if value > datetime.now(MSK).date():
        raise ValueError("Дата рождения не может быть в будущем")
    return value


class CustomerCreate(StrictModel):
    """Тело POST /customers"""

    full_name: FullNameStr
    phone: Phone
    email: EmailStr | None = None
    birth_date: date

    _birth_date_ok = field_validator("birth_date")(_check_not_future)


class CustomerUpdate(PatchModel):
    """Тело PATCH /customers/{id}"""

    nullable_fields = frozenset({"email"})

    full_name: FullNameStr | None = None
    phone: Phone | None = None
    email: EmailStr | None = None
    birth_date: date | None = None

    @field_validator("birth_date")
    @classmethod
    def _birth_date_ok(cls, value: date | None) -> date | None:
        """Запрещает дату рождения в будущем"""
        return None if value is None else _check_not_future(value)


class CustomerRead(BaseModel):
    """Покупатель в ответах: `rank` считается при каждом ответе"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    phone: str
    email: str | None
    birth_date: date
    rank: FlightRank | None = None
    created_at: MskDatetime
