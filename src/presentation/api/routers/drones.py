import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.exceptions import RequestValidationError

from src.application.commands import NewDrone
from src.application.dto import DroneFilter
from src.application.use_cases.drones import (
    CreateDrone,
    GetDrone,
    ListDroneParts,
    ListDrones,
    PurchaseDrone,
    UpdateDrone,
)
from src.domain.enums import DronePurpose, DroneStatus, FlightRank
from src.presentation.api.dependencies import PageDep, provide
from src.presentation.api.mapping import to_page
from src.presentation.api.schemas.common import ERROR_RESPONSES, Page
from src.presentation.api.schemas.drone import (
    DroneCreate,
    DroneRead,
    DroneUpdate,
    PurchaseRequest,
)
from src.presentation.api.schemas.part import PartRead

router = APIRouter(prefix="/drones", tags=["Дроны"])

CreateUC = Annotated[CreateDrone, Depends(provide(CreateDrone))]
GetUC = Annotated[GetDrone, Depends(provide(GetDrone))]
ListUC = Annotated[ListDrones, Depends(provide(ListDrones))]
UpdateUC = Annotated[UpdateDrone, Depends(provide(UpdateDrone))]
PartsUC = Annotated[ListDroneParts, Depends(provide(ListDroneParts))]
PurchaseUC = Annotated[PurchaseDrone, Depends(provide(PurchaseDrone))]


@router.post(
    "", response_model=DroneRead, status_code=status.HTTP_201_CREATED, responses=ERROR_RESPONSES
)
async def create_drone(data: DroneCreate, uc: CreateUC) -> DroneRead:
    """Добавить дрон (статус `in_stock`, владельца нет)"""
    return DroneRead.model_validate(await uc.execute(NewDrone(**data.model_dump())))


@router.get("", response_model=Page[DroneRead])
async def list_drones(
    uc: ListUC,
    page: PageDep,
    purpose: DronePurpose | None = None,
    rank: Annotated[FlightRank | None, Query(description="Ровно этот ранг")] = None,
    max_rank: Annotated[FlightRank | None, Query(description="Ранг не выше указанного")] = None,
    status: DroneStatus | None = None,
    manufacturer: Annotated[str | None, Query(description="Без учёта регистра")] = None,
    has_camera: bool | None = None,
    min_price: Annotated[int | None, Query(ge=0, description="Копейки, включительно")] = None,
    max_price: Annotated[int | None, Query(ge=0, description="Копейки, включительно")] = None,
    customer_id: uuid.UUID | None = None,
) -> Page[DroneRead]:
    """Список дронов с фильтрами (комбинируются через «И») и пагинацией"""
    if min_price is not None and max_price is not None and min_price > max_price:
        raise RequestValidationError(
            [
                {
                    "type": "value_error",
                    "loc": ("query", "min_price"),
                    "msg": "min_price не может быть больше max_price",
                    "input": min_price,
                }
            ]
        )
    flt = DroneFilter(
        purpose=purpose,
        rank=rank,
        max_rank=max_rank,
        status=status,
        manufacturer=manufacturer,
        has_camera=has_camera,
        min_price=min_price,
        max_price=max_price,
        customer_id=customer_id,
    )
    return to_page(await uc.execute(flt, page), DroneRead)


@router.get("/{drone_id}", response_model=DroneRead, responses=ERROR_RESPONSES)
async def get_drone(drone_id: uuid.UUID, uc: GetUC) -> DroneRead:
    """Один дрон"""
    return DroneRead.model_validate(await uc.execute(drone_id))


@router.patch("/{drone_id}", response_model=DroneRead, responses=ERROR_RESPONSES)
async def update_drone(drone_id: uuid.UUID, data: DroneUpdate, uc: UpdateUC) -> DroneRead:
    """Изменить дрон; `status` — только `in_stock` или `withdrawn`, проданный не меняется"""
    changes = data.model_dump(exclude_unset=True)
    return DroneRead.model_validate(await uc.execute(drone_id, changes))


@router.get("/{drone_id}/parts", response_model=Page[PartRead], responses=ERROR_RESPONSES)
async def list_drone_parts(drone_id: uuid.UUID, uc: PartsUC, page: PageDep) -> Page[PartRead]:
    """Запчасти дрона"""
    return to_page(await uc.execute(drone_id, page), PartRead)


@router.post("/{drone_id}/purchase", response_model=DroneRead, responses=ERROR_RESPONSES)
async def purchase_drone(drone_id: uuid.UUID, data: PurchaseRequest, uc: PurchaseUC) -> DroneRead:
    """Купить дрон: проверяется последняя лицензия покупателя"""
    return DroneRead.model_validate(await uc.execute(drone_id, data.customer_id))
