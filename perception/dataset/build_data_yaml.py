"""catalog.json → YOLO data.yaml üretici.

perception/ paket DIŞINDA. class_idx sırası TEK yerde (catalog.json) kalsın
diye data.yaml elle yazılmaz; bu script üretir. Çıktı .gitignore'da (commit yok).
"""


def build_data_yaml(catalog_path: str, out_path: str) -> list[str]:
    """catalog.json class_idx sırasına göre YOLO sınıf listesi yazar.

    Girdi: catalog.json + çıktı data.yaml yolu. Çıktı: sınıf adı listesi.
    """
    raise NotImplementedError
