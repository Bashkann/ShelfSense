"""PostgreSQL → mobil çevrimdışı SQLite kopyası.

Saf Python iş mantığı modülü. Mağaza + katalog verisini tek dosyalık SQLite'a
döker; `make mobile-assets` bu çıktıyı mobile/ assets'e koyar.
"""


def export_sqlite(out_path: str) -> str:
    """PostgreSQL verisini mobil için SQLite dosyasına aktarır.

    Girdi: çıktı .db yolu. Çıktı: yazılan dosya yolu.
    """
    raise NotImplementedError
