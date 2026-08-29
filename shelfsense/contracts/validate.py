"""StoreMap JSON doğrulayıcı CLI.

Kullanım: python -m shelfsense.contracts.validate <store.json>
Başarılıysa düğüm/raf sayısını basar; hatalıysa mesajı yazıp exit(1).
"""
import sys
from pathlib import Path

from pydantic import ValidationError

from shelfsense.contracts.store import StoreMap


def main() -> None:
    """argv[1]'deki JSON'u StoreMap'e karşı doğrular, özet basar."""
    if len(sys.argv) != 2:
        print("kullanım: python -m shelfsense.contracts.validate <store.json>")
        sys.exit(1)
    try:
        store = StoreMap.model_validate_json(Path(sys.argv[1]).read_text("utf-8"))
    except (ValidationError, OSError) as err:
        print(f"GEÇERSİZ: {err}")
        sys.exit(1)
    print(f"GEÇERLİ: {len(store.nodes)} düğüm, {len(store.shelf_blocks)} raf bloğu, "
          f"{len(store.placements)} yerleşim.")


if __name__ == "__main__":
    main()
