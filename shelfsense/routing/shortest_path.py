"""En kısa yol (tek çift düğüm arası).

Saf Python iş mantığı modülü. networkx grafı üzerinde Dijkstra; çıktı düğüm
id listesi + toplam mesafe. tsp.py ziyaret sırasını bununla besler.
"""
import networkx as nx


def shortest_path(graph: nx.Graph, source: str, target: str) -> tuple[list[str], float]:
    """İki düğüm arası en kısa yolu ve mesafeyi döndürür.

    Girdi: graf + kaynak/hedef düğüm id. Çıktı: (yol düğümleri, mesafe).
    """
    raise NotImplementedError
