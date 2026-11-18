import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Self

from src.domain.entities.customer import Customer
from src.domain.entities.license import License
from src.domain.enums import FlightRank, LicenseStatus


@dataclass(slots=True, frozen=True)
class CustomerView:
    """Покупатель вместе с вычисляемым рангом"""

    id: uuid.UUID
    full_name: str
    phone: str
    email: str | None
    birth_date: date
    rank: FlightRank | None
    created_at: datetime

    @classmethod
    def of(cls, customer: Customer, rank: FlightRank | None) -> Self:
        """Собирает представление из сущности"""
        return cls(
            id=customer.id,
            full_name=customer.full_name,
            phone=customer.phone,
            email=customer.email,
            birth_date=customer.birth_date,
            rank=rank,
            created_at=customer.created_at,
        )


@dataclass(slots=True, frozen=True)
class LicenseView:
    """Лицензия с актуальным статусом на сегодня"""

    id: uuid.UUID
    key: str
    customer_id: uuid.UUID
    rank: FlightRank
    status: LicenseStatus
    issued_at: datetime
    valid_until: date
    revoke_reason: str | None

    @classmethod
    def of(cls, lic: License, today: date) -> Self:
        """Собирает представление из сущности"""
        return cls(
            id=lic.id,
            key=lic.key,
            customer_id=lic.customer_id,
            rank=lic.rank,
            status=lic.effective_status(today),
            issued_at=lic.issued_at,
            valid_until=lic.valid_until,
            revoke_reason=lic.revoke_reason,
        )
