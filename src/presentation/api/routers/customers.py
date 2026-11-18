import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.application.commands import NewCustomer
from src.application.use_cases.customers import (
    CreateCustomer,
    GetCustomer,
    ListCustomerLicenses,
    ListCustomers,
    UpdateCustomer,
)
from src.presentation.api.dependencies import PageDep, provide
from src.presentation.api.mapping import to_page
from src.presentation.api.schemas.common import ERROR_RESPONSES, Page
from src.presentation.api.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate
from src.presentation.api.schemas.license import LicenseRead

router = APIRouter(prefix="/customers", tags=["Покупатели"])

CreateUC = Annotated[CreateCustomer, Depends(provide(CreateCustomer))]
GetUC = Annotated[GetCustomer, Depends(provide(GetCustomer))]
ListUC = Annotated[ListCustomers, Depends(provide(ListCustomers))]
UpdateUC = Annotated[UpdateCustomer, Depends(provide(UpdateCustomer))]
LicensesUC = Annotated[ListCustomerLicenses, Depends(provide(ListCustomerLicenses))]


@router.post(
    "", response_model=CustomerRead, status_code=status.HTTP_201_CREATED, responses=ERROR_RESPONSES
)
async def create_customer(data: CustomerCreate, uc: CreateUC) -> CustomerRead:
    """Добавить покупателя"""
    return CustomerRead.model_validate(await uc.execute(NewCustomer(**data.model_dump())))


@router.get("", response_model=Page[CustomerRead])
async def list_customers(
    uc: ListUC,
    page: PageDep,
    phone: Annotated[str | None, Query(description="Точный телефон")] = None,
) -> Page[CustomerRead]:
    """Список покупателей, поиск по телефону"""
    return to_page(await uc.execute(phone, page), CustomerRead)


@router.get("/{customer_id}", response_model=CustomerRead, responses=ERROR_RESPONSES)
async def get_customer(customer_id: uuid.UUID, uc: GetUC) -> CustomerRead:
    """Один покупатель"""
    return CustomerRead.model_validate(await uc.execute(customer_id))


@router.patch("/{customer_id}", response_model=CustomerRead, responses=ERROR_RESPONSES)
async def update_customer(
    customer_id: uuid.UUID, data: CustomerUpdate, uc: UpdateUC
) -> CustomerRead:
    """Изменить покупателя; новая дата рождения не должна «узаконить» лицензию до 18 лет"""
    changes = data.model_dump(exclude_unset=True)
    return CustomerRead.model_validate(await uc.execute(customer_id, changes))


@router.get("/{customer_id}/licenses", response_model=Page[LicenseRead], responses=ERROR_RESPONSES)
async def list_customer_licenses(
    customer_id: uuid.UUID, uc: LicensesUC, page: PageDep
) -> Page[LicenseRead]:
    """Все лицензии покупателя, включая отозванные и истёкшие"""
    return to_page(await uc.execute(customer_id, page), LicenseRead)
