"""StoreMap'ten yürüme grafı kurma.

Saf Python iş mantığı modülü (backend değil). Girdi StoreMap, çıktı networkx
graf; düğüm=Node, kenar=Edge(weight=metre). Rota çekirdeği.
"""
import networkx as nx

from shelfsense.contracts.store import StoreMap


def build_graph(store: StoreMap) -> nx.Graph:
    """StoreMap'ten ağırlıklı yürüme grafı kurar.

    Girdi: StoreMap. Çıktı: networkx.Graph (kenar ağırlığı = metre).
    """
    raise NotImplementedError
