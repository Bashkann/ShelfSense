"""Türkçe metin normalleştirme: küçültme + ek kırpma.

Saf Python iş mantığı modülü (backend değil). Girdi ham token, çıktı
normalize kök form; matcher.py bunu katalog eşlemesinde kullanır.
"""


def normalize(text: str) -> str:
    """Türkçe küçültme (İ/I kuralı) uygulanmış metni döndürür.

    Girdi: ham kullanıcı metni. Çıktı: küçük harfli, sadeleştirilmiş metin.
    """
    raise NotImplementedError


def strip_suffix(token: str) -> str:
    """Yaygın Türkçe çekim eklerini kırpıp kök forma yaklaşır.

    Girdi: tek token (örn. "sütü"). Çıktı: kök form (örn. "süt").
    """
    raise NotImplementedError
