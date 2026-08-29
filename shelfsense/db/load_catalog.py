"""catalog.json → veritabanı yükleyici (tek doğru kaynaktan tohumlama).

Saf Python iş mantığı modülü. data/catalog.json okunup products/variants/
shelves tablolarına yazılır. catalog.json DEĞİŞTİRİLMEZ, sadece okunur.
"""


def load_catalog(path: str = "data/catalog.json") -> int:
    """catalog.json'u veritabanına yükler; yüklenen ürün sayısını döndürür.

    Girdi: catalog.json yolu. Çıktı: yüklenen ürün sayısı.
    """
    raise NotImplementedError
