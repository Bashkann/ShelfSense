"""FastAPI bağımlılıkları (dependency injection).

İnce kabuk yardımcıları: DB bağlantısı, ayar ve repository sağlayıcıları.
İş mantığı yok; sadece router'lara kaynak enjekte eder.
"""


def get_repository():
    """İstek başına repository/veri erişim nesnesi sağlar.

    Girdi: yok. Çıktı: repository örneği (db/repository.py).
    """
    raise NotImplementedError
