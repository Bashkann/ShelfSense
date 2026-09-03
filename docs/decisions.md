# Kararlar (ADR)

> İskelet — başlık düzeyinde. Her karar verildiğinde madde eklenecek.

## Verilmiş kabuller
- 2D (x, y) metre koordinat; Z sözleşmede yok (projeksiyon Blender export'ta).
- Ürün verisinin tek doğru kaynağı `data/product_mapping.json`, mağaza
  verisinin tek doğru kaynağı `data/store.json` dosyasıdır.
- perception/ paket dışında (üretim aracı, ürünün parçası değil).
- Merkezi veritabanı PostgreSQL 16'dır.
- Python veri erişim katmanında SQLAlchemy 2 ve senkron Psycopg 3 kullanılır.
- Veritabanı şema değişiklikleri forward-only Flyway migration'larıyla yönetilir.
- Veritabanı şemasının tek doğru kaynağı Flyway migration'larıdır;
  `schema.sql` kullanılmaz.

## Açık kararlar (bkz. contracts/*_schema.md AÇIK SORULAR)
### Erişim düğümü: elle mi, hesaplanarak mı?
### facing enum'u yeterli mi?
### ShelfBlock id formatı
### kategori ↔ raf bloğu eşlemesi
### RouteStep.trigger: düğüme varış mı, mesafe eşiği mi?

## Reddedilenler
<!-- neden seçilmedi -->

## Importer safety decisions

- Missing active shelves may be deactivated automatically. A shelf that is
  already inactive is never reactivated by import, even if it reappears in
  `store.json`; reactivation is an explicit operator/admin decision.
- Existing `shelf_levels` are not guessed away or automatically deleted. An
  incompatible vocabulary change such as `A/B/C/D` to `ust/orta/alt` that
  conflicts with retained levels fails global preflight with
  `SHELF_LEVEL_PROJECTED_CONFLICT` and requires an explicit manual level
  migration or cleanup decision.
- Import is single-writer per store for the MVP. Per-store PostgreSQL advisory
  transaction locking (or equivalent store-scoped locking) is deferred
  hardening.
- An explicit edge `is_bidirectional` boolean wins. If it is absent, the legacy
  fallback is `true` and `LEGACY_EDGE_DIRECTIONALITY_DEFAULTED` is reported.
  The current real Blender export does not emit this field, so it cannot yet
  express one-way edges; a future export contract should emit an explicit
  `true` or `false`.
- Legacy `entrance_node_id` is validated when present but is not persisted.
  Entrances are `navigation_nodes` with `node_type='giris'`, multiple entrances
  are supported, and future routing starts from the resolved user position.
