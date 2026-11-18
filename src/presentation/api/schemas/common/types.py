from datetime import datetime
from typing import Annotated, Any

from pydantic import (
    Field,
    PlainSerializer,
    StringConstraints,
)

from src.domain.rules import (
    EMAIL_MAX_LENGTH,
    FULL_NAME_MAX_LENGTH,
    MANUFACTURER_MAX_LENGTH,
    MSK,
    NAME_MAX_LENGTH,
    PHONE_PATTERN,
    SKU_MAX_LENGTH,
)


def _to_msk(value: datetime) -> str:
    """Сериализует момент времени в ISO 8601 с московским смещением"""
    return value.astimezone(MSK).isoformat(timespec="seconds")


MskDatetime = Annotated[datetime, PlainSerializer(_to_msk, return_type=str, when_used="json")]


PositiveInt = Annotated[int, Field(gt=0, strict=True)]


Phone = Annotated[str, StringConstraints(pattern=PHONE_PATTERN)]


def _text(max_length: int) -> Any:
    """Строка без пробелов по краям, непустая, не длиннее `max_length`"""
    return Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=max_length)
    ]


SkuStr = _text(SKU_MAX_LENGTH)


ManufacturerStr = _text(MANUFACTURER_MAX_LENGTH)


NameStr = _text(NAME_MAX_LENGTH)


FullNameStr = _text(FULL_NAME_MAX_LENGTH)


EmailStr = _text(EMAIL_MAX_LENGTH)
