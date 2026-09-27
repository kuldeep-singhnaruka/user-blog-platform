"""Settings from the environment, with local defaults so the app runs without a .env file."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent


class Settings(BaseSettings):
    app_name: str = "Fieldnotes"
    database_url: str = "sqlite:///./data/blog.db"
    jwt_secret: str = "dev-only-change-with-JWT_SECRET-env"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 720
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    seed_demo_data: bool = True

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
            path = (BACKEND_ROOT / self.database_url[len(prefix) :]).resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            return "sqlite:///" + str(path)
        return self.database_url


settings = Settings()
