"""/product router — İNCE HTTP KABUĞU (SQL yok).

Gövde db/repository.py'yi çağırır; burada sorgu bulunmaz.
"""
from fastapi import APIRouter

from shelfsense.contracts.api import ProductLocationResponse

router = APIRouter(prefix="/product", tags=["product"])


@router.get("/{product_id}/location", response_model=ProductLocationResponse)
def read_product_location(product_id: int) -> ProductLocationResponse:
    """Ürünün raf ve erişim düğümünü döndürür (repository'e delege).

    Girdi: catalog product_id. Çıktı: ProductLocationResponse.
    """
    raise NotImplementedError
