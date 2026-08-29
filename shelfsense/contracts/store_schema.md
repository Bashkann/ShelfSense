DURUM: TASLAK — onay bekleyen: Blender'cı, rotacı · son değişiklik: 2026-08-29

> Bu şema `contracts/store.py`'nin insan-okur karşılığıdır. Çakışma olursa
> `store.py` bağlayıcıdır. Ekip onaylayınca bu dosyanın başına **DONDURULDU**
> damgası ekip tarafından vurulur — bu damgayı iskeleti kuran vurmaz.

---

## AÇIK SORULAR (onay bekliyor)

- [ ] **Erişim düğümü elle mi, hesaplanarak mı?**
  `ShelfBlock.access_node_id` Blender'da rafın önüne elle mi konacak, yoksa
  export script'i koridor merkezinden mi hesaplayacak? Karar `export_store.py`
  ile `build_scene.py` iş bölümünü belirler.
- [ ] **`facing` enum'u tüm raflar için yeterli mi?**
  Şu an `+x | -x | +y | -y | open`. Köşe/çapraz raf veya iki yüzü açık ada
  senaryosu çıkarsa enum genişler.
- [ ] **`ShelfBlock.id` formatı.**
  `catalog.json` yalnızca kategori düzeyi raf verir (`shelf_dairy` vb.).
  Fiziksel blok id'si bundan nasıl türetilecek? Öneri:
  `<shelf>__b<NN>` (örn. `shelf_dairy__b01`). Onay bekliyor.
- [ ] **Kategori ↔ raf bloğu eşlemesi.**
  `catalog.json`'daki `shelf` alanı KATEGORİ (5 raf: dry_goods, cleaning,
  dairy, produce, beverages), fiziksel mağazada bir kategori birden çok bloğa
  yayılabilir. Bir kategori → kaç blok, hangi ürün hangi bloğa? Bu eşleme
  `Placement` üretilirken netleşmeli.

---

## Koordinat ve birim kabulleri

- **2D (x, y), birim metre.** Z ekseni sözleşmeye girmez; yükseklik bilgisi
  rota için gereksiz olduğundan Blender export sırasında düşürülür (projeksiyon).
- **Origin taşıma yok.** Blender koordinatları olduğu gibi kullanılır. Rota
  başlangıcı ayrı bir offset değil, `StoreMap.entrance_node_id` ile verilir.
- **id'ler** anlamlı ve benzersiz string.

## Alan alan

- **Node** (`id`, `x`, `y`, `kind`): graf/koridor düğümü. `kind` düğüm rolü
  (kavşak, raf-önü, giriş) — serbest string mı sınırlı enum mu açık soru.
- **Edge** (`from_id`, `to_id`, `weight`): yönsüz koridor kenarı. `weight`
  metre cinsinden yürüme maliyeti.
- **ShelfBlock** (`id`, `aisle_id`, `x`, `y`, `w`, `h`, `facing`,
  `access_node_id`): fiziksel raf bloğu. `w`/`h` blok genişlik/derinliği (m).
  `facing` erişilebilir yüz. `access_node_id` bloğun önündeki koridor düğümü.
- **Placement** (`product_id`, `shelf_block_id`, `slot`): ürünün rafa
  yerleşimi. `product_id` **`catalog.json`'daki int id ile birebir**. `slot`
  raf içi konum — serbest etiket mi yapısal mı açık soru.
- **Aisle** (`id`, `name`): koridor/reyon grubu.
- **StoreMap** (`store_id`, `entrance_node_id`, `nodes`, `edges`, `aisles`,
  `shelf_blocks`, `placements`): tam harita. Doğrulama:
  `python -m shelfsense.contracts.validate <store.json>`.
