"""Ortam yapılandırması (.env okuma) — pydantic-settings.

İş mantığı yok: yalnızca ayar şeması. Değerler .env'den gelir (.env.example).
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Uygulama ayarları. Alanlar .env değişkenleriyle eşleşir."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = ""
    llm_api_key: str = ""
    llm_base_url: str = ""
    pangu_project_id: str = ""
    pangu_deployment_id: str = ""
    model_path: str = ""


@lru_cache
def get_settings() -> Settings:
    """Tekil (önbellekli) Settings örneğini döndürür.

    Girdi: yok. Çıktı: .env'den okunmuş Settings.
    """
    # TODO: sözleşme dondurulunca zorunlu alan doğrulaması eklenecek
    raise NotImplementedError
