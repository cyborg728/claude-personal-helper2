from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BOT_")

    telegram_token: str
    admin_username: str
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    webhook_domain: str = "tg-assistant.f-f.dev"
    webhook_path: str = "/webhook"
    mode: str = "polling"  # "polling" or "webhook"
    host: str = "0.0.0.0"
    port: int = 8443
    database_url: str = "sqlite+aiosqlite:///data/bot.db"
    default_locale: str = "en"
    available_locales: list[str] = ["en", "ru", "ko"]

    @property
    def webhook_url(self) -> str:
        return f"https://{self.webhook_domain}{self.webhook_path}"


settings = Settings()  # type: ignore[call-arg]
