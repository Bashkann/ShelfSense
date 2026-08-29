"""Asistan ayrıştırıcı testleri — İSKELET (skip'li).

Sözleşme (contracts/) dondurulup assistant/ implement edilince skip kalkar.
"""
import pytest

pytestmark = pytest.mark.skip(reason="assistant/ henüz implement edilmedi")


def test_parse_resolves_known_synonyms() -> None:
    """Bilinen synonym'ler doğru catalog product_id'ye çözülmeli."""
    raise NotImplementedError


def test_parse_collects_unresolved_items() -> None:
    """Eşleşmeyen ifadeler unresolved listesine düşmeli."""
    raise NotImplementedError
