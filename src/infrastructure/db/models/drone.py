import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.enums import DronePurpose, DroneStatus, FlightRank
from src.domain.rules import MANUFACTURER_MAX_LENGTH, NAME_MAX_LENGTH, SKU_MAX_LENGTH
from src.infrastructure.db.base import Base, utcnow

"""У проданного дрона четыре поля «следа продажи» заполнены, у остальных пусты"""
_SOLD_CONSISTENT = (
    "(status = 'sold' AND customer_id IS NOT NULL AND sold_at IS NOT NULL"
    " AND sold_price IS NOT NULL AND sold_license_id IS NOT NULL)"
    " OR (status != 'sold' AND customer_id IS NULL AND sold_at IS NULL"
    " AND sold_price IS NULL AND sold_license_id IS NULL)"
)


class DroneOrm(Base):
    """Строка таблицы `drones`"""

    __tablename__ = "drones"
    __table_args__ = (
        CheckConstraint("weight_g > 0", name="weight_positive"),
        CheckConstraint("max_flight_time_min > 0", name="flight_time_positive"),
        CheckConstraint("max_range_m > 0", name="range_positive"),
        CheckConstraint("price > 0", name="price_positive"),
        CheckConstraint(_SOLD_CONSISTENT, name="sold_fields_consistent"),
        Index("ix_drones_status_purpose_rank", "status", "purpose", "rank"),
        Index("ix_drones_customer_id", "customer_id"),
        Index("ix_drones_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    sku: Mapped[str] = mapped_column(String(SKU_MAX_LENGTH), unique=True)
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH))
    manufacturer: Mapped[str] = mapped_column(String(MANUFACTURER_MAX_LENGTH))
    purpose: Mapped[DronePurpose]
    rank: Mapped[FlightRank]
    weight_g: Mapped[int]
    max_flight_time_min: Mapped[int]
    max_range_m: Mapped[int]
    has_camera: Mapped[bool] = mapped_column(default=False, server_default="0")
    price: Mapped[int]
    status: Mapped[DroneStatus] = mapped_column(
        default=DroneStatus.IN_STOCK, server_default=DroneStatus.IN_STOCK.value
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT")
    )
    sold_at: Mapped[datetime | None]
    sold_price: Mapped[int | None]
    sold_license_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("licenses.id", ondelete="RESTRICT")
    )
    created_at: Mapped[datetime] = mapped_column(default=utcnow, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=utcnow, onupdate=utcnow, server_default=func.now()
    )
