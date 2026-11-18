from dataclasses import dataclass
from datetime import date


@dataclass(slots=True, frozen=True)
class NewCustomer:
    """Данные нового покупателя"""

    full_name: str
    phone: str
    email: str | None
    birth_date: date
