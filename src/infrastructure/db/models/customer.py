import uuid
from datetime import date, datetime

from sqlalchemy import CHAR, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.rules import EMAIL_MAX_LENGTH, FULL_NAME_MAX_LENGTH, PHONE_LENGTH
from src.infrastructure.db.base import Base, utcnow


class CustomerOrm(Base):
    """Строка таблицы `customers`"""

    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(FULL_NAME_MAX_LENGTH))
    phone: Mapped[str] = mapped_column(CHAR(PHONE_LENGTH), unique=True)
    email: Mapped[str | None] = mapped_column(String(EMAIL_MAX_LENGTH))
    birth_date: Mapped[date]
    created_at: Mapped[datetime] = mapped_column(default=utcnow, server_default=func.now())
