from datetime import date

from sqlalchemy import CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.rules import DAILY_LICENSE_LIMIT
from src.infrastructure.db.base import Base


class LicenseDailyCounterOrm(Base):
    """Сколько лицензий выдано за конкретный московский день"""

    __tablename__ = "license_daily_counters"
    __table_args__ = (
        CheckConstraint(
            f"issued >= 0 AND issued <= {DAILY_LICENSE_LIMIT}", name="issued_within_limit"
        ),
    )

    day: Mapped[date] = mapped_column(primary_key=True)
    issued: Mapped[int] = mapped_column(default=0, server_default="0")
