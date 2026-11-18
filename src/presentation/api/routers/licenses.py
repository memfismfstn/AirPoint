import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.application.dto import LicenseFilter
from src.application.use_cases.licenses import (
    GetLicense,
    IssueLicense,
    ListLicenses,
    RenewLicense,
    ResumeLicense,
    RevokeLicense,
    SuspendLicense,
)
from src.domain.enums import LicenseStatus
from src.presentation.api.dependencies import PageDep, provide
from src.presentation.api.mapping import to_page
from src.presentation.api.schemas.common import ERROR_RESPONSES, Page
from src.presentation.api.schemas.license import LicenseCreate, LicenseRead, LicenseRevoke

router = APIRouter(prefix="/licenses", tags=["Лицензии"])

IssueUC = Annotated[IssueLicense, Depends(provide(IssueLicense))]
GetUC = Annotated[GetLicense, Depends(provide(GetLicense))]
ListUC = Annotated[ListLicenses, Depends(provide(ListLicenses))]
SuspendUC = Annotated[SuspendLicense, Depends(provide(SuspendLicense))]
ResumeUC = Annotated[ResumeLicense, Depends(provide(ResumeLicense))]
RevokeUC = Annotated[RevokeLicense, Depends(provide(RevokeLicense))]
RenewUC = Annotated[RenewLicense, Depends(provide(RenewLicense))]


@router.post(
    "", response_model=LicenseRead, status_code=status.HTTP_201_CREATED, responses=ERROR_RESPONSES
)
async def issue_license(data: LicenseCreate, uc: IssueUC) -> LicenseRead:
    """Выдать лицензию; живая лицензия более низкого ранга отзывается («повышение»)"""
    return LicenseRead.model_validate(await uc.execute(data.customer_id, data.rank))


@router.get("", response_model=Page[LicenseRead])
async def list_licenses(
    uc: ListUC,
    page: PageDep,
    customer_id: uuid.UUID | None = None,
    status: Annotated[LicenseStatus | None, Query(description="С учётом истечения")] = None,
    key: Annotated[str | None, Query(description="Точный ключ")] = None,
) -> Page[LicenseRead]:
    """Список лицензий, поиск по ключу"""
    flt = LicenseFilter(customer_id=customer_id, status=status, key=key)
    return to_page(await uc.execute(flt, page), LicenseRead)


@router.get("/{license_id}", response_model=LicenseRead, responses=ERROR_RESPONSES)
async def get_license(license_id: uuid.UUID, uc: GetUC) -> LicenseRead:
    """Одна лицензия"""
    return LicenseRead.model_validate(await uc.execute(license_id))


@router.post("/{license_id}/suspend", response_model=LicenseRead, responses=ERROR_RESPONSES)
async def suspend_license(license_id: uuid.UUID, uc: SuspendUC) -> LicenseRead:
    """Приостановить действующую лицензию"""
    return LicenseRead.model_validate(await uc.execute(license_id))


@router.post("/{license_id}/resume", response_model=LicenseRead, responses=ERROR_RESPONSES)
async def resume_license(license_id: uuid.UUID, uc: ResumeUC) -> LicenseRead:
    """Возобновить приостановленную лицензию (если срок не истёк)"""
    return LicenseRead.model_validate(await uc.execute(license_id))


@router.post("/{license_id}/revoke", response_model=LicenseRead, responses=ERROR_RESPONSES)
async def revoke_license(license_id: uuid.UUID, data: LicenseRevoke, uc: RevokeUC) -> LicenseRead:
    """Отозвать лицензию навсегда с обязательной причиной"""
    return LicenseRead.model_validate(await uc.execute(license_id, data.reason))


@router.post("/{license_id}/renew", response_model=LicenseRead, responses=ERROR_RESPONSES)
async def renew_license(license_id: uuid.UUID, uc: RenewUC) -> LicenseRead:
    """Продлить действующую лицензию на год; можно за 30 дней до конца срока (docs/license.md)"""
    return LicenseRead.model_validate(await uc.execute(license_id))
