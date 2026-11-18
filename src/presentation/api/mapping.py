from collections.abc import Callable

from pydantic import BaseModel

from src.application.dto import Page as AppPage
from src.presentation.api.schemas.common import Page


def to_page[T, S: BaseModel](page: AppPage[T], schema: type[S]) -> Page[S]:
    """Собирает ответ-список из страницы приложения"""
    convert: Callable[[T], S] = schema.model_validate
    return Page[S](
        items=[convert(i) for i in page.items],
        total=page.total,
        limit=page.pagination.limit,
        offset=page.pagination.offset,
    )
