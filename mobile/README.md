# mobile/

Android istemci (rota takip + raf tarama).

## Açma

Android Studio bu klasörden (`mobile/`) açılır — **repo kökünden değil**.

## Varlıklar (çevrimdışı veri + model)

Çevrimdışı `catalog.db` (SQLite) ve `model.onnx`, repo kökünde üretilir:

```bash
make mobile-assets
```

Üretilen dosyalar `app/src/main/assets/` altına konur ve **commit edilmez**
(bkz. `mobile/.gitignore`). Şimdilik hedef yalnızca TODO basar; export
script'leri (`db/export_sqlite.py`, `perception/export/to_onnx.py`) sözleşme
dondurulunca implement edilecek.
