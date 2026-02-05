from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "GUVI Agentic HoneyPot API"
    api_key: str = "local-dev-secret"
    openai_api_key: str | None = None
    callback_url: str = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
    request_timeout_seconds: float = 3.0
    max_stored_messages: int = 40
    finalize_turn_threshold: int = 18
    finalize_min_turn_threshold: int = 12
    finalize_min_intel_items: int = 2

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
