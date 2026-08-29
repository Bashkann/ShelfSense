"""StoreMap JSON dışa aktarımı — .blend dosyasını PARSE ETMEZ.

ÖNEMLİ: Bu script bir .blend dosyasını AÇIP PARSE ETMEZ. Sahne build_scene.py
ile KODLA üretildiği için koordinatlar üretim sırasında zaten elde; StoreMap
JSON'u sahne üretilirken yayılır. Çıktı contracts/store.py ile doğrulanır.
"""
from shelfsense.contracts.store import StoreMap


def export_store(out_path: str) -> StoreMap:
    """Kodla üretilen sahneden StoreMap kurup JSON'a yazar.

    Girdi: çıktı JSON yolu. Çıktı: StoreMap (ve diske yazılır).
    """
    raise NotImplementedError
