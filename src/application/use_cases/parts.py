import uuid
from typing import Any

from src.application.commands import NewPart
from src.application.dto import Page, Pagination
from src.application.use_cases.base import UseCase, require_drone, require_part
from src.domain.entities.part import Part
from src.domain.enums import DronePurpose


class CreatePart(UseCase):
    """Добавляет запчасть"""

    async def execute(self, cmd: NewPart) -> Part:
        """Создаёт запчасть, при необходимости сразу привязывая к дрону

        Args:
            cmd: Данные запчасти

        Returns:
            Созданная запчасть

        Raises:
            DomainError: Дрона нет или тип запчасти не совпадает с типом дрона
        """
        now, _ = self.moment()
        async with self.uow as uow:
            await uow.begin_write()
            part = Part.register(name=cmd.name, purpose=cmd.purpose, price=cmd.price, now=now)
            if cmd.drone_id is not None:
                part.attach_to(await require_drone(uow, cmd.drone_id))
            await uow.parts.add(part)
            await uow.commit()
        return part


class GetPart(UseCase):
    """Возвращает одну запчасть"""

    async def execute(self, part_id: uuid.UUID) -> Part:
        """Находит запчасть

        Args:
            part_id: Идентификатор запчасти

        Returns:
            Запчасть

        Raises:
            DomainError: Запчасти нет
        """
        async with self.uow as uow:
            return await require_part(uow, part_id)


class ListParts(UseCase):
    """Возвращает страницу запчастей"""

    async def execute(
        self, purpose: DronePurpose | None, attached: bool | None, page: Pagination
    ) -> Page[Part]:
        """Ищет запчасти по типу и признаку привязки

        Args:
            purpose: Тип запчасти
            attached: True — привязанные, False — свободные
            page: Параметры пагинации

        Returns:
            Страница запчастей
        """
        async with self.uow as uow:
            return await uow.parts.list(purpose, attached, page)


class UpdatePart(UseCase):
    """Меняет запчасть"""

    async def execute(self, part_id: uuid.UUID, changes: dict[str, Any]) -> Part:
        """Меняет запчасть, привязывает её к дрону (`drone_id`) или отвязывает (`None`)

        Args:
            part_id: Идентификатор запчасти
            changes: Меняемые поля (только переданные в запросе)

        Returns:
            Обновлённая запчасть

        Raises:
            DomainError: Запчасти или дрона нет, она привязана к другому дрону,
                типы не совпадают
        """
        async with self.uow as uow:
            await uow.begin_write()
            part = await require_part(uow, part_id, for_update=True)
            target_id = changes["drone_id"] if "drone_id" in changes else part.drone_id
            target = None if target_id is None else await require_drone(uow, target_id)
            part.apply_update(changes, target)
            await uow.parts.save(part)
            await uow.commit()
        return part


class DeletePart(UseCase):
    """Удаляет запчасть"""

    async def execute(self, part_id: uuid.UUID) -> None:
        """Удаляет запчасть

        Args:
            part_id: Идентификатор запчасти

        Raises:
            DomainError: Запчасти нет
        """
        async with self.uow as uow:
            await uow.begin_write()
            part = await require_part(uow, part_id, for_update=True)
            await uow.parts.delete(part)
            await uow.commit()
