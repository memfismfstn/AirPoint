from dataclasses import fields
from typing import Any


def to_orm[O](orm_cls: type[O], entity: Any) -> O:
    """Строит ORM-объект из сущности"""
    return orm_cls(**{f.name: getattr(entity, f.name) for f in fields(entity)})


def to_entity[E](entity_cls: type[E], orm: Any) -> E:
    """Строит сущность из ORM-объекта"""
    return entity_cls(**{f.name: getattr(orm, f.name) for f in fields(entity_cls)})
