from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TradeOS API"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./tradeos.db"
    jwt_secret: str = "tradeos-local-development-secret-change-me"
    jwt_expiry_minutes: int = 60 * 24 * 7
    encryption_key: str | None = None
    cors_origins: str = "http://localhost:5173"
    frontend_url: str = "http://localhost:5173"
    allowed_hosts: str = "*"
    seed_demo: bool = True
    broker_public_ip: str | None = None
    broker_local_ip: str | None = None
    broker_mac_address: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def allowed_host_list(self) -> list[str]:
        return [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
