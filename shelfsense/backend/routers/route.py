"""/route router — İNCE HTTP KABUĞU (algoritma yok).

Gövde routing/ modüllerini çağırır; rota hesabı burada yapılmaz.
"""
from fastapi import APIRouter

from shelfsense.contracts.api import Route, RouteRequest

router = APIRouter(prefix="/route", tags=["route"])


@router.post("", response_model=Route)
def create_route(request: RouteRequest) -> Route:
    """Ürün listesi için rota üretir (routing/ modüllerine delege).

    Girdi: RouteRequest. Çıktı: Route.
    """
    raise NotImplementedError
