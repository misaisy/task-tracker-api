import logging
import sys

from pydantic import Field, ValidationError, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):

    APP_HOST: str = Field(default="0.0.0.0")

    APP_PORT: int = Field(default=8000, ge=1024, le=65535)

    DEBUG: bool = Field(default=False)

    LOG_LEVEL: str = Field(default="INFO")

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/taskdb"
    )

    TEST_DATABASE_URL: str = Field(
        default="postgresql+asyncpg://testuser:testpass@localhost:5433/testdb"
    )

    SECRET_KEY: str

    AUTH_ALGORITHM: str = Field(default="HS256")

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, ge=1)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("APP_HOST")
    @classmethod
    def validate_host(cls, value: str) -> str:
        """Проверяет, что хост не пустой и содержит только допустимые символы."""
        if not value.strip():
            raise ValueError("APP_HOST не может быть пустым")

        allowed = set("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.-")
        if not all(c in allowed for c in value):
            raise ValueError(
                f"APP_HOST содержит недопустимые символы: '{value}'. "
                f"Разрешены только буквы, цифры, точки и дефисы"
            )
        return value.strip()

    @field_validator("APP_PORT")
    @classmethod
    def validate_port(cls, value: int) -> int:
        """Дополнительная проверка порта."""
        if value == 5432:
            raise ValueError(
                f"Порт {value} обычно используется PostgreSQL. "
                f"Выберите другой порт для приложения"
            )
        return value

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Проверяет, что уровень логирования допустимый."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if value.upper() not in allowed:
            raise ValueError(
                f"LOG_LEVEL должен быть одним из: {', '.join(sorted(allowed))}. "
                f"Получено: '{value}'"
            )
        return value.upper()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def APP_URL(self) -> str:
        """URL приложения, собранный из хоста и порта."""
        return f"http://{self.APP_HOST}:{self.APP_PORT}"


try:
    settings = Settings()
except ValidationError as e:
    logger.critical("Ошибка конфигурации приложения")
    for error in e.errors():
        field = " -> ".join(str(x) for x in error['loc'])
        logger.critical("  %s: %s", field, error['msg'])
    logger.critical("Проверьте файл .env в корне проекта")
    sys.exit(1)
