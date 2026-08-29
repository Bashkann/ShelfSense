"""/map router — İNCE HTTP KABUĞU (algoritma/SQL yok).

Gövde db/repository.py'yi çağırır; burada iş mantığı bulunmaz.
"""
from fastapi import APIRouter

from shelfsense.contracts.store import StoreMap

router = APIRouter(prefix="/map", tags=["map"])


@router.get("/{store_id}", response_model=StoreMap)
def read_store_map(store_id: str) -> StoreMap:
    """Mağaza haritasını döndürür (repository.get_store_map'e delege).

    Girdi: store_id yol parametresi. Çıktı: StoreMap.
    """
    raise NotImplementedError
