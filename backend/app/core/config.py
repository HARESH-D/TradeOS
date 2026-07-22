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
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    gemini_api_url: str = "https://generativelanguage.googleapis.com/v1/interactions"
    agent_request_timeout_seconds: float = 90
    ollama_enabled: bool = False
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_context_length: int = 4_096
    ollama_max_output_tokens: int = 700
    ollama_health_timeout_seconds: float = 2
    ollama_request_timeout_seconds: float = 180

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
