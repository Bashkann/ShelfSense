"""Structured importer reports and abort errors."""

from dataclasses import asdict, dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal
from uuid import UUID

Severity = Literal["info", "warning", "failure"]


@dataclass
class ReportEntry:
    """A single informational, warning, or failure report entry."""

    category: str
    severity: Severity
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class TableStats:
    """Per-table projected write and retention counts."""

    inserted: int = 0
    updated: int = 0
    unchanged: int = 0
    deleted: int = 0
    deactivated: int = 0
    retained_missing: int = 0


@dataclass
class ThresholdResult:
    """A missing-record threshold calculation."""

    baseline: int
    missing_count: int
    missing_ratio: Decimal
    max_count: int
    max_ratio: Decimal
    affected_ids: list[str]


@dataclass
class ImportReport:
    """Complete preflight and import outcome."""

    store_path: str
    product_mapping_path: str
    store_external_id: str = ""
    preflight_status: Literal["PASS", "FAIL"] = "PASS"
    tables: dict[str, TableStats] = field(default_factory=dict)
    entries: list[ReportEntry] = field(default_factory=list)
    thresholds: dict[str, ThresholdResult] = field(default_factory=dict)

    def stats(self, table: str) -> TableStats:
        """Return a mutable stats bucket for a table."""

        return self.tables.setdefault(table, TableStats())

    def add(self, category: str, severity: Severity, **details: Any) -> None:
        """Append one structured report entry."""

        self.entries.append(ReportEntry(category, severity, details))

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""

        return _jsonable(asdict(self))


class ImportAborted(RuntimeError):
    """Raised when the global preflight gate rejects an import."""

    def __init__(self, report: ImportReport):
        self.report = report
        category = report.entries[-1].category if report.entries else "IMPORT_ABORTED"
        super().__init__(category)

    @property
    def category(self) -> str:
        """Return the failure category that stopped preflight."""

        return self.report.entries[-1].category


def abort(report: ImportReport, category: str, **details: Any) -> None:
    """Mark preflight failed and raise its structured exception."""

    report.preflight_status = "FAIL"
    report.add(category, "failure", **details)
    raise ImportAborted(report)


def new_report(store_path: str | Path, product_path: str | Path) -> ImportReport:
    """Create the report before any source parsing or database access."""

    return ImportReport(str(store_path), str(product_path))


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, (Decimal, UUID, Path)):
        return str(value)
    return value
