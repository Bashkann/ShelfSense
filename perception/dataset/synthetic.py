"""Sentetik eğitim verisi üretimi (Blender render + YOLO etiket).

perception/ paket DIŞINDA — çalışan sistem import ETMEZ (bkz. README).
catalog.json class_idx'lerini kullanarak görüntü + etiket üretir.
"""


def generate(out_dir: str, count: int) -> int:
    """Sentetik görüntü ve YOLO etiketi üretir; üretilen kare sayısını döndürür.

    Girdi: çıktı dizini + adet. Çıktı: üretilen görüntü sayısı.
    """
    raise NotImplementedError
