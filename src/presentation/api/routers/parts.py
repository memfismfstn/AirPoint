import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from src.application.commands import NewPart
from src.application.use_cases.parts import CreatePart, DeletePart, GetPart, ListParts, UpdatePart
from src.domain.enums import DronePurpose
from src.presentation.api.dependencies import PageDep, provide
from src.presentation.api.mapping import to_page
from src.presentation.api.schemas.common import ERROR_RESPONSES, Page
from src.presentation.api.schemas.part import PartCreate, PartRead, PartUpdate

router = APIRouter(prefix="/parts", tags=["Запчасти"])

CreateUC = Annotated[CreatePart, Depends(provide(CreatePart))]
GetUC = Annotated[GetPart, Depends(provide(GetPart))]
ListUC = Annotated[ListParts, Depends(provide(ListParts))]
UpdateUC = Annotated[UpdatePart, Depends(provide(UpdatePart))]
DeleteUC = Annotated[DeletePart, Depends(provide(DeletePart))]


@router.post(
    "", response_model=PartRead, status_code=status.HTTP_201_CREATED, responses=ERROR_RESPONSES
)
async def create_part(data: PartCreate, uc: CreateUC) -> PartRead:
    """Добавить запчасть, при желании сразу привязав к дрону"""
    return PartRead.model_validate(await uc.execute(NewPart(**data.model_dump())))


@router.get("", response_model=Page[PartRead])
async def list_parts(
    uc: ListUC,
    page: PageDep,
    purpose: DronePurpose | None = None,
    attached: bool | None = None,
) -> Page[PartRead]:
    """Список запчастей: `attached=true` — привязанные, `false` — свободные"""
    return to_page(await uc.execute(purpose, attached, page), PartRead)


@router.get("/{part_id}", response_model=PartRead, responses=ERROR_RESPONSES)
async def get_part(part_id: uuid.UUID, uc: GetUC) -> PartRead:
    """Одна запчасть"""
    return PartRead.model_validate(await uc.execute(part_id))


@router.patch("/{part_id}", response_model=PartRead, responses=ERROR_RESPONSES)
async def update_part(part_id: uuid.UUID, data: PartUpdate, uc: UpdateUC) -> PartRead:
    """Изменить, привязать (`drone_id`) или отвязать (`drone_id: null`) запчасть"""
    changes = data.model_dump(exclude_unset=True)
    return PartRead.model_validate(await uc.execute(part_id, changes))


@router.delete("/{part_id}", status_code=status.HTTP_204_NO_CONTENT, responses=ERROR_RESPONSES)
async def delete_part(part_id: uuid.UUID, uc: DeleteUC) -> Response:
    """Удалить запчасть"""
    await uc.execute(part_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
