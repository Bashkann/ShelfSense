"""Rota motoru testleri — İSKELET (skip'li).

Sözleşme (contracts/) dondurulup routing/ implement edilince skip kalkar.
"""
import pytest

pytestmark = pytest.mark.skip(reason="routing/ henüz implement edilmedi")


def test_shortest_path_returns_expected_distance() -> None:
    """İki düğüm arası en kısa yol beklenen toplam mesafeyi döndürmeli."""
    raise NotImplementedError


def test_route_visit_order_is_shelf_blocks() -> None:
    """Route.visit_order ShelfBlock.id listesi olmalı (ürün id'si değil)."""
    raise NotImplementedError
