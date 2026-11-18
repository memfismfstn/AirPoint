from datetime import date, datetime

from src.domain.rules import MSK


def msk_date(moment: datetime) -> date:
    """Переводит момент времени в календарную дату по Москве"""
    return moment.astimezone(MSK).date()


def add_one_year(day: date) -> date:
    """Прибавляет к дате один год, 29 февраля превращается в 28 февраля"""
    try:
        return day.replace(year=day.year + 1)
    except ValueError:
        return day.replace(year=day.year + 1, day=28)


def age_on(birth_date: date, day: date) -> int:
    """Считает полных лет человека на указанную дату"""
    years = day.year - birth_date.year
    if (day.month, day.day) < (birth_date.month, birth_date.day):
        years -= 1
    return years
