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

`.env.example` dosyasını kopyalayarak yerel yapılandırmayı oluşturun, PostgreSQL
servisini başlatın ve container sağlığını kontrol edin:

```bash
cp .env.example .env
docker compose up -d db
docker compose ps
```

`docker compose ps` çıktısında `db` servisi `healthy` olmalıdır. Ardından
migration'ları uygulayın:

```bash
python -m alembic upgrade head
```

Yerel bağlantı portu `POSTGRES_PORT` ile değiştirilirse `DATABASE_URL` içindeki
port da aynı değere güncellenmelidir.

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
