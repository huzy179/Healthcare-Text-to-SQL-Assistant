from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    database_url: str = Field(
        default="postgresql://healthcare_readonly:readonly_password@localhost:5433/healthcare",
        alias="DATABASE_URL",
    )
    vllm_base_url: str | None = Field(default=None, alias="VLLM_BASE_URL")
    vllm_model: str | None = Field(default=None, alias="VLLM_MODEL")
    vllm_api_key: str = Field(default="local", alias="VLLM_API_KEY")
    prompt_file: Path = ROOT_DIR / "inference" / "prompts" / "text_to_sql_prompt.txt"
    schema_file: Path = ROOT_DIR / "inference" / "prompts" / "schema_context.txt"

    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
