from fastapi import HTTPException, status


class DomainError(HTTPException):
    """Нарушение бизнес-правила, FastAPI сам превращает его в ответ"""

    status_code: int = status.HTTP_409_CONFLICT
    code: str = "DOMAIN_ERROR"
    default_message: str = "Нарушено бизнес-правило"

    def __init__(self, message: str | None = None, headers: dict[str, str] | None = None) -> None:
        """Создаёт ошибку"""
        message = message or self.default_message
        super().__init__(
            status_code=self.status_code,
            detail={"code": self.code, "message": message},
            headers=headers,
        )
        self.message = message


class NotFoundError(DomainError):
    """Объект не найден"""

    status_code = status.HTTP_404_NOT_FOUND
