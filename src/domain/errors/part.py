from src.domain.errors.base import DomainError, NotFoundError


class PartNotFound(NotFoundError):
    """Запчасть не найдена"""

    code = "PART_NOT_FOUND"
    default_message = "Запчасть не найдена"


class PartPurposeMismatch(DomainError):
    """Назначение запчасти не совпадает с дроном"""

    code = "PART_PURPOSE_MISMATCH"


class PartAlreadyAttached(DomainError):
    """Запчасть уже привязана"""

    code = "PART_ALREADY_ATTACHED"
    default_message = "Запчасть уже привязана к другому дрону, сначала отвяжите её"
