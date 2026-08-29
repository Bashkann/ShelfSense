"""Sözleşme testleri — SKIP YOK, gerçekten çalışır.

(1) data/mock/store_min.json, StoreMap'e karşı geçerli mi?
(2) her placement.product_id, data/catalog.json'da mevcut mu?
"""
from shelfsense.contracts.store import StoreMap


def test_store_min_valid_against_contract(store_min_path):
    """store_min.json contracts/store.py StoreMap ile doğrulanabilir olmalı."""
    store = StoreMap.model_validate_json(store_min_path.read_text("utf-8"))
    assert store.nodes, "en az bir düğüm bekleniyor"
    assert store.shelf_blocks, "en az bir raf bloğu bekleniyor"
    assert store.placements, "en az bir yerleşim bekleniyor"


def test_every_placement_product_exists_in_catalog(store_min_path, catalog):
    """Her placement.product_id, catalog.json ürün id'lerinden biri olmalı."""
    store = StoreMap.model_validate_json(store_min_path.read_text("utf-8"))
    catalog_ids = {product["id"] for product in catalog["products"]}
    for placement in store.placements:
        assert placement.product_id in catalog_ids, (
            f"product_id {placement.product_id} catalog.json'da yok"
        )
