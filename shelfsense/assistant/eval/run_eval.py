"""Asistan değerlendirme koşucusu.

Metrikler: (1) item recall — beklenen ürünlerin ne kadarı çözüldü;
(2) kısıt doğruluğu — çözülen kalemlerde doğru kısıt oranı.
Girdi eval_set.jsonl, çıktı metrik özeti.
"""


def run_eval(eval_set_path: str) -> dict:
    """eval_set.jsonl üzerinde asistanı koşturup metrikleri döndürür.

    Girdi: jsonl yolu. Çıktı: {item_recall, constraint_accuracy} sözlüğü.
    """
    raise NotImplementedError
