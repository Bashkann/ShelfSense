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

## Mimari kural
İş mantığı saf Python modüllerinde (routing, assistant, db). backend yalnızca
bu modülleri HTTP'ye açan ince kabuktur — router'larda algoritma/SQL yok.
