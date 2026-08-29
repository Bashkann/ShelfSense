"""Sadeleştirilmiş yolu sesli yönergelere çevirir.

Saf Python iş mantığı modülü. Bu modül contracts/api.py RouteStep/Route
ÜRETİR; mobil rota-takip motoru TÜKETİR (sözleşme: api_schema.md).
"""
import networkx as nx

from shelfsense.contracts.api import Route


def build_route(graph: nx.Graph, path: list[str], visit_order: list[str]) -> Route:
    """Sadeleştirilmiş yoldan RouteStep listesi ve Route üretir.

    Girdi: graf + yol + durak sırası. Çıktı: Route (steps + visit_order).
    """
    raise NotImplementedError
