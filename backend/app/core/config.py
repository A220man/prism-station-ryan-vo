from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    app_name: str = "prism-station"
    environment: str = "development"
    debug: bool = True

    database_url: str = "sqlite:///./prism_station.db"

    secret_key: str = Field(default="dev-secret-change-in-production-min-32-chars-long", min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    oidc_enabled: bool = False
    oidc_issuer_url: Optional[str] = None
    oidc_client_id: Optional[str] = None
    oidc_client_secret: Optional[str] = None
    oidc_redirect_uri: Optional[str] = None

    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_api_key: Optional[str] = None

    frontend_url: str = "http://localhost:5173"
    backend_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()