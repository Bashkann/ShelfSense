"""YOLO .pt → ONNX dönüştürücü (mobil çıkarım için).

perception/ paket DIŞINDA. `make mobile-assets` bu çıktıyı mobile/ assets'e koyar.
"""


def to_onnx(weights_path: str, out_path: str) -> str:
    """.pt ağırlığını ONNX'e dönüştürür; yazılan dosya yolunu döndürür.

    Girdi: .pt yolu + çıktı .onnx yolu. Çıktı: yazılan dosya yolu.
    """
    raise NotImplementedError
