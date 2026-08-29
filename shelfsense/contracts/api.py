"""ShelfSense DIŞ (HTTP sınırı) sözleşmesi — TEK DOĞRU KAYNAK.

ParsedItem burada yeniden TANIMLANMAZ; assistant.schemas'tan import edilir
(iç model kazanır kuralı, bkz. assistant/schemas.py).

Rota talimatı sözleşmesi (RouteStep/Route) iki tarafı bağlar:
- ÜRETEN: routing/instructions.py
- TÜKETEN: mobil rota-takip motoru
İkisi aynı kişide olsa bile sözleşme olarak burada dondurulur.
"""
from pydantic import BaseModel

from shelfsense.assistant.schemas import ParsedItem


class ParseListRequest(BaseModel):
    """POST /assistant/parse girdisi. text = ham sesli liste metni."""
    text: str


class ParseListResponse(BaseModel):
    """Ayrıştırma yanıtı. items çözülenler, unresolved çözülemeyen ham ifadeler."""
    items: list[ParsedItem]
    unresolved: list[str]


class RouteStep(BaseModel):
    """Tek rota adımı. instructions.py üretir, mobil motor tüketir."""
    index: int
    instruction_text: str
    distance_m: float
    target_node_id: str
    # KARAR GEREKLİ: tetiklenme koşulu düğüme varış mı, mesafe eşiği mi?
    trigger: str


class Route(BaseModel):
    """Tam rota. visit_order = ziyaret sırasıyla ShelfBlock.id listesi.

    visit_order ürün id'si DEĞİL: aynı raftaki ürünler tek durak sayılır.
    """
    steps: list[RouteStep]
    total_distance_m: float
    visit_order: list[str]


class RouteRequest(BaseModel):
    """POST /route girdisi. product_ids = catalog.json int id listesi."""
    store_id: str
    product_ids: list[int]
    start_node_id: str


class ProductLocationResponse(BaseModel):
    """GET /product/{id}/location yanıtı. Ürünün rafı ve erişim düğümü."""
    product_id: int
    shelf_block_id: str
    access_node_id: str
