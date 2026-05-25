import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent

dotenv_path = BASE_DIR / ".env"
load_dotenv(dotenv_path)

app_env = os.getenv("APP_ENV", "dev").strip().lower()

env_specific = BASE_DIR / f".env.{app_env}"
if env_specific.exists():
    load_dotenv(env_specific, override=True)

class Settings(BaseSettings):
    
    APP_HOST: str = Field(default="127.0.0.1")

    APP_PORT: int = Field(default=8000, ge=1024, le=65535)

    DEBUG: bool = Field(default=False)
    
    LOG_LEVEL: str = Field(default="INFO")

    APP_ENV: str = Field(default="dev")

    model_config = SettingsConfigDict(extra="ignore")

try:
    settings = Settings()
except ValidationError as e:
    print("=" * 60, file=sys.stderr)
    print("ОШИБКА КОНФИГУРАЦИИ:", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    for error in e.errors():
        field = " -> ".join(str(x) for x in error['loc'])
        print(f"  {field}: {error['msg']}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Проверьте файл: .env.{app_env}", file=sys.stderr)
    sys.exit(1)