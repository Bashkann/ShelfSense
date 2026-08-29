-- ShelfSense PostgreSQL şeması — İSKELET.
-- Kolonlar KASITLI boş: sözleşme (contracts/store.py) dondurulunca oradan
-- türetilecek. Şimdilik yalnızca tablo isimleri sabitlenir.
--
-- TODO: kolonları store.py StoreMap / catalog.json modellerinden türet.

-- catalog.json kaynaklı:
-- CREATE TABLE products (...);
-- CREATE TABLE variants (...);
-- CREATE TABLE shelves (...);        -- kategori düzeyi raflar

-- StoreMap kaynaklı:
-- CREATE TABLE aisles (...);
-- CREATE TABLE nodes (...);
-- CREATE TABLE edges (...);
-- CREATE TABLE shelf_blocks (...);   -- fiziksel raf blokları
-- CREATE TABLE placements (...);     -- ürün ↔ raf bloğu yerleşimi
