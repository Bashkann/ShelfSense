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
