import uuid
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import Enum, MetaData, Uuid
from sqlalchemy.orm import DeclarativeBase

from src.domain.enums import DronePurpose, DroneStatus, FlightRank, LicenseStatus
from src.infrastructure.db.types import UTCDateTime

"""Длина VARCHAR под значения enum, совпадает с миграциями"""
ENUM_LENGTH = 20

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def utcnow() -> datetime:
    """Текущий момент в UTC, значение по умолчанию для колонок времени"""
    return datetime.now(UTC)


def _enum_type(enum_cls: type[StrEnum], name: str) -> Enum:
    """Создаёт тип Enum: VARCHAR со значениями enum и CHECK-ограничением"""
    return Enum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=ENUM_LENGTH,
        values_callable=lambda members: [m.value for m in members],
    )


class Base(DeclarativeBase):
    """Базовый класс всех ORM-моделей"""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    type_annotation_map = {
        uuid.UUID: Uuid(as_uuid=True),
        datetime: UTCDateTime(),
        FlightRank: _enum_type(FlightRank, "flight_rank"),
        DronePurpose: _enum_type(DronePurpose, "drone_purpose"),
        DroneStatus: _enum_type(DroneStatus, "drone_status"),
        LicenseStatus: _enum_type(LicenseStatus, "license_status"),
    }
