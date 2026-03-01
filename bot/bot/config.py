"""Configuration loaded from environment variables."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Telegram
    telegram_bot_token: str = ""
    admin_telegram_ids: list[int] = []

    # Database (Neon)
    database_url: str = ""

    # Google Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # Game config
    free_turns_per_day: int = 10
    premium_price_stars: int = 150
    premium_duration_days: int = 30

    # Admin
    admin_api_secret: str = ""

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
