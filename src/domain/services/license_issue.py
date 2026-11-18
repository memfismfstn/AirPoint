from src.domain.entities.license import License
from src.domain.enums import FlightRank
from src.domain.errors import (
    ActiveLicenseExists,
    CustomerUnderage,
)
from src.domain.rules import ADULT_AGE


def ensure_can_issue(customer_adult: bool, live_licenses: list[License], rank: FlightRank) -> None:
    """Правила выдачи лицензии, не требующие обращения к хранилищу"""
    if not customer_adult:
        raise CustomerUnderage(f"Лицензию можно выдать только с {ADULT_AGE} лет")
    for old in live_licenses:
        if old.rank.level >= rank.level:
            raise ActiveLicenseExists(
                f"У покупателя уже есть действующая лицензия ранга {old.rank.value}, "
                f"не ниже запрошенного {rank.value}",
            )
