from pydantic import (
    BaseModel,
)


class Page[T](BaseModel):
    """Список с пагинацией"""

    items: list[T]
    total: int
    limit: int
    offset: int
