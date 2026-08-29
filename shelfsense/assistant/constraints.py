"""Kısıt uygulama: catalog.json constraints tablosuna göre filtre/sıralama.

Saf Python iş mantığı modülü. Girdi ParsedItem.constraints + varyant listesi,
çıktı seçilen/sıralı varyant(lar). Örn. "en ucuz" → price asc.
"""
from shelfsense.assistant.schemas import ParsedItem


def apply_constraints(item: ParsedItem, variants: list[dict]) -> list[dict]:
    """Kalemin kısıtlarını varyantlara uygular (filtre + sıralama).

    Girdi: ParsedItem + ürün varyantları. Çıktı: sıralı/filtreli varyantlar.
    """
    raise NotImplementedError
