import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.enums import DronePurpose
from src.domain.rules import NAME_MAX_LENGTH
from src.infrastructure.db.base import Base, utcnow


class PartOrm(Base):
    """Строка таблицы `parts`"""

    __tablename__ = "parts"
    __table_args__ = (
        CheckConstraint("price > 0", name="price_positive"),
        Index("ix_parts_drone_id", "drone_id"),
        Index("ix_parts_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH))
    purpose: Mapped[DronePurpose]
    price: Mapped[int]
    drone_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("drones.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(default=utcnow, server_default=func.now())
