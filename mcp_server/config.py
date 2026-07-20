from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    database_url: str = Field(
        default="postgresql://healthcare_readonly:readonly_password@localhost:5433/healthcare",
        alias="DATABASE_URL",
    )
    query_timeout_ms: int = Field(default=30000, alias="MCP_QUERY_TIMEOUT_MS")
    max_rows: int = Field(default=200, alias="MCP_MAX_ROWS")

    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
