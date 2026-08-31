"""Uygulama ortam ayarları."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ortam değişkenlerinden yüklenen uygulama ayarları."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    model_path: str = "./models/shelf.onnx"


@lru_cache
def get_settings() -> Settings:
    """Ayarları bir kez yükleyip aynı nesneyi tekrar kullanır."""

    return Settings()