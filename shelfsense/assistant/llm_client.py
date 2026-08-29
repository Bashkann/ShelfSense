"""LLM istemci arayüzü — sesli listeyi yapılandırılmış ParsedList'e çevirir.

Saf Python iş mantığı modülü. httpx ile LLM_BASE_URL'e istek; prompt ve şema
bu modülde. Erişilemezse rule_parser devreye girer.
"""
from shelfsense.assistant.schemas import ParsedList


def parse_list(text: str) -> ParsedList:
    """Metni LLM ile ayrıştırıp ParsedList döndürür.

    Girdi: ham sesli liste metni. Çıktı: ParsedList.
    """
    raise NotImplementedError
