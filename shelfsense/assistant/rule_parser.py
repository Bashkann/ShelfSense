"""Kural tabanlı ayrıştırıcı — LLM erişilemezse YEDEK.

Saf Python iş mantığı modülü. llm_client başarısız olursa devreye girer;
synonyms + constraints tablolarından deterministik ayrıştırma yapar.
"""
from shelfsense.assistant.schemas import ParsedList


def parse(text: str, catalog: dict) -> ParsedList:
    """Sesli liste metnini kural tabanlı ayrıştırır.

    Girdi: ham metin + catalog. Çıktı: ParsedList (items + unresolved).
    """
    raise NotImplementedError
