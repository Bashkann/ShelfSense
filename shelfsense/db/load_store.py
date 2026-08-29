"""StoreMap JSON → veritabanı yükleyici.

Saf Python iş mantığı modülü. contracts/store.py ile doğrulanmış bir StoreMap
JSON'unu nodes/edges/shelf_blocks/placements tablolarına yazar.
"""
from shelfsense.contracts.store import StoreMap


def load_store(store: StoreMap) -> str:
    """Doğrulanmış StoreMap'i veritabanına yazar; store_id döndürür.

    Girdi: StoreMap. Çıktı: yazılan store_id.
    """
    raise NotImplementedError
