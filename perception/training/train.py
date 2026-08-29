"""YOLO model eğitimi (ultralytics).

perception/ paket DIŞINDA — üretim aracı. Girdi data.yaml, çıktı .pt ağırlık.
"""


def train(data_yaml: str, epochs: int) -> str:
    """data.yaml ile YOLO modeli eğitir; ağırlık dosyası yolunu döndürür.

    Girdi: data.yaml + epoch sayısı. Çıktı: .pt ağırlık yolu.
    """
    raise NotImplementedError
