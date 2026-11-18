from src.domain.errors.base import DomainError, NotFoundError


class DroneNotFound(NotFoundError):
    """Дрон не найден"""

    code = "DRONE_NOT_FOUND"
    default_message = "Дрон не найден"


class SkuAlreadyExists(DomainError):
    """Артикул уже занят"""

    code = "SKU_ALREADY_EXISTS"


class DroneNotAvailable(DomainError):
    """Дрон недоступен для покупки"""

    code = "DRONE_NOT_AVAILABLE"
    default_message = "Дрон не в наличии"


class DroneSold(DomainError):
    """Дрон уже продан"""

    code = "DRONE_SOLD"
    default_message = "Проданный дрон изменить нельзя"


class InvalidDroneStatus(DomainError):
    """Недопустимый статус дрона"""

    code = "INVALID_DRONE_STATUS"
    default_message = "Статус sold ставится только покупкой, через PATCH его выставить нельзя"
