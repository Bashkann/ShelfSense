"""/assistant router — İNCE HTTP KABUĞU (LLM/kural mantığı yok).

Gövde assistant/ modüllerini çağırır; ayrıştırma burada yapılmaz.
"""
from fastapi import APIRouter

from shelfsense.contracts.api import ParseListRequest, ParseListResponse

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/parse", response_model=ParseListResponse)
def parse_list(request: ParseListRequest) -> ParseListResponse:
    """Sesli liste metnini ayrıştırır (assistant/ modüllerine delege).

    Girdi: ParseListRequest. Çıktı: ParseListResponse.
    """
    raise NotImplementedError
