"""FastAPI uygulama girişi — İNCE HTTP KABUĞU.

Bu katman algoritma/SQL İÇERMEZ; yalnızca routing/assistant/db modüllerini
HTTP'ye açar. Router'ları toplar ve uygulamayı kurar.
"""
from fastapi import FastAPI


def create_app() -> FastAPI:
    """Router'ları bağlayıp FastAPI uygulamasını kurar.

    Girdi: yok. Çıktı: yapılandırılmış FastAPI örneği.
    """
    raise NotImplementedError
