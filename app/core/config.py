from functools import lru_cache

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class CorsSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    cors_origins: list[str] = ["http://127.0.0.1:5173", "http://localhost:5173"]

    @field_validator("cors_origins")
    @classmethod
    def explicit_origins(cls, origins: list[str]) -> list[str]:
        from urllib.parse import urlsplit

        for origin in origins:
            parsed = urlsplit(origin)
            if (
                "*" in origin or parsed.scheme not in {"http", "https"}
                or not parsed.netloc or parsed.path or parsed.query or parsed.fragment
                or parsed.username or parsed.password
            ):
                raise ValueError("CORS origins must be explicit HTTP(S) origins without paths")
        return origins


class Settings(CorsSettings):
    app_db_host: str = "app-db"
    app_db_port: int = 5432
    app_db_name: str = "automation_hub"
    app_db_user: str = "hub_app"
    app_db_password: SecretStr

    @property
    def database_url(self) -> URL:
        return URL.create(
            "postgresql+psycopg", username=self.app_db_user,
            password=self.app_db_password.get_secret_value(), host=self.app_db_host,
            port=self.app_db_port, database=self.app_db_name,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
