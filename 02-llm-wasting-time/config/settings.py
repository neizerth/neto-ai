from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = "test-key"
    model_name: str = "gpt-4o-mini"
    database_url: str = "sqlite:///./app.db"
    openai_timeout_seconds: int = 60
    max_user_query_length: int = 1000
    min_user_query_length: int = 5
    max_clarification_rounds: int = 2
    max_questions_per_round: int = 5
    max_alternatives: int = 5
    session_ttl_hours: int = 24
    history_default_limit: int = 20


@lru_cache
def get_settings() -> Settings:
    return Settings()
