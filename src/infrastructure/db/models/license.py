import uuid
from datetime import date, datetime

from sqlalchemy import CHAR, CheckConstraint, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.enums import FlightRank, LicenseStatus
from src.domain.rules import LICENSE_KEY_LENGTH
from src.domain.services.license_key import generate_license_key
from src.infrastructure.db.base import Base


class LicenseOrm(Base):
    """Строка таблицы `licenses`"""

    __tablename__ = "licenses"
    __table_args__ = (
        CheckConstraint(
            "status != 'revoked' OR revoke_reason IS NOT NULL", name="revoked_has_reason"
        ),
        Index("ix_licenses_customer_id_issued_at", "customer_id", "issued_at"),
        Index("ix_licenses_issued_at", "issued_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(
        CHAR(LICENSE_KEY_LENGTH), unique=True, default=generate_license_key
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"))
    rank: Mapped[FlightRank]
    status: Mapped[LicenseStatus] = mapped_column(
        default=LicenseStatus.ACTIVE, server_default=LicenseStatus.ACTIVE.value
    )
    issued_at: Mapped[datetime]
    valid_until: Mapped[date]
    revoke_reason: Mapped[str | None] = mapped_column(Text)
