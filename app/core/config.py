from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "temple-api-gateway"
    environment: str = "dev"
    identity_service_url: str = "http://localhost:8001"
    registration_service_url: str = "http://localhost:8002"
    admin_service_url: str = "http://localhost:8003"
    upstream_timeout_seconds: float = 75.0
    upstream_retry_attempts: int = 3
    cors_allowed_origins: str = (
        "https://temple-app-lake.vercel.app,"
        "https://dist-phi-livid-17.vercel.app,"
        "https://dist-5whgbucq6-apoorv-jains-projects-48c4afa9.vercel.app,"
        "http://localhost:8081,"
        "http://localhost:19006"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
