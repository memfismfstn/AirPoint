from collections.abc import Callable
from dataclasses import dataclass

DEFAULT_PAGE_SIZE = 20


MAX_PAGE_SIZE = 100


@dataclass(slots=True, frozen=True)
class Pagination:
    """Параметры пагинации"""

    limit: int
    offset: int


@dataclass(slots=True)
class Page[T]:
    """Страница результатов"""

    items: list[T]
    total: int
    pagination: Pagination

    def map[R](self, func: Callable[[T], R]) -> Page[R]:
        """Преобразует каждый элемент страницы"""
        return Page(
            items=[func(item) for item in self.items],
            total=self.total,
            pagination=self.pagination,
        )
