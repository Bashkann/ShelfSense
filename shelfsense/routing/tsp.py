"""Ziyaret sırası optimizasyonu (gezgin satıcı yaklaşık çözümü).

Saf Python iş mantığı modülü. Girdi ziyaret edilecek raf erişim düğümleri,
çıktı sıralı durak listesi (Route.visit_order kaynağı). Küçük N için yeterli.
"""
import networkx as nx


def order_visits(graph: nx.Graph, start: str, targets: list[str]) -> list[str]:
    """Durakları en kısa toplam yolu verecek sırayla dizer.

    Girdi: graf + başlangıç + hedef düğümler. Çıktı: sıralı durak listesi.
    """
    raise NotImplementedError
