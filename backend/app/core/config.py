"""Runtime configuration loaded from the environment and an optional .env file."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent


class Settings(BaseSettings):
    app_name: str = "Fieldnotes"
    environment: str = "development"
    database_url: str = "sqlite:///./data/blog.db"
    jwt_secret: str = "dev-only-change-with-JWT_SECRET-env"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 720
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    upload_dir: str = "uploads"
    max_upload_bytes: int = 2_000_000
    wikipedia_api_base: str = "https://en.wikipedia.org/api/rest_v1"
    external_timeout_seconds: float = 3.0
    external_retries: int = 2
    external_api_base: str = ""
    external_api_key: str = ""
    webhook_secret: str = "dev-webhook-secret"
    rate_limit_per_minute: int = 120
    login_rate_limit_per_minute: int = 10
    list_cache_seconds: int = 10
    seed_demo_data: bool = True
    admin_email: str = "admin@fieldnotes.local"
    admin_password: str = "Admin123!"
    admin_name: str = "Fieldnotes Admin"

    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", BACKEND_ROOT / ".env"),
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def resolved_database_url(self) -> str:
        prefix = "sqlite:///./"
        if self.database_url.startswith(prefix):
            relative = self.database_url[len(prefix) :]
            path = (BACKEND_ROOT / relative).resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            return "sqlite:///" + str(path)
        return self.database_url

    def resolved_upload_dir(self) -> Path:
        path = Path(self.upload_dir)
        if not path.is_absolute():
            path = BACKEND_ROOT / path
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
