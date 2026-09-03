# Mimari

> İskelet — başlık düzeyinde. İçerik sözleşme dondurulunca doldurulacak.

## Genel bakış

## Bileşenler
### Sözleşme katmanı (contracts/) — tek doğru kaynak
### Asistan (assistant/) — sesli liste ayrıştırma
### Rota motoru (routing/)
### Veri katmanı (db/)
### Backend (backend/) — ince HTTP kabuğu
### Algı (perception/) — paket dışı üretim aracı
### Blender (blender/) — sahne üretimi + StoreMap yayımı
### Mobil (mobile/) — çevrimdışı istemci

## Veri akışı
<!-- product_mapping.json + store.json → db importer → db → backend → mobil -->

## Importer boundaries

- `entrance_node_id` is a legacy export-compatibility field. The importer
  validates it when present but does not persist it. Database entrances are
  `navigation_nodes` whose `node_type` is `giris`; multiple entrances are
  supported. Future routing starts from the resolved current user position,
  not from a store-level entrance foreign key.
- Planning currently happens before the write transaction. The MVP importer is
  therefore single-writer per store: two imports for the same store must not run
  concurrently. Database constraints and rollback preserve integrity, but a
  stale concurrent plan can fail as `WRITE_TRANSACTION_FAILED`. A future
  hardening step is a per-store PostgreSQL advisory transaction lock or an
  equivalent store-scoped lock.

## Mimari kural
İş mantığı saf Python modüllerinde (routing, assistant, db). backend yalnızca
bu modülleri HTTP'ye açan ince kabuktur — router'larda algoritma/SQL yok.
