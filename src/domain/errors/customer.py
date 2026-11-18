from src.domain.errors.base import DomainError, NotFoundError


class CustomerNotFound(NotFoundError):
    """Покупатель не найден"""

    code = "CUSTOMER_NOT_FOUND"
    default_message = "Покупатель не найден"


class PhoneAlreadyExists(DomainError):
    """Телефон уже занят"""

    code = "PHONE_ALREADY_EXISTS"
    default_message = "Покупатель с таким телефоном уже есть"


class CustomerUnderage(DomainError):
    """Покупателю нет 18 лет"""

    code = "CUSTOMER_UNDERAGE"
