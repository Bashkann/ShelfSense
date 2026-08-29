"""Veri erişim katmanı (repository) — SQL sorguları BURADA toplanır.

Saf Python iş mantığı modülü. Backend router'ları SQL yazmaz; bu modülün
fonksiyonlarını çağırır. Çıktılar contracts modelleriyle uyumlu.
"""
from shelfsense.contracts.api import ProductLocationResponse
from shelfsense.contracts.store import StoreMap


def get_store_map(store_id: str) -> StoreMap:
    """store_id'ye ait tam StoreMap'i veritabanından kurar.

    Girdi: store_id. Çıktı: StoreMap.
    """
    raise NotImplementedError


def get_product_location(product_id: int) -> ProductLocationResponse:
    """Ürünün raf bloğu ve erişim düğümünü döndürür.

    Girdi: catalog product_id. Çıktı: ProductLocationResponse.
    """
    raise NotImplementedError
