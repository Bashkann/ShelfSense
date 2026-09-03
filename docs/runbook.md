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

### Importer operational rules

- Do not run two imports for the same store concurrently. The MVP importer is
  single-writer per store. A stale concurrent plan cannot violate database
  integrity, but it can roll back as `WRITE_TRANSACTION_FAILED`. A per-store
  advisory transaction lock is deferred hardening.
- A previously inactive shelf is never automatically reactivated when it
  reappears in `store.json`. Reactivation is an explicit operator/admin action;
  source reappearance alone does not establish operational availability.
- If a physical shelf changes incompatibly from `A/B/C/D` to `ust/orta/alt`
  and retained levels conflict, global preflight stops with
  `SHELF_LEVEL_PROJECTED_CONFLICT`. The importer does not delete old levels or
  guess that the shelf was rebuilt; an explicit manual migration/cleanup
  decision is required.
- An explicit edge `is_bidirectional` boolean wins. If the field is absent, the
  legacy fallback is `true` and `LEGACY_EDGE_DIRECTIONALITY_DEFAULTED` is
  reported. The current real Blender export does not emit the field and cannot
  yet express one-way edges.
- `entrance_node_id` is a legacy export-compatibility field. When present it is
  validated as a reference to a `giris` node in the same source, but is not
  persisted. Database entrances are `navigation_nodes.node_type='giris'`, can
  be multiple, and future routing starts from the resolved current user
  position rather than a store-level entrance foreign key.

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
