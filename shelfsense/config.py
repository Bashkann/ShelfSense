"""Ortam yapılandırması (.env okuma) — pydantic-settings.

İş mantığı yok: yalnızca ayar şeması. Değerler .env'den gelir.
"""

from decimal import Decimal
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Uygulama ayarları. Alanlar .env değişkenleriyle eşleşir."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    llm_api_key: str = ""
    llm_base_url: str = ""
    pangu_project_id: str = ""
    pangu_deployment_id: str = ""
    model_path: str = "./models/shelf.onnx"
    import_max_missing_shelves: int = 3
    import_max_missing_shelf_ratio: Decimal = Decimal("0.20")
    import_max_missing_edges: int = 2
    import_max_missing_edge_ratio: Decimal = Decimal("0.10")
    import_max_missing_placements: int = 5
    import_max_missing_placement_ratio: Decimal = Decimal("0.15")


@lru_cache
def get_settings() -> Settings:
    """Tekil ve önbellekli Settings örneğini döndürür."""

    return Settings()
