"""Veri kümesini train/val/test olarak böler.

perception/ paket DIŞINDA. Girdi görüntü dizini, çıktı YOLO split dizinleri.
"""


def split(data_dir: str, ratios: tuple[float, float, float]) -> dict:
    """Görüntüleri verilen oranlarla train/val/test'e böler.

    Girdi: veri dizini + oranlar. Çıktı: split → görüntü sayısı sözlüğü.
    """
    raise NotImplementedError
