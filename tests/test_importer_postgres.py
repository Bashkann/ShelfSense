"""Opt-in PostgreSQL integration coverage for the importer repository."""

import os
from decimal import Decimal

import pytest
from importer_helpers import (
    DEFAULT_THRESHOLDS,
    SequentialUUIDs,
    categories,
    make_bundle,
)
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Connection, make_url

from shelfsense.db.importer.report import ImportAborted
from shelfsense.db.importer.repository import SqlImportRepository
from shelfsense.db.importer.service import (
    apply_preflighted_plan,
    import_bundle,
    preflight_bundle,
)

DATABASE_URL_ENV = "SHELFSENSE_IMPORT_INTEGRATION_DATABASE_URL"
SAFE_DATABASE_PREFIX = "shelfsense_import_validation_"


class FailingSqlImportRepository(SqlImportRepository):
    """Raise after several real SQL writes to prove transaction rollback."""

    def _write_products(self, connection: Connection, plan) -> None:
        super()._write_products(connection, plan)
        raise RuntimeError("injected integration write failure")


def test_postgres_import_is_idempotent_and_atomic() -> None:
    engine = _integration_engine()
    repository = SqlImportRepository(engine)
    try:
        first_report = import_bundle(
            make_bundle(),
            repository,
            DEFAULT_THRESHOLDS,
            store_name="ShelfSense Market",
            uuid_factory=SequentialUUIDs(),
        )
        first_state = repository.read_store_state("store-1")
        first_ids = _all_ids(first_state)

        assert first_state.store is not None
        assert first_state.store.name == "ShelfSense Market"
        assert first_state.store.is_active is True
        assert first_state.products["1"].external_id == "1"
        assert first_state.shelves["shelf-1"].side_description == "left wall"
        edge = next(iter(first_state.edges.values()))
        assert edge.distance_m == Decimal("2.000")
        assert edge.is_bidirectional is True
        assert edge.from_node_id < edge.to_node_id
        assert "LEGACY_EDGE_DIRECTIONALITY_DEFAULTED" in categories(first_report)
        assert _table_counts(engine) == {
            "stores": 1,
            "navigation_nodes": 2,
            "aisles": 1,
            "products": 1,
            "navigation_edges": 1,
            "shelf_blocks": 1,
            "shelf_levels": 4,
            "product_placements": 1,
            "product_placement_levels": 1,
        }

        second_report = import_bundle(
            make_bundle(),
            repository,
            DEFAULT_THRESHOLDS,
            store_name="Ignored replacement name",
            uuid_factory=SequentialUUIDs(1000),
        )
        second_state = repository.read_store_state("store-1")
        assert _all_ids(second_state) == first_ids
        assert second_state.store is not None
        assert second_state.store.name == "ShelfSense Market"
        assert "STORE_NAME_IGNORED_EXISTING_STORE" in categories(second_report)

        rollback_bundle = make_bundle()
        rollback_bundle.store.store_id = "store-rollback"
        failing_repository = FailingSqlImportRepository(engine)
        with pytest.raises(ImportAborted) as caught:
            import_bundle(
                rollback_bundle,
                failing_repository,
                DEFAULT_THRESHOLDS,
                store_name="Must Roll Back",
                uuid_factory=SequentialUUIDs(2000),
            )
        assert caught.value.category == "WRITE_TRANSACTION_FAILED"
        assert failing_repository.read_store_state("store-rollback").store is None
        assert _table_counts(engine) == {
            "stores": 1,
            "navigation_nodes": 2,
            "aisles": 1,
            "products": 1,
            "navigation_edges": 1,
            "shelf_blocks": 1,
            "shelf_levels": 4,
            "product_placements": 1,
            "product_placement_levels": 1,
        }
    finally:
        engine.dispose()


def test_postgres_level_order_reorder_uses_positive_noncolliding_staging() -> None:
    engine = _integration_engine()
    repository = SqlImportRepository(engine)
    bundle = _bundle_for_store("store-level-reorder")
    try:
        import_bundle(
            bundle,
            repository,
            DEFAULT_THRESHOLDS,
            store_name="Level Reorder Store",
            uuid_factory=SequentialUUIDs(3000),
        )
        before = _swap_a_and_b_orders(repository, engine, bundle.store.store_id)
        plan = preflight_bundle(
            bundle,
            repository,
            DEFAULT_THRESHOLDS,
            uuid_factory=SequentialUUIDs(3100),
        )
        staged_values: list[int] = []

        assert before == {"A": 2, "B": 1, "C": 3, "D": 4}
        assert len(plan.level_orders_to_stage) == 2
        assert set(plan.level_orders_to_stage.values()) == {5, 6}
        listener = _capture_staged_level_orders(staged_values)
        event.listen(engine, "after_cursor_execute", listener)
        try:
            apply_preflighted_plan(plan, repository)
        finally:
            event.remove(engine, "after_cursor_execute", listener)

        assert set(staged_values) == set(plan.level_orders_to_stage.values())
        assert _level_orders(repository, bundle.store.store_id) == {
            "A": 1,
            "B": 2,
            "C": 3,
            "D": 4,
        }
    finally:
        engine.dispose()


def test_postgres_failure_after_level_staging_restores_original_orders() -> None:
    engine = _integration_engine()
    repository = SqlImportRepository(engine)
    bundle = _bundle_for_store("store-level-rollback")
    try:
        import_bundle(
            bundle,
            repository,
            DEFAULT_THRESHOLDS,
            store_name="Level Rollback Store",
            uuid_factory=SequentialUUIDs(4000),
        )
        before = _swap_a_and_b_orders(repository, engine, bundle.store.store_id)
        plan = preflight_bundle(
            bundle,
            repository,
            DEFAULT_THRESHOLDS,
            uuid_factory=SequentialUUIDs(4100),
        )
        staged_values: list[int] = []
        capture_listener = _capture_staged_level_orders(staged_values)
        event.listen(engine, "after_cursor_execute", capture_listener)
        event.listen(engine, "before_cursor_execute", _fail_before_final_level_write)
        try:
            with pytest.raises(ImportAborted) as caught:
                apply_preflighted_plan(plan, repository)
        finally:
            event.remove(engine, "after_cursor_execute", capture_listener)
            event.remove(
                engine, "before_cursor_execute", _fail_before_final_level_write
            )

        assert caught.value.category == "WRITE_TRANSACTION_FAILED"
        assert set(staged_values) == set(plan.level_orders_to_stage.values())
        assert _level_orders(repository, bundle.store.store_id) == before
        assert not set(before.values()) & set(plan.level_orders_to_stage.values())
    finally:
        engine.dispose()


def _integration_engine():
    database_url = os.getenv(DATABASE_URL_ENV)
    if not database_url:
        pytest.skip(f"set {DATABASE_URL_ENV} to run PostgreSQL integration coverage")
    database_name = make_url(database_url).database or ""
    if not database_name.startswith(SAFE_DATABASE_PREFIX):
        pytest.fail(
            f"integration database name must start with {SAFE_DATABASE_PREFIX!r}"
        )
    return create_engine(database_url)


def _bundle_for_store(store_external_id: str):
    bundle = make_bundle()
    bundle.store.store_id = store_external_id
    return bundle


def _swap_a_and_b_orders(repository, engine, store_external_id: str) -> dict[str, int]:
    state = repository.read_store_state(store_external_id)
    shelf_id = state.shelves["shelf-1"].id
    levels = {
        code: level
        for (current_shelf_id, code), level in state.levels.items()
        if current_shelf_id == shelf_id
    }
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE shelf_levels SET level_order = 10 WHERE id = :id"),
            {"id": levels["A"].id},
        )
        connection.execute(
            text("UPDATE shelf_levels SET level_order = 1 WHERE id = :id"),
            {"id": levels["B"].id},
        )
        connection.execute(
            text("UPDATE shelf_levels SET level_order = 2 WHERE id = :id"),
            {"id": levels["A"].id},
        )
    return _level_orders(repository, store_external_id)


def _level_orders(repository, store_external_id: str) -> dict[str, int]:
    state = repository.read_store_state(store_external_id)
    shelf_id = state.shelves["shelf-1"].id
    return {
        code: level.level_order
        for (current_shelf_id, code), level in state.levels.items()
        if current_shelf_id == shelf_id
    }


def _capture_staged_level_orders(target: list[int]):
    def listener(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith("UPDATE shelf_levels SET level_order ="):
            target.append(parameters["value"])

    return listener


def _fail_before_final_level_write(
    connection, cursor, statement, parameters, context, executemany
):
    if statement.startswith("INSERT INTO shelf_levels"):
        raise RuntimeError("injected failure after level-order staging")


def _all_ids(state) -> dict[str, set]:
    return {
        "stores": {state.store.id} if state.store else set(),
        "navigation_nodes": {row.id for row in state.nodes.values()},
        "aisles": {row.id for row in state.aisles.values()},
        "products": {row.id for row in state.products.values()},
        "navigation_edges": {row.id for row in state.edges.values()},
        "shelf_blocks": {row.id for row in state.shelves.values()},
        "shelf_levels": {row.id for row in state.levels.values()},
        "product_placements": {row.id for row in state.placements.values()},
    }


def _table_counts(engine) -> dict[str, int]:
    tables = (
        "stores",
        "navigation_nodes",
        "aisles",
        "products",
        "navigation_edges",
        "shelf_blocks",
        "shelf_levels",
        "product_placements",
        "product_placement_levels",
    )
    with engine.connect() as connection:
        return {
            table: connection.execute(
                text(f"SELECT COUNT(*) FROM {table}")
            ).scalar_one()
            for table in tables
        }
