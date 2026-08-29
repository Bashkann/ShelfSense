"""Rota takip simülatörü — gerçek cihaz olmadan yürüyüşü canlandırır.

Saf Python iş mantığı modülü. Girdi StoreMap + Route, çıktı adım adım konum
akışı; deviation/instructions'ı uçtan uca test etmeye yarar.
"""
from shelfsense.contracts.api import Route
from shelfsense.contracts.store import StoreMap


def simulate(store: StoreMap, route: Route) -> list[str]:
    """Route boyunca ziyaret edilen düğüm id'lerini sırayla üretir.

    Girdi: StoreMap + Route. Çıktı: adım adım düğüm id listesi.
    """
    raise NotImplementedError
