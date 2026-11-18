from typing import ClassVar

from pydantic import (
    BaseModel,
    ConfigDict,
    model_validator,
)


class StrictModel(BaseModel):
    """Тело запроса: лишние поля запрещены (422)"""

    model_config = ConfigDict(extra="forbid")


class PatchModel(StrictModel):
    """Тело PATCH: передаются только меняемые поля, `null` разрешён лишь где указано"""

    nullable_fields: ClassVar[frozenset[str]] = frozenset()

    @model_validator(mode="after")
    def _forbid_explicit_null(self) -> PatchModel:
        """Запрещает явный `null` у обязательных полей"""
        for name in self.model_fields_set - self.nullable_fields:
            if getattr(self, name) is None:
                raise ValueError(f"Поле {name} не может быть null")
        return self
