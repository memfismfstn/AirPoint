from src.domain.errors.base import DomainError, NotFoundError
from src.domain.errors.customer import CustomerNotFound, CustomerUnderage, PhoneAlreadyExists
from src.domain.errors.drone import (
    DroneNotAvailable,
    DroneNotFound,
    DroneSold,
    InvalidDroneStatus,
    SkuAlreadyExists,
)
from src.domain.errors.license import (
    ActiveLicenseExists,
    DailyLimitReached,
    InvalidLicenseTransition,
    LicenseExpired,
    LicenseNotFound,
    LicenseRankTooLow,
    LicenseSuspended,
    NoLicense,
    RenewalTooEarly,
)
from src.domain.errors.part import PartAlreadyAttached, PartNotFound, PartPurposeMismatch

__all__ = [
    "DomainError",
    "NotFoundError",
    "CustomerNotFound",
    "PhoneAlreadyExists",
    "CustomerUnderage",
    "DroneNotFound",
    "SkuAlreadyExists",
    "DroneNotAvailable",
    "DroneSold",
    "InvalidDroneStatus",
    "PartNotFound",
    "PartPurposeMismatch",
    "PartAlreadyAttached",
    "LicenseNotFound",
    "NoLicense",
    "LicenseSuspended",
    "LicenseExpired",
    "LicenseRankTooLow",
    "DailyLimitReached",
    "ActiveLicenseExists",
    "InvalidLicenseTransition",
    "RenewalTooEarly",
]
