"""Importer projection, synchronization, thresholds, and atomicity tests."""

from copy import deepcopy
from dataclasses import replace
from uuid import UUID

import pytest
from importer_helpers import (
    DEFAULT_THRESHOLDS,
    MemoryRepository,
    SequentialUUIDs,
    bundle_data,
    categories,
    make_bundle,
)

from shelfsense.db.importer.report import ImportAborted
from shelfsense.db.importer.service import import_bundle, preflight_bundle
from shelfsense.db.importer.state import LevelRecord


def test_repeated_import_is_idempotent_and_preserves_internal_uuids() -> None:
    repository = MemoryRepository()
    first = import_bundle(
        make_bundle(),
        repository,
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )
    first_state = deepcopy(repository.state)

    second = import_bundle(
        make_bundle(),
        repository,
        DEFAULT_THRESHOLDS,
        uuid_factory=SequentialUUIDs(1000),
    )

    assert repository.state == first_state
    assert first.tables["stores"].inserted == 1
    assert second.tables["stores"].unchanged == 1
    assert second.tables["navigation_nodes"].unchanged == 2
    assert second.tables["product_placements"].unchanged == 1
    assert second.tables["product_placement_levels"].unchanged == 1


def test_store_and_shelf_operational_fields_are_preserved_on_reimport() -> None:
    repository = MemoryRepository()
    import_bundle(
        make_bundle(),
        repository,
        DEFAULT_THRESHOLDS,
        store_name="Original Name",
        uuid_factory=SequentialUUIDs(),
    )
    repository.state.store = replace(repository.state.store, is_active=False)
    shelf = repository.state.shelves["shelf-1"]
    repository.state.shelves["shelf-1"] = replace(shelf, is_active=False)

    import_bundle(
        make_bundle(),
        repository,
        DEFAULT_THRESHOLDS,
        store_name="Ignored Name",
        uuid_factory=SequentialUUIDs(1000),
    )

    assert repository.state.store.name == "Original Name"
    assert repository.state.store.is_active is False
    assert repository.state.shelves["shelf-1"].is_active is False


def test_missing_shelf_is_deactivated_and_reappearance_does_not_reactivate() -> None:
    full_data = bundle_data()
    _add_shelf(full_data, "shelf-2")
    repository = MemoryRepository()
    import_bundle(
        make_bundle(full_data),
        repository,
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )

    reduced = deepcopy(full_data)
    reduced["store"]["shelf_blocks"] = reduced["store"]["shelf_blocks"][:1]
    report = import_bundle(
        make_bundle(reduced),
        repository,
        DEFAULT_THRESHOLDS,
        uuid_factory=SequentialUUIDs(1000),
    )
    assert report.tables["shelf_blocks"].deactivated == 1
    assert repository.state.shelves["shelf-2"].is_active is False

    import_bundle(
        make_bundle(full_data),
        repository,
        DEFAULT_THRESHOLDS,
        uuid_factory=SequentialUUIDs(2000),
    )
    assert repository.state.shelves["shelf-2"].is_active is False


def test_missing_shelf_threshold_aborts_and_preserves_database_state() -> None:
    full_data = bundle_data()
    for number in range(2, 6):
        _add_shelf(full_data, f"shelf-{number}")
    repository = MemoryRepository()
    import_bundle(
        make_bundle(full_data),
        repository,
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )
    before = deepcopy(repository.state)
    reduced = deepcopy(full_data)
    reduced["store"]["shelf_blocks"] = reduced["store"]["shelf_blocks"][:1]

    with pytest.raises(ImportAborted) as caught:
        import_bundle(
            make_bundle(reduced),
            repository,
            DEFAULT_THRESHOLDS,
            uuid_factory=SequentialUUIDs(1000),
        )

    assert caught.value.category == "MISSING_SHELF_THRESHOLD_EXCEEDED"
    assert repository.state == before
    assert repository.apply_calls == 1


def test_missing_edge_threshold_aborts() -> None:
    full_data = bundle_data()
    for number in range(2, 5):
        _add_node_and_edge(full_data, number)
    repository = MemoryRepository()
    import_bundle(
        make_bundle(full_data),
        repository,
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )
    before = deepcopy(repository.state)
    reduced = deepcopy(full_data)
    reduced["store"]["edges"] = reduced["store"]["edges"][:1]

    with pytest.raises(ImportAborted) as caught:
        import_bundle(
            make_bundle(reduced),
            repository,
            DEFAULT_THRESHOLDS,
            uuid_factory=SequentialUUIDs(1000),
        )

    assert caught.value.category == "MISSING_EDGE_THRESHOLD_EXCEEDED"
    assert repository.state == before


def test_missing_edge_under_threshold_is_hard_deleted() -> None:
    full_data = bundle_data()
    _add_node_and_edge(full_data, 2)
    repository = MemoryRepository()
    import_bundle(
        make_bundle(full_data),
        repository,
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )
    reduced = deepcopy(full_data)
    reduced["store"]["edges"] = reduced["store"]["edges"][:1]

    report = import_bundle(
        make_bundle(reduced),
        repository,
        DEFAULT_THRESHOLDS,
        uuid_factory=SequentialUUIDs(1000),
    )

    assert len(repository.state.edges) == 1
    assert report.tables["navigation_edges"].deleted == 1


def test_edge_direction_change_is_correlated_for_reporting() -> None:
    repository = MemoryRepository()
    import_bundle(
        make_bundle(),
        repository,
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )
    directed = bundle_data()
    directed["store"]["edges"][0]["is_bidirectional"] = False

    report = import_bundle(
        make_bundle(directed),
        repository,
        DEFAULT_THRESHOLDS,
        uuid_factory=SequentialUUIDs(1000),
    )

    assert "EDGE_TOPOLOGY_OR_DIRECTION_CHANGED" in categories(report)
    assert len(repository.state.edges) == 1
    assert next(iter(repository.state.edges.values())).is_bidirectional is False


def test_missing_navigation_node_is_retained_and_reported() -> None:
    initial = bundle_data()
    initial["store"]["nodes"].append(
        {"id": "old-node", "x": "9", "y": "9", "kind": "kavsak"}
    )
    repository = MemoryRepository()
    import_bundle(
        make_bundle(initial),
        repository,
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )

    report = import_bundle(
        make_bundle(),
        repository,
        DEFAULT_THRESHOLDS,
        uuid_factory=SequentialUUIDs(1000),
    )

    assert "old-node" in repository.state.nodes
    assert "MISSING_NAVIGATION_NODE" in categories(report)


def test_aisle_number_swap_succeeds_using_projected_state() -> None:
    initial = bundle_data()
    initial["store"]["aisles"][0]["aisle_number"] = 2
    initial["store"]["aisles"].append(
        {"id": "aisle-2", "name": "Aisle 2", "aisle_number": 3}
    )
    repository = MemoryRepository()
    import_bundle(
        make_bundle(initial),
        repository,
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )
    swapped = deepcopy(initial)
    swapped["store"]["aisles"][0]["aisle_number"] = 3
    swapped["store"]["aisles"][1]["aisle_number"] = 2

    plan = preflight_bundle(
        make_bundle(swapped),
        repository,
        DEFAULT_THRESHOLDS,
        uuid_factory=SequentialUUIDs(1000),
    )
    assert len(plan.aisle_numbers_to_clear) == 2
    repository.apply_plan(plan)
    assert repository.state.aisles["aisle-1"].aisle_number == 3
    assert repository.state.aisles["aisle-2"].aisle_number == 2


def test_true_projected_aisle_number_duplicate_aborts() -> None:
    data = bundle_data()
    data["store"]["aisles"].append(
        {"id": "aisle-2", "name": "Aisle 2", "aisle_number": 1}
    )

    with pytest.raises(ImportAborted) as caught:
        preflight_bundle(
            make_bundle(data),
            MemoryRepository(),
            DEFAULT_THRESHOLDS,
            store_name="Test Store",
        )

    assert caught.value.category == "AISLE_NUMBER_PROJECTED_CONFLICT"


def test_missing_aisle_is_retained_and_reported() -> None:
    initial = bundle_data()
    initial["store"]["aisles"].append(
        {"id": "old-aisle", "name": "Old", "aisle_number": 9}
    )
    repository = MemoryRepository()
    import_bundle(
        make_bundle(initial),
        repository,
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )

    report = import_bundle(
        make_bundle(),
        repository,
        DEFAULT_THRESHOLDS,
        uuid_factory=SequentialUUIDs(1000),
    )
    assert "old-aisle" in repository.state.aisles
    assert "MISSING_AISLE" in categories(report)


def test_missing_product_is_retained_and_reported() -> None:
    initial = bundle_data()
    initial["products"]["products"].append(
        {"id": 2, "name": "Old", "category": "old", "unit": "adet"}
    )
    repository = MemoryRepository()
    import_bundle(
        make_bundle(initial),
        repository,
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )

    report = import_bundle(
        make_bundle(),
        repository,
        DEFAULT_THRESHOLDS,
        uuid_factory=SequentialUUIDs(1000),
    )
    assert "2" in repository.state.products
    assert "MISSING_PRODUCT_REMOVED_FROM_CATALOG" in categories(report)


def test_missing_placement_threshold_aborts() -> None:
    initial = bundle_data()
    for number in range(2, 8):
        _add_shelf(initial, f"shelf-{number}")
        initial["store"]["placements"].append(
            {
                "product_id": 1,
                "shelf_block_id": f"shelf-{number}",
                "slot": "A",
            }
        )
    repository = MemoryRepository()
    import_bundle(
        make_bundle(initial),
        repository,
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )
    before = deepcopy(repository.state)
    reduced = deepcopy(initial)
    reduced["store"]["placements"] = reduced["store"]["placements"][:1]

    with pytest.raises(ImportAborted) as caught:
        import_bundle(
            make_bundle(reduced),
            repository,
            DEFAULT_THRESHOLDS,
            uuid_factory=SequentialUUIDs(1000),
        )

    assert caught.value.category == "MISSING_PLACEMENT_THRESHOLD_EXCEEDED"
    assert repository.state == before


def test_missing_placement_is_deleted_with_bridge_and_warning() -> None:
    repository = MemoryRepository()
    import_bundle(
        make_bundle(),
        repository,
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )
    reduced = bundle_data()
    reduced["store"]["placements"] = []

    report = import_bundle(
        make_bundle(reduced),
        repository,
        DEFAULT_THRESHOLDS,
        uuid_factory=SequentialUUIDs(1000),
    )

    assert repository.state.placements == {}
    assert repository.state.placement_levels == set()
    assert report.tables["product_placements"].deleted == 1
    assert "PRODUCTS_WITH_NO_PLACEMENT_AFTER_IMPORT" in categories(report)


def test_zero_placement_shelf_warns_and_retains_existing_levels() -> None:
    repository = MemoryRepository()
    import_bundle(
        make_bundle(),
        repository,
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )
    level_ids = {level.id for level in repository.state.levels.values()}
    reduced = bundle_data()
    reduced["store"]["placements"] = []

    report = import_bundle(
        make_bundle(reduced),
        repository,
        DEFAULT_THRESHOLDS,
        uuid_factory=SequentialUUIDs(1000),
    )

    assert "SHELF_LEVELS_UNRESOLVED" in categories(report)
    assert level_ids <= {level.id for level in repository.state.levels.values()}


def test_valid_explicit_levels_are_used() -> None:
    data = bundle_data()
    data["store"]["shelf_blocks"][0]["levels"] = _abcd_levels()
    plan = preflight_bundle(
        make_bundle(data),
        MemoryRepository(),
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )
    assert [(level.code, level.level_order) for level in plan.levels] == [
        ("A", 1),
        ("B", 2),
        ("C", 3),
        ("D", 4),
    ]


def test_explicit_levels_reject_nonexistent_placement_level() -> None:
    data = bundle_data()
    data["store"]["shelf_blocks"][0]["levels"] = _abcd_levels()
    data["store"]["placements"][0]["slot"] = "ust"

    with pytest.raises(ImportAborted) as caught:
        preflight_bundle(
            make_bundle(data),
            MemoryRepository(),
            DEFAULT_THRESHOLDS,
            store_name="Test Store",
        )

    assert caught.value.category == "UNSUPPORTED_EXPLICIT_LEVEL_STRUCTURE"


def test_unsupported_partial_explicit_structure_aborts() -> None:
    data = bundle_data()
    data["store"]["shelf_blocks"][0]["levels"] = [{"code": "A", "order": 1}]

    with pytest.raises(ImportAborted) as caught:
        preflight_bundle(
            make_bundle(data),
            MemoryRepository(),
            DEFAULT_THRESHOLDS,
            store_name="Test Store",
        )

    assert caught.value.category == "UNSUPPORTED_EXPLICIT_LEVEL_STRUCTURE"


def test_mixed_template_vocabulary_aborts() -> None:
    data = bundle_data()
    data["products"]["products"].append(
        {"id": 2, "name": "Drink", "category": "drink", "unit": "adet"}
    )
    data["store"]["placements"].append(
        {"product_id": 2, "shelf_block_id": "shelf-1", "slot": "ust"}
    )

    with pytest.raises(ImportAborted) as caught:
        preflight_bundle(
            make_bundle(data),
            MemoryRepository(),
            DEFAULT_THRESHOLDS,
            store_name="Test Store",
        )

    assert caught.value.category == "LEVEL_TEMPLATE_DETECTION_FAILED"


def test_bridge_rows_are_synchronized_to_exact_desired_set() -> None:
    repository = MemoryRepository()
    import_bundle(
        make_bundle(),
        repository,
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )
    changed = bundle_data()
    changed["store"]["placements"][0]["slot"] = "B,D"

    report = import_bundle(
        make_bundle(changed),
        repository,
        DEFAULT_THRESHOLDS,
        uuid_factory=SequentialUUIDs(1000),
    )
    level_codes = {level.id: level.code for level in repository.state.levels.values()}
    linked_codes = {
        level_codes[level_id] for _, level_id in repository.state.placement_levels
    }
    assert linked_codes == {"B", "D"}
    assert report.tables["product_placement_levels"].deleted == 1
    assert report.tables["product_placement_levels"].inserted == 2


def test_desired_bridge_rows_always_use_levels_from_the_placement_shelf() -> None:
    data = bundle_data()
    _add_shelf(data, "shelf-2")
    data["store"]["placements"].append(
        {"product_id": 1, "shelf_block_id": "shelf-2", "slot": "D"}
    )
    plan = preflight_bundle(
        make_bundle(data),
        MemoryRepository(),
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )
    placements = {placement.id: placement for placement in plan.placements}
    levels = {level.id: level for level in plan.levels}
    for placement_id, level_id, shelf_id in plan.desired_placement_levels:
        assert placements[placement_id].shelf_block_id == shelf_id
        assert levels[level_id].shelf_block_id == shelf_id


def test_abcd_to_beverage_with_retained_levels_aborts_projected_conflict() -> None:
    repository = MemoryRepository()
    import_bundle(
        make_bundle(),
        repository,
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )
    before = deepcopy(repository.state)
    beverage = bundle_data()
    beverage["store"]["placements"][0]["slot"] = "ust"

    with pytest.raises(ImportAborted) as caught:
        import_bundle(
            make_bundle(beverage),
            repository,
            DEFAULT_THRESHOLDS,
            uuid_factory=SequentialUUIDs(1000),
        )

    assert caught.value.category == "SHELF_LEVEL_PROJECTED_CONFLICT"
    assert repository.state == before


def test_nonconflicting_stale_level_is_retained_and_reported() -> None:
    repository = MemoryRepository()
    import_bundle(
        make_bundle(),
        repository,
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )
    shelf = repository.state.shelves["shelf-1"]
    stale = LevelRecord(
        UUID(int=9000),
        repository.state.store.id,
        shelf.id,
        "Z",
        99,
        "legacy",
    )
    repository.state.levels[(shelf.id, stale.code)] = stale

    report = import_bundle(
        make_bundle(),
        repository,
        DEFAULT_THRESHOLDS,
        uuid_factory=SequentialUUIDs(1000),
    )

    assert repository.state.levels[(shelf.id, "Z")] == stale
    assert "MISSING_SHELF_LEVEL" in categories(report)


def test_write_phase_failure_rolls_back_all_prior_writes() -> None:
    repository = MemoryRepository()
    repository.fail_during_apply = True

    with pytest.raises(ImportAborted) as caught:
        import_bundle(
            make_bundle(),
            repository,
            DEFAULT_THRESHOLDS,
            store_name="Test Store",
            uuid_factory=SequentialUUIDs(),
        )

    assert caught.value.category == "WRITE_TRANSACTION_FAILED"
    assert repository.observed_partial_write is True
    assert repository.state == MemoryRepository().state


def _add_shelf(data: dict, external_id: str) -> None:
    number = int(external_id.rsplit("-", 1)[-1])
    data["store"]["shelf_blocks"].append(
        {
            "id": external_id,
            "aisle_id": "aisle-1",
            "access_node_id": "node-shelf",
            "x": str(number + 1),
            "y": "0",
            "w": "1",
            "h": "1",
            "facing": "+x",
            "side": f"side {number}",
        }
    )


def _add_node_and_edge(data: dict, number: int) -> None:
    node_id = f"node-{number}"
    data["store"]["nodes"].append(
        {"id": node_id, "x": str(number + 2), "y": "0", "kind": "kavsak"}
    )
    data["store"]["edges"].append(
        {"from_id": "node-entrance", "to_id": node_id, "weight": str(number + 2)}
    )


def _abcd_levels() -> list[dict[str, object]]:
    return [
        {"code": "A", "order": 1},
        {"code": "B", "order": 2},
        {"code": "C", "order": 3},
        {"code": "D", "order": 4},
    ]
