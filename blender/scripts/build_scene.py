"""Blender sahne üretimi — mağazayı KODLA kurar.

Blender içinde çalışır (bpy). Sahne kodla üretildiğinden koordinatlar üretim
sırasında zaten eldedir; export_store.py StoreMap JSON'unu buradan yayar.
"""


def build_scene(store_id: str) -> None:
    """Kodla mağaza sahnesini (raflar, koridorlar, düğümler) kurar.

    Girdi: store_id. Çıktı: yok (Blender sahnesini doldurur).
    """
    raise NotImplementedError
