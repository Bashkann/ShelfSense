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
docker compose run --rm flyway migrate
```

Yerel bağlantı portu `POSTGRES_PORT` ile değiştirilirse `DATABASE_URL` içindeki
port da aynı değere güncellenmelidir.

### Ürün ve mağaza importu

Ürün ve mağaza verisi için kanonik yol birleşik importer'dır. Önce yalnızca
preflight çalıştırın:

```bash
python -m shelfsense.db.importer --store data/store.json --products data/product_mapping.json --store-name "<mağaza adı>" --preflight-only
```

Preflight onaylandıktan sonra aynı komutu `--preflight-only` olmadan çalıştırın.
Eski `load_catalog` ve `load_store` giriş noktalarını kullanmayın.

## Backend çalıştırma
<!-- uvicorn ... (main.py implement edilince) -->

## Mobil varlık üretimi
```bash
make mobile-assets
```

## Model (perception)
### Sentetik veri → eğitim → ONNX dışa aktarım
