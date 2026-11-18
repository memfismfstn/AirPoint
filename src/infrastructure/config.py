from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфигурация приложения"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./aerotochka.db"
    sql_echo: bool = False
    app_title: str = "АэроТочка"
    app_version: str = "0.2.0"
    docs_url: str | None = "/"


settings = Settings()
