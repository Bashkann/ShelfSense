# Runbook

> İskelet — başlık düzeyinde. Adımlar implement edildikçe doldurulacak.

## Kurulum
<!-- bkz. kök README.md "Kurulum" -->

## Sözleşme doğrulama
```bash
python -m shelfsense.contracts.validate data/mock/store_min.json
pytest tests/test_contracts.py
```

## Veritabanı
### Katalog yükleme (load_catalog)
### Mağaza yükleme (load_store)

## Backend çalıştırma
<!-- uvicorn ... (main.py implement edilince) -->

## Mobil varlık üretimi
```bash
make mobile-assets
```

## Model (perception)
### Sentetik veri → eğitim → ONNX dışa aktarım
