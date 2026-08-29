"""Katalog eşleme: normalize metni catalog.json ürününe bağlar.

Saf Python iş mantığı modülü (backend değil). rapidfuzz ile synonyms alanına
bulanık eşleme; çıktı catalog.json int product_id.
"""
from shelfsense.assistant.schemas import ParsedItem


def match_item(text: str, catalog: dict) -> ParsedItem:
    """Tek ifadeyi kataloga eşler; çözülemezse product_id=None döner.

    Girdi: normalize metin + catalog dict. Çıktı: ParsedItem.
    """
    raise NotImplementedError
