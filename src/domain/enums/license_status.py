from enum import StrEnum


class LicenseStatus(StrEnum):
    """Статус лицензии"""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"
