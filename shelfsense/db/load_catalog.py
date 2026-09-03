"""Deprecated legacy catalog-loader entry point.

Product and store data are imported together through ``shelfsense.db.importer``
from ``data/product_mapping.json`` and ``data/store.json``.
"""


def load_catalog(path: str = "data/product_mapping.json") -> int:
    """Reject use of the deprecated split loader; use the unified importer."""

    raise NotImplementedError(
        f"load_catalog({path!r}) is deprecated; use shelfsense.db.importer"
    )
