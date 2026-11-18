from typing import Any

from fastapi import status
from pydantic import (
    BaseModel,
)


class ErrorDetail(BaseModel):
    """Тело ошибки 404 или 409"""

    code: str
    message: str


class ErrorResponse(BaseModel):
    """Ответ с ошибкой 404 или 409"""

    detail: ErrorDetail


ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Объект не найден"},
    status.HTTP_409_CONFLICT: {"model": ErrorResponse, "description": "Нарушено бизнес-правило"},
}
