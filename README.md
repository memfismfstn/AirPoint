# АэроТочка

Бэкенд интернет-магазина дронов. Python 3.14.3, FastAPI, async SQLAlchemy 2 (`Mapped`), Alembic, SQLite.

Структура (Clean Architecture): `src/domain` → `src/application` → `src/infrastructure` и `src/presentation`, сборка в `src/main.py`.

## Запуск

```bash
uv sync
cp .env.example .env
uv run alembic upgrade head
uv run uvicorn src.main:app --reload --host 127.0.0.1 --port 8001
```

## Проверки

```bash
uv run pytest
uv run ruff check .
uv run ruff check --fix
uv run ruff format --check .
uv run alembic check
```

## Документация проекта

- `docs/architecture.md` — слои Clean Architecture, правило зависимостей, SOLID, как добавить фичу
- `docs/license.md` — проектные решения по лицензиям, контракт продления (`POST /licenses/{id}/renew`), защита от гонки
- `docs/*.mmd` и `docs/*.svg` — UML: классы предметной области, наследование, слои и зависимости, состояния лицензии, последовательности (выдача, покупка, продление)

## Соглашения кода

- Python 3.14.3, модели на `Mapped` / `mapped_column`
- Докстринги в Google style, без точек в конце строк (проверяет `tests/test_docstrings.py`)
- Таблицы создаёт только Alembic, время хранится в UTC, «день» для лимита считается по Москве
