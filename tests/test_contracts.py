"""Sözleşme testleri — SKIP YOK, gerçekten çalışır.

(1) data/mock/store_min.json, StoreMap'e karşı geçerli mi?
(2) her placement.product_id, data/product_mapping.json'da mevcut mu?
"""

from shelfsense.contracts.store import StoreMap


def test_store_min_valid_against_contract(store_min_path):
    """store_min.json contracts/store.py StoreMap ile doğrulanabilir olmalı."""
    store = StoreMap.model_validate_json(store_min_path.read_text("utf-8"))
    assert store.nodes, "en az bir düğüm bekleniyor"
    assert store.shelf_blocks, "en az bir raf bloğu bekleniyor"
    assert store.placements, "en az bir yerleşim bekleniyor"


def test_every_placement_product_exists_in_mapping(store_min_path, product_mapping):
    """Her placement.product_id, product_mapping ürünlerinden biri olmalı."""
    store = StoreMap.model_validate_json(store_min_path.read_text("utf-8"))
    product_ids = {product["id"] for product in product_mapping["products"]}
    for placement in store.placements:
        assert placement.product_id in product_ids, (
            f"product_id {placement.product_id} product_mapping.json'da yok"
        )


def test_one_product_per_shelf_block(store_min_path):
    """MVP sadeleştirmesi: her raf bloğunda tek ürün (rapor §3, Bu Hafta).

    Bu kural başlangıç aşamasına aittir; raf içi dikey yerleşim MVP sonrası
    devreye girince bu test güncellenir.
    """
    store = StoreMap.model_validate_json(store_min_path.read_text("utf-8"))
    seen: dict[str, int] = {}
    for placement in store.placements:
        seen[placement.shelf_block_id] = seen.get(placement.shelf_block_id, 0) + 1
    fazla = {block: n for block, n in seen.items() if n > 1}
    assert not fazla, f"raf bloğu başına tek ürün olmalı, fazlası: {fazla}"
