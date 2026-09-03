"""Ortak pytest fixture'ları: repo yolları ve JSON yükleyiciler."""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"


@pytest.fixture
def product_mapping() -> dict:
    """Yetkili data/product_mapping.json içeriğini döndürür."""
    return json.loads((DATA_DIR / "product_mapping.json").read_text("utf-8"))


@pytest.fixture
def store_min_path() -> Path:
    """data/mock/store_min.json dosya yolunu döndürür."""
    return DATA_DIR / "mock" / "store_min.json"
