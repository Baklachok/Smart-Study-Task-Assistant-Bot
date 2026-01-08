import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):  # type: ignore
    TELEGRAM_BOT_TOKEN: str
    API_URL: str = "http://backend:8000/api/v1"


settings = Settings(TELEGRAM_BOT_TOKEN=os.environ["TELEGRAM_BOT_TOKEN"])
