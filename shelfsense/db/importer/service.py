"""Public preflight and atomic import service entry points."""

from collections.abc import Callable
from pathlib import Path
from uuid import UUID, uuid4

from shelfsense.config import Settings, get_settings
from shelfsense.db.connection import get_engine
from shelfsense.db.importer.preflight import (
    build_import_plan,
    thresholds_from_settings,
)
from shelfsense.db.importer.report import (
    ImportAborted,
    ImportReport,
    abort,
    new_report,
)
from shelfsense.db.importer.repository import SqlImportRepository
from shelfsense.db.importer.source import SourceBundle, SourceLoadError, load_sources
from shelfsense.db.importer.state import ImportPlan, ImportRepository, ImportThresholds


def preflight_from_files(
    store_path: str | Path = "data/store.json",
    product_mapping_path: str | Path = "data/product_mapping.json",
    *,
    store_name: str | None = None,
    settings: Settings | None = None,
    repository: ImportRepository | None = None,
    uuid_factory: Callable[[], UUID] = uuid4,
) -> ImportPlan:
    """Read sources and build a plan; never write database state."""

    report = new_report(store_path, product_mapping_path)
    try:
        bundle = load_sources(store_path, product_mapping_path)
    except SourceLoadError as error:
        abort(report, error.category, **error.details)
    active_settings = settings or get_settings()
    active_repository = repository or SqlImportRepository(get_engine())
    return build_import_plan(
        bundle,
        active_repository,
        thresholds_from_settings(active_settings),
        report,
        store_name=store_name,
        uuid_factory=uuid_factory,
    )


def preflight_bundle(
    bundle: SourceBundle,
    repository: ImportRepository,
    thresholds: ImportThresholds,
    *,
    store_name: str | None = None,
    uuid_factory: Callable[[], UUID] = uuid4,
    store_path: str = "<synthetic-store>",
    product_mapping_path: str = "<synthetic-products>",
) -> ImportPlan:
    """Build a plan from already parsed synthetic or application sources."""

    return build_import_plan(
        bundle,
        repository,
        thresholds,
        new_report(store_path, product_mapping_path),
        store_name=store_name,
        uuid_factory=uuid_factory,
    )


def import_from_files(
    store_path: str | Path = "data/store.json",
    product_mapping_path: str | Path = "data/product_mapping.json",
    *,
    store_name: str | None = None,
    settings: Settings | None = None,
    repository: ImportRepository | None = None,
    uuid_factory: Callable[[], UUID] = uuid4,
) -> ImportReport:
    """Run global preflight, then apply its plan as one transaction."""

    active_repository = repository or SqlImportRepository(get_engine())
    plan = preflight_from_files(
        store_path,
        product_mapping_path,
        store_name=store_name,
        settings=settings,
        repository=active_repository,
        uuid_factory=uuid_factory,
    )
    return apply_preflighted_plan(plan, active_repository)


def import_bundle(
    bundle: SourceBundle,
    repository: ImportRepository,
    thresholds: ImportThresholds,
    *,
    store_name: str | None = None,
    uuid_factory: Callable[[], UUID] = uuid4,
) -> ImportReport:
    """Import an already parsed bundle, primarily for isolated tests."""

    plan = preflight_bundle(
        bundle,
        repository,
        thresholds,
        store_name=store_name,
        uuid_factory=uuid_factory,
    )
    return apply_preflighted_plan(plan, repository)


def apply_preflighted_plan(
    plan: ImportPlan, repository: ImportRepository
) -> ImportReport:
    """Cross the write gate exactly once with a fully validated plan."""

    try:
        repository.apply_plan(plan)
    except Exception as error:
        plan.report.add(
            "WRITE_TRANSACTION_FAILED",
            "failure",
            error_type=type(error).__name__,
            message=str(error),
        )
        raise ImportAborted(plan.report) from error
    return plan.report
