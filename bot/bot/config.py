"""Configuration loaded from environment variables."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Telegram
    telegram_bot_token: str = ""

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

    # Delivery mode. Empty WEBHOOK_URL = long polling (process must stay up).
    # Set WEBHOOK_URL (e.g. https://<app>.up.railway.app) to receive updates
    # over HTTPS instead, which lets Railway's App Sleeping suspend the
    # container when there is no traffic.
    webhook_url: str = ""
    port: int = 8080  # Railway injects PORT

    # Comeback nudges. Off by default: it polls Neon every 6h (waking the
    # compute each time) and players.last_active_at is never written, so it
    # has never matched anyone. It also cannot run while the app sleeps.
    enable_comeback_job: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
