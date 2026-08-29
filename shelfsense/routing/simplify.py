"""Ham yolu insan-anlatısına indirgeme (gereksiz düğümleri sadeleştirme).

Saf Python iş mantığı modülü. Düz koridordaki ara düğümleri birleştirir;
çıktı yön değişim noktaları — instructions.py bunları cümleye çevirir.
"""
import networkx as nx


def simplify_path(graph: nx.Graph, path: list[str]) -> list[str]:
    """Yoldaki gereksiz ara düğümleri eleyip dönüş noktalarını bırakır.

    Girdi: graf + düğüm id yolu. Çıktı: sadeleştirilmiş düğüm id yolu.
    """
    raise NotImplementedError
