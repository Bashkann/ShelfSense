.PHONY: mobile-assets

# Mobil çevrimdışı varlıkları üretir: catalog.db (SQLite) + model.onnx.
# Sözleşme dondurulup export_sqlite.py ve to_onnx.py implement edilince
# aşağıdaki gerçek komutlar açılır.
mobile-assets:
	@echo "TODO: export_sqlite ve to_onnx implement edilmedi"
#	python -m shelfsense.db.export_sqlite --out mobile/app/src/main/assets/catalog.db
#	python perception/export/to_onnx.py --out mobile/app/src/main/assets/model.onnx
