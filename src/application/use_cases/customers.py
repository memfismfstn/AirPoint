import uuid
from typing import Any

from src.application.commands import NewCustomer
from src.application.dto import CustomerView, LicenseFilter, LicenseView, Page, Pagination
from src.application.use_cases.base import UseCase, require_customer
from src.domain.dates import msk_date
from src.domain.entities.customer import Customer
from src.domain.errors import CustomerUnderage, PhoneAlreadyExists


class CreateCustomer(UseCase):
    """Добавляет покупателя"""

    async def execute(self, cmd: NewCustomer) -> CustomerView:
        """Создаёт покупателя с уникальным телефоном

        Args:
            cmd: Данные покупателя

        Returns:
            Созданный покупатель без ранга

        Raises:
            DomainError: Телефон уже занят
        """
        now, _ = self.moment()
        async with self.uow as uow:
            await uow.begin_write()
            if await uow.customers.get_by_phone(cmd.phone) is not None:
                raise PhoneAlreadyExists()
            customer = Customer.register(
                full_name=cmd.full_name,
                phone=cmd.phone,
                email=cmd.email,
                birth_date=cmd.birth_date,
                now=now,
            )
            await uow.customers.add(customer)
            await uow.commit()
        return CustomerView.of(customer, None)


class GetCustomer(UseCase):
    """Возвращает одного покупателя"""

    async def execute(self, customer_id: uuid.UUID) -> CustomerView:
        """Находит покупателя и считает его ранг

        Args:
            customer_id: Идентификатор покупателя

        Returns:
            Покупатель с рангом

        Raises:
            DomainError: Покупателя нет
        """
        _, today = self.moment()
        async with self.uow as uow:
            customer = await require_customer(uow, customer_id)
            ranks = await uow.licenses.active_ranks([customer.id], today)
        return CustomerView.of(customer, ranks.get(customer.id))


class ListCustomers(UseCase):
    """Возвращает страницу покупателей"""

    async def execute(self, phone: str | None, page: Pagination) -> Page[CustomerView]:
        """Ищет покупателей, при необходимости по точному телефону

        Args:
            phone: Телефон или None
            page: Параметры пагинации

        Returns:
            Страница покупателей с рангами
        """
        _, today = self.moment()
        async with self.uow as uow:
            result = await uow.customers.list(phone, page)
            ranks = await uow.licenses.active_ranks([c.id for c in result.items], today)
        return result.map(lambda c: CustomerView.of(c, ranks.get(c.id)))


class UpdateCustomer(UseCase):
    """Меняет покупателя"""

    async def execute(self, customer_id: uuid.UUID, changes: dict[str, Any]) -> CustomerView:
        """Применяет изменения, не давая «узаконить» лицензию несовершеннолетнему

        Args:
            customer_id: Идентификатор покупателя
            changes: Меняемые поля (только переданные в запросе)

        Returns:
            Обновлённый покупатель с рангом

        Raises:
            DomainError: Покупателя нет, телефон занят или лицензия оказалась бы
                выдана до 18 лет
        """
        _, today = self.moment()
        async with self.uow as uow:
            await uow.begin_write()
            customer = await require_customer(uow, customer_id, for_update=True)
            phone = changes.get("phone")
            if phone is not None and phone != customer.phone:
                other = await uow.customers.get_by_phone(phone)
                if other is not None and other.id != customer.id:
                    raise PhoneAlreadyExists()
            for field, value in changes.items():
                setattr(customer, field, value)
            if "birth_date" in changes:
                for issued_at in await uow.licenses.issue_moments(customer.id):
                    if not customer.is_adult_on(msk_date(issued_at)):
                        raise CustomerUnderage(
                            f"С такой датой рождения лицензия от {msk_date(issued_at)} "
                            f"оказалась бы выдана несовершеннолетнему",
                        )
            await uow.customers.save(customer)
            await uow.commit()
            ranks = await uow.licenses.active_ranks([customer.id], today)
        return CustomerView.of(customer, ranks.get(customer.id))


class ListCustomerLicenses(UseCase):
    """Возвращает лицензии покупателя"""

    async def execute(self, customer_id: uuid.UUID, page: Pagination) -> Page[LicenseView]:
        """Отдаёт все лицензии покупателя, включая отозванные и истёкшие

        Args:
            customer_id: Идентификатор покупателя
            page: Параметры пагинации

        Returns:
            Страница лицензий

        Raises:
            DomainError: Покупателя нет
        """
        _, today = self.moment()
        async with self.uow as uow:
            await require_customer(uow, customer_id)
            result = await uow.licenses.list(LicenseFilter(customer_id=customer_id), today, page)
        return result.map(lambda lic: LicenseView.of(lic, today))
