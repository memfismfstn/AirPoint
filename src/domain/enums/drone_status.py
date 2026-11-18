from enum import StrEnum


class DroneStatus(StrEnum):
    """Статус дрона"""

    IN_STOCK = "in_stock"
    SOLD = "sold"
    WITHDRAWN = "withdrawn"
