from pydantic_settings import BaseSettings


class Settings(BaseSettings):  # type: ignore
    TELEGRAM_BOT_TOKEN: str
    API_URL: str = "http://backend:8000/api/v1"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    BOT_QUEUE: str = "telegram"


settings = Settings()
