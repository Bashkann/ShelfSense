"""Asistan İÇ modelleri (LLM ↔ asistan modülleri arası).

Bunlar HTTP sınırının modeli DEĞİL; dış (istek/yanıt) modelleri
contracts/api.py'de. İç ve dış model çakışırsa İÇ model kazanır ve
contracts/api.py bu tipleri import eder — yeniden tanımlamaz.
"""
from pydantic import BaseModel


class ParsedItem(BaseModel):
    """Ayrıştırıcının çözdüğü tek alışveriş kalemi.

    Girdi: kullanıcının ham ifadesi (raw). Çıktı: catalog.json'a bağlanmış
    ürün + miktar + kısıtlar + seçilen varyant.
    """
    raw: str
    product_id: int | None = None  # catalog.json id; çözülemezse None
    name: str | None = None
    quantity: float | None = None
    unit: str | None = None
    # catalog.json "constraints" anahtarları, örn. "en ucuz", "laktozsuz"
    constraints: list[str] = []
    # Katalogda KARŞILANAMAYAN kısıtlar (örn. "sekersiz" — böyle varyant yok).
    # Boş değilse: kullanıcı sesli UYARILIR ve en yakın ürün onayına sunulur.
    # Sessizce kısıtı düşürmek erişilebilirlik açısından kabul edilemez.
    unmet_constraints: list[str] = []
    variant_id: int | None = None  # constraints.py'nin seçtiği varyant
    confidence: float | None = None  # KARAR GEREKLİ: eşik altı → unresolved mı?


class ParsedList(BaseModel):
    """Bir sesli listenin tamamının ayrıştırma sonucu.

    Girdi: serbest metin. Çıktı: çözülen kalemler + çözülemeyen ham ifadeler.
    """
    items: list[ParsedItem] = []
    unresolved: list[str] = []
