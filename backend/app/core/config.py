from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BACKEND_DIR.parent


def _env_files() -> tuple[str, ...]:
    paths: list[Path] = []
    for candidate in (ROOT_DIR / ".env", BACKEND_DIR / ".env"):
        if candidate.exists():
            paths.append(candidate)
    if not paths:
        paths.append(BACKEND_DIR / ".env")
    return tuple(str(path) for path in paths)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # MySQL — all credentials live in .env (see root .env.example)
    mysql_root_password: str = ""
    mysql_host: str = "mysql" #"127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = "password"
    mysql_database: str = "daniel_mulondo"
    database_url: str = ""

    storage_backend: str = "json"

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    session_secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    session_max_age: int = 60 * 60 * 24 * 14  # 14 days

    # Admin URL prefix (nginx: location /admin { proxy_pass http://backend:PORT; })
    admin_path_prefix: str = "/admin"
    investor_path_prefix: str = "/portal"

    admin_username: str = ""
    admin_password: str = ""
    admin_email: str = "admin@example.com"

    # Brevo transactional email (https://www.brevo.com)
    brevo_api_key: str = ""
    brevo_sender_email: str = ""
    brevo_sender_name: str = "Mulondo Daniel"
    admin_notification_email: str = ""

    # Alpaca Market Data API (keys stay server-side — never expose to frontend)
    alpaca_api_key: str = ""
    alpaca_api_secret: str = ""
    alpaca_data_base_url: str = "https://data.alpaca.markets"

    @model_validator(mode="after")
    def resolve_database_url(self) -> "Settings":
        if self.database_url:
            return self
        user = quote_plus(self.mysql_user)
        password = quote_plus(self.mysql_password)
        self.database_url = (
            f"mysql+pymysql://{user}:{password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )
        return self

    @model_validator(mode="after")
    def resolve_notification_email(self) -> "Settings":
        if not self.admin_notification_email and self.admin_email:
            self.admin_notification_email = self.admin_email
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
