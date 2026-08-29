"""Rotadan sapma tespiti (mobil konum vs. beklenen yol).

Saf Python iş mantığı modülü. Girdi mevcut konum + aktif Route, çıktı sapma
var mı / yeniden hesap gerekli mi. simulator.py bunu uçtan uca test eder.
"""
from shelfsense.contracts.api import Route


def check_deviation(current_node_id: str, route: Route) -> bool:
    """Kullanıcının rotadan sapıp sapmadığını döndürür.

    Girdi: mevcut düğüm id + aktif Route. Çıktı: sapma varsa True.
    """
    raise NotImplementedError
