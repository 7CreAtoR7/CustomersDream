from __future__ import annotations

from typing import Annotated, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения, читаются из .env (и переменных окружения)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = Field(..., alias="BOT_TOKEN")
    # NoDecode отключает JSON-парсинг — мы сами разрулим "1,2,3" в валидаторе
    admin_ids: Annotated[List[int], NoDecode] = Field(
        default_factory=list, alias="ADMIN_IDS"
    )
    manager_username: str = Field(default="", alias="MANAGER_USERNAME")

    payments_provider_token: str = Field(default="", alias="PAYMENTS_PROVIDER_TOKEN")
    crypto_usdt_trc20: str = Field(default="", alias="CRYPTO_USDT_TRC20")
    default_currency: str = Field(default="USD", alias="DEFAULT_CURRENCY")

    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/bot.db",
        alias="DATABASE_URL",
    )

    # URL Mini App (FastAPI). Для dev: http://localhost:8080, для прода: https://yourdomain.com
    webapp_url: str = Field(default="http://localhost:8080", alias="WEBAPP_URL")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, value):
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [int(v) for v in value]
        if isinstance(value, str):
            return [int(x.strip()) for x in value.split(",") if x.strip()]
        return value

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids


settings = Settings()  # type: ignore[call-arg]
