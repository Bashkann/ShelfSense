# ShelfSense

ShelfSense, görme engelli kullanıcılar için **sesli market alışveriş
asistanıdır**. Kullanıcı alışveriş listesini sesle söyler; sistem listeyi
ayrıştırıp ürünleri katalogla eşler, mağaza haritası üzerinde en kısa rotayı
kurar ve adım adım sesli yönergelerle kullanıcıyı raflara götürür. Raf önünde
telefon kamerasıyla ürün tespiti (YOLO) doğrulama sağlar. 4 kişilik ekip,
3 haftalık MVP.

## Tek doğru kaynak

- **`data/catalog.json` ve `shelfsense/contracts/` tek doğru kaynaktır** —
  kimse kendi ürün listesini veya kendi veri şemasını tutmaz. Ürünler, YOLO
  sınıfları, LLM ayrıştırma hedefi ve veritabanı bu iki kaynaktan türetilir.
- **Mağaza koda gömülü değildir**: raf koordinatları ve sayıları JSON'dan
  (`StoreMap`) gelir; mağaza değişince kod değişmez, JSON değişir.

## Sözleşme durumu: TASLAK

`shelfsense/contracts/` henüz **TASLAK**. Blender'cı ve rotacı onaylamadan
hiçbir modül bu şemayı kalıcı kabul etmesin. Açık sorular:
[`store_schema.md`](shelfsense/contracts/store_schema.md) ve
[`api_schema.md`](shelfsense/contracts/api_schema.md). Onaylanınca şema
başlarına **DONDURULDU** damgası ekipçe vurulur.

## Klasör yapısı ve sorumluluk

| Alan | Klasör | Sahip |
|---|---|---|
| Sözleşme (tek doğru kaynak) | `shelfsense/contracts/` | ortak (Blender'cı + rotacı onayı) |
| Asistan (sesli liste → ürün) | `shelfsense/assistant/` | **asistancı** |
| Rota motoru | `shelfsense/routing/` | **rotacı** |
| Veri katmanı | `shelfsense/db/` | backend |
| Backend (ince HTTP kabuğu) | `shelfsense/backend/` | backend |
| Algı / model (paket dışı) | `perception/` | **algıcı** |
| Sahne + StoreMap üretimi | `blender/` | **Blender'cı** |
| Mobil istemci | `mobile/` | **mobilci** |

> **Mimari kural:** İş mantığı saf Python modüllerindedir (`routing`,
> `assistant`, `db`). `backend` yalnızca bu modülleri HTTP'ye açan ince
> kabuktur — router dosyalarında algoritma veya SQL **yoktur**.

## Dal kuralı

Her iş kendi alan dalında: `feat/<alan>` (örn. `feat/routing`,
`feat/assistant`, `feat/perception`, `feat/mobile`).

## Kurulum

### 1) Backend / rota / asistan geliştiricisi

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e . && pip install -r requirements.txt
cp .env.example .env
```

### 2) Model (perception) geliştiricisi

Yukarıdakilere **ek olarak** (PyTorch ~2 GB — yalnızca model eğitecek kişi kurar):

```bash
pip install -r requirements-ml.txt
```

## Doğrulama

```bash
python -m shelfsense.contracts.validate data/mock/store_min.json
pytest tests/test_contracts.py
```

## CI

Sözleşme dondurulduğunda eklenecek — henüz **yok** (bilinçli karar).
