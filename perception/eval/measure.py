"""Model doğruluk ölçümü (mAP, precision/recall).

perception/ paket DIŞINDA. Girdi model + test kümesi, çıktı metrik özeti.
"""


def measure(weights_path: str, data_yaml: str) -> dict:
    """Modeli test kümesinde ölçer; metrik sözlüğü döndürür.

    Girdi: ağırlık + data.yaml. Çıktı: {map, precision, recall} sözlüğü.
    """
    raise NotImplementedError
