"""Kenar maliyeti hesabı (metre + olası ceza terimleri).

Saf Python iş mantığı modülü. Girdi iki Node, çıktı maliyet (metre).
İleride kalabalık/engel cezası eklenebilir.
"""
from shelfsense.contracts.store import Node


def edge_cost(a: Node, b: Node) -> float:
    """İki düğüm arası yürüme maliyetini (metre) hesaplar.

    Girdi: iki Node. Çıktı: maliyet (float, metre).
    """
    raise NotImplementedError
