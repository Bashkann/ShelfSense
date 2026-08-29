"""PostgreSQL bağlantı yönetimi.

Saf Python iş mantığı modülü. DATABASE_URL'den (config.py) bağlantı açar;
psycopg2 tabanlı. Backend bu modül üzerinden veriye erişir.
"""


def get_connection():
    """DATABASE_URL kullanarak yeni bir PostgreSQL bağlantısı açar.

    Girdi: yok (config.py'den okur). Çıktı: psycopg2 bağlantı nesnesi.
    """
    raise NotImplementedError
