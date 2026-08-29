# perception/

1. **Bu klasör çalışan sistem tarafından import EDİLMEZ.** Blender ile aynı
   konumda durur — bir üretim aracıdır, ürünün (paketlenen `shelfsense`) parçası
   değildir. Bu yüzden `pyproject.toml` içinde `packages` listesine girmez ve
   `__init__.py` taşımaz.
2. **`dataset/data.yaml` elle tutulmaz.** `build_data_yaml.py` onu
   `catalog.json`'daki `class_idx` sırasından üretir (sınıf sırası tek yerde
   kalsın diye). Üretilen dosya **commit edilmez** — `.gitignore`'dadır.
