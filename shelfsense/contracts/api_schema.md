DURUM: TASLAK — onay bekleyen: rotacı, asistancı · son değişiklik: 2026-08-29

> Bu şema `contracts/api.py`'nin insan-okur karşılığıdır. Çakışma olursa
> `api.py` bağlayıcıdır. Ekip onaylayınca başa **DONDURULDU** damgası ekip
> tarafından vurulur — iskeleti kuran vurmaz.

---

## AÇIK SORULAR (onay bekliyor)

- [ ] **`RouteStep.trigger` tetiklenme koşulu.**
  Adım ne zaman "tamamlandı" sayılır — hedef düğüme varış mı, yoksa mesafe
  eşiği mi (örn. hedefe 2 m kala)? Mobil rota-takip motorunun davranışını
  belirler.
- [ ] **`ParsedItem.confidence` eşiği.**
  Eşik altı kalan kalem `unresolved`'a mı düşer, yoksa düşük güvenle mi
  döner? (İç model kararı — bkz. `assistant/schemas.py`.)

---

## İç ↔ dış model ayrımı

- **İç model** (`assistant/schemas.py`): `ParsedItem`, `ParsedList` — LLM ile
  asistan modülleri arasında dolaşır.
- **Dış model** (`contracts/api.py`): HTTP istek/yanıt gövdeleri.
- **Kural:** çakışırsa iç model kazanır. `api.py`, `ParsedItem`'ı **import
  eder**, yeniden tanımlamaz.

## Uç noktalar (sözleşme)

| Uç nokta | İstek | Yanıt |
|---|---|---|
| `POST /assistant/parse` | `ParseListRequest(text)` | `ParseListResponse(items, unresolved)` |
| `POST /route` | `RouteRequest(store_id, product_ids, start_node_id)` | `Route(steps, total_distance_m, visit_order)` |
| `GET /product/{id}/location` | — | `ProductLocationResponse(product_id, shelf_block_id, access_node_id)` |

## Rota talimatı sözleşmesi

- **`RouteStep`** (`index`, `instruction_text`, `distance_m`, `target_node_id`,
  `trigger`): tek yönerge. **ÜRETEN** `routing/instructions.py`, **TÜKETEN**
  mobil rota-takip motoru. İkisi aynı kişide olsa bile sözleşme olarak yazılır.
- **`Route`** (`steps`, `total_distance_m`, `visit_order`): `visit_order`
  ziyaret sırasıyla **`ShelfBlock.id`** listesi — ürün id'si DEĞİL; aynı
  raftaki ürünler tek durak sayılır.

## Ürün id'leri

`RouteRequest.product_ids` ve `ProductLocationResponse.product_id`,
`data/catalog.json`'daki **int** `id` alanıyla birebir aynıdır.
