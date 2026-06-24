from app.core.settings import Settings
from app.core.settings import settings as _settings


def get_settings() -> Settings:
    return _settings
