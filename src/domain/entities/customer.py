import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Self

from src.domain.dates import age_on
from src.domain.rules import ADULT_AGE


@dataclass(slots=True, kw_only=True)
class Customer:
    """Покупатель, регистрации нет, находят по уникальному телефону

    Ранг в сущности не хранится: это ранг его действующей лицензии,
    и считается он при каждом ответе

    Attributes:
        id: Идентификатор, UUID4
        full_name: ФИО
        phone: Телефон в формате `+7XXXXXXXXXX`
        email: Электронная почта или None
        birth_date: Дата рождения
        created_at: Момент создания
    """

    id: uuid.UUID
    full_name: str
    phone: str
    email: str | None
    birth_date: date
    created_at: datetime

    @classmethod
    def register(
        cls, *, full_name: str, phone: str, email: str | None, birth_date: date, now: datetime
    ) -> Self:
        """Создаёт нового покупателя

        Args:
            full_name: ФИО
            phone: Телефон
            email: Электронная почта или None
            birth_date: Дата рождения
            now: Текущий момент

        Returns:
            Новый покупатель с UUID4
        """
        return cls(
            id=uuid.uuid4(),
            full_name=full_name,
            phone=phone,
            email=email,
            birth_date=birth_date,
            created_at=now,
        )

    def is_adult_on(self, day: date) -> bool:
        """Проверяет, исполнилось ли покупателю 18 лет к указанной дате

        Args:
            day: Дата проверки

        Returns:
            True, если покупатель совершеннолетний
        """
        return age_on(self.birth_date, day) >= ADULT_AGE
