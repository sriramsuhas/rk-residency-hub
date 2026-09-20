"""
Centralized application configuration.

All environment-dependent values are read once here via pydantic-settings,
so the rest of the codebase never touches os.environ directly.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://rk_user:rk_password@localhost:5432/rk_pms_db"

    # JWT
    jwt_secret_key: str = "dev_secret_change_me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # App
    app_env: str = "development"
    cors_origins: str = "http://localhost:5173"

    # Uploads
    max_upload_size_mb: int = 5
    upload_dir: str = "uploads"

    # Email (SMTP). If smtp_host is left blank, emails are logged to the
    # console instead of actually being sent — convenient for local
    # development without needing a real mail server, and used
    # automatically by the test suite. Set smtp_host to enable real
    # delivery (e.g. via Gmail SMTP, SendGrid, Mailtrap, etc).
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    email_from: str = "RK Residency Hub <no-reply@rkresidencyhub.example>"
    smtp_use_tls: bool = True

    # Used to build links inside emails (e.g. the password reset link)
    frontend_base_url: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — avoids re-parsing env on every import."""
    return Settings()


settings = get_settings()
