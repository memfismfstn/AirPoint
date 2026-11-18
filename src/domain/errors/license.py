from src.domain.errors.base import DomainError, NotFoundError


class LicenseNotFound(NotFoundError):
    """Лицензия не найдена"""

    code = "LICENSE_NOT_FOUND"
    default_message = "Лицензия не найдена"


class NoLicense(DomainError):
    """У покупателя нет лицензии"""

    code = "NO_LICENSE"
    default_message = "У покупателя нет действующей лицензии"


class LicenseSuspended(DomainError):
    """Лицензия приостановлена"""

    code = "LICENSE_SUSPENDED"
    default_message = "Лицензия покупателя приостановлена"


class LicenseExpired(DomainError):
    """Лицензия истекла"""

    code = "LICENSE_EXPIRED"
    default_message = "Срок действия лицензии покупателя истёк"


class LicenseRankTooLow(DomainError):
    """Ранг лицензии ниже ранга дрона"""

    code = "LICENSE_RANK_TOO_LOW"


class DailyLimitReached(DomainError):
    """Дневной лимит выдачи исчерпан"""

    code = "DAILY_LIMIT_REACHED"


class ActiveLicenseExists(DomainError):
    """Живая лицензия того же или высшего ранга уже есть"""

    code = "ACTIVE_LICENSE_EXISTS"


class InvalidLicenseTransition(DomainError):
    """Недопустимый переход статуса лицензии"""

    code = "INVALID_LICENSE_TRANSITION"


class RenewalTooEarly(DomainError):
    """Продлевать рано"""

    code = "RENEWAL_TOO_EARLY"
