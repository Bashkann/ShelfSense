"""Cevap metni üretimi — rapor F4'ün ilk yarısı.

Saf Python iş mantığı modülü (backend değil). Girdi ParsedList, çıktı
kullanıcıya SESLİ okunacak Türkçe metin. Seslendirmenin kendisi mobilde
(Android TTS); bu modül yalnızca NE söyleneceğine karar verir.
"""
from shelfsense.assistant.schemas import ParsedItem, ParsedList


def build_reply(parsed: ParsedList) -> str:
    """Ayrıştırma sonucunu kullanıcıya okunacak tek metne çevirir.

    Girdi: ParsedList. Çıktı: özet + varsa uyarı/onay sorularını içeren metin.
    """
    raise NotImplementedError


def summarize_items(items: list[ParsedItem]) -> str:
    """Çözülen kalemleri okunabilir diziye çevirir.

    Girdi: ParsedItem listesi. Çıktı: "bir kilo un, iki paket makarna" gibi
    virgülle ayrılmış özet.
    """
    raise NotImplementedError


def unmet_constraint_question(item: ParsedItem) -> str:
    """Karşılanamayan kısıt için uyarı + onay sorusu üretir.

    Girdi: unmet_constraints dolu ParsedItem. Çıktı: "Şekersiz kola
    bulamadım, normal kola ekleyeyim mi?" gibi soru.
    """
    raise NotImplementedError


def unresolved_warning(unresolved: list[str]) -> str:
    """Hiç çözülemeyen ham ifadeler için uyarı metni üretir.

    Girdi: çözülemeyen ifade listesi. Çıktı: "Zeytinyağını bulamadım." gibi
    metin; liste boşsa boş string.
    """
    raise NotImplementedError
