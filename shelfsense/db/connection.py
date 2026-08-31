"""SQLAlchemy bağlantı ve oturum yönetimi."""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from shelfsense.config import get_settings


@lru_cache
def get_engine() -> Engine:
    """Süreç başına tek Engine oluşturur.

    Engine import sırasında değil, ilk ihtiyaç anında oluşturulur.
    """

    return create_engine(
        get_settings().database_url,
        pool_pre_ping=True,
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Veritabanı oturumlarını üreten factory nesnesini döndürür."""

    return sessionmaker(
        bind=get_engine(),
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
    )


def get_session() -> Iterator[Session]:
    """İstek için oturum oluşturur ve işlem sonunda kapatır.

    Commit işlemi çağıran kodun sorumluluğundadır.
    """

    with get_session_factory()() as session:
        yield session
