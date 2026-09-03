"""ShelfSense mağaza haritası sözleşmesi — TEK DOĞRU KAYNAK.

Sabit kabuller (ayrıntılı gerekçe: store_schema.md):
- 2D (x, y) METRE; Z sözleşmede yok, projeksiyon Blender export'ta düşürülür.
- Blender koordinatı OLDUĞU GİBİ; origin taşıma yok.
- entrance_node_id legacy export uyumluluk alanıdır; kalıcı rota başlangıcı değildir.
- id'ler benzersiz string; ShelfBlock.id product_mapping.json shelf'inden türetilir.
"""

from typing import Literal

from pydantic import BaseModel

# Rafın erişilebilir yüzü. "open" = dört taraftan erişilir ada (meyve kasaları).
Facing = Literal["+x", "-x", "+y", "-y", "open"]


class Node(BaseModel):
    """Koridor/graf düğümü. x,y = metre cinsinden Blender koordinatı."""

    id: str
    x: float
    y: float
    kind: str  # KARAR GEREKLİ: serbest string mi, enum mu (kavşak/raf-önü/giriş)?


class Edge(BaseModel):
    """Legacy yönsüz kenar. weight = metre cinsinden yürüme maliyeti."""

    from_id: str
    to_id: str
    weight: float  # KARAR GEREKLİ: öklid mesafe mi, elle ağırlık da olur mu?


class ShelfBlock(BaseModel):
    """Fiziksel raf bloğu. access_node_id = önündeki koridor düğümü id'si."""

    id: str
    aisle_id: str
    x: float
    y: float
    w: float
    h: float
    facing: Facing
    access_node_id: str  # KARAR GEREKLİ: elle mi konur, export mi hesaplar?


class Placement(BaseModel):
    """Ürün yerleşimi. product_id, product_mapping.json id'siyle birebir aynı."""

    product_id: int
    shelf_block_id: str
    slot: str  # KARAR GEREKLİ: serbest etiket mi, yapısal (raf katı/göz no) mu?


class Aisle(BaseModel):
    """Koridor/reyon grubu. name = insan-okur etiket."""

    id: str
    name: str


class StoreMap(BaseModel):
    """Tam mağaza haritası. Doğrulama giriş noktası: contracts/validate.py."""

    store_id: str
    entrance_node_id: str  # Legacy export compatibility; importer does not persist it.
    nodes: list[Node]
    edges: list[Edge]
    aisles: list[Aisle]
    shelf_blocks: list[ShelfBlock]
    placements: list[Placement]
