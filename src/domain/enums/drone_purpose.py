from enum import StrEnum


class DronePurpose(StrEnum):
    """Назначение дрона или запчасти"""

    TOY = "toy"
    CAMERA = "camera"
    FPV = "fpv"
    AGRO = "agro"
    CARGO = "cargo"
    INSPECTION = "inspection"
