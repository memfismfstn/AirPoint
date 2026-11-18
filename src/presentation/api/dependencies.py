from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Query

from src.application.dto import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, Pagination
from src.application.interfaces import Clock, UnitOfWork
from src.application.use_cases.base import UseCase


def get_uow() -> UnitOfWork:
    """Возвращает единицу работы на запрос"""
    raise NotImplementedError


def get_clock() -> Clock:
    """Возвращает источник времени"""
    raise NotImplementedError


def provide[U: UseCase](use_case_cls: type[U]) -> Callable[..., U]:
    """Строит зависимость, которая собирает сценарий из единицы работы и часов"""

    def factory(
        uow: Annotated[UnitOfWork, Depends(get_uow)],
        clock: Annotated[Clock, Depends(get_clock)],
    ) -> U:
        return use_case_cls(uow, clock)

    return factory


def page_params(
    limit: Annotated[
        int, Query(ge=1, le=MAX_PAGE_SIZE, description="Размер страницы")
    ] = DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0, description="Сколько объектов пропустить")] = 0,
) -> Pagination:
    """Читает и проверяет `limit` и `offset`"""
    return Pagination(limit=limit, offset=offset)


PageDep = Annotated[Pagination, Depends(page_params)]
