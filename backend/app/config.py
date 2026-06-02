from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
import httpx
from openai import OpenAI


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHROMA_COLLECTION: str = "telecom_incidents"

    DATA_PATH: str = "./data/telecom_incidents.csv"

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    TOP_K: int = 10
    RRF_K: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_openai_client() -> OpenAI:
    """
    Returns a configured OpenAI client.
    When OPENAI_BASE_URL is set (custom proxy/gateway), SSL verification is
    disabled via a custom httpx transport — required for gateways whose
    certificate chain is not trusted by Python's default CA bundle on Windows.
    """
    settings = get_settings()
    kwargs: dict = {"api_key": settings.OPENAI_API_KEY}
    if settings.OPENAI_BASE_URL:
        kwargs["base_url"] = settings.OPENAI_BASE_URL
        kwargs["http_client"] = httpx.Client(verify=False)
    return OpenAI(**kwargs)
