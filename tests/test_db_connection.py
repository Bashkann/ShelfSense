"""Veritabanı bağlantı katmanı regresyon testleri."""

import os
import subprocess
import sys
from pathlib import Path

from conftest import REPO_ROOT


def test_connection_module_imports_without_env_file(tmp_path: Path) -> None:
    """Bağlantı modülü, ayarları import sırasında yüklememelidir."""

    environment = os.environ.copy()
    environment.pop("DATABASE_URL", None)
    environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, (str(REPO_ROOT), environment.get("PYTHONPATH", "")))
    )

    result = subprocess.run(
        [sys.executable, "-c", "import shelfsense.db.connection"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
