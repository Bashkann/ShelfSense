"""Importer global preflight, source ownership, and normalization tests."""

import json
from copy import deepcopy
from decimal import Decimal

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
from shelfsense.db.importer.service import (
    import_bundle,
    preflight_bundle,
    preflight_from_files,
)
from shelfsense.db.importer.source import SourceBundle


def test_new_store_requires_name_without_database_writes() -> None:
    repository = MemoryRepository()

    with pytest.raises(ImportAborted) as caught:
        preflight_bundle(
            make_bundle(),
            repository,
            DEFAULT_THRESHOLDS,
            uuid_factory=SequentialUUIDs(),
        )

    assert caught.value.category == "STORE_NAME_REQUIRED"
    assert repository.read_calls == 1
    assert repository.apply_calls == 0
    assert repository.state.store is None


def test_new_store_name_is_used_only_for_insert() -> None:
    repository = MemoryRepository()

    report = import_bundle(
        make_bundle(),
        repository,
        DEFAULT_THRESHOLDS,
        store_name="ShelfSense Market",
        uuid_factory=SequentialUUIDs(),
    )

    assert report.preflight_status == "PASS"
    assert repository.state.store.name == "ShelfSense Market"


def test_existing_store_name_is_preserved() -> None:
    repository = MemoryRepository()
    import_bundle(
        make_bundle(),
        repository,
        DEFAULT_THRESHOLDS,
        store_name="ShelfSense - Kadıköy Şubesi",
        uuid_factory=SequentialUUIDs(),
    )

    report = import_bundle(
        make_bundle(),
        repository,
        DEFAULT_THRESHOLDS,
        uuid_factory=SequentialUUIDs(100),
    )

    assert repository.state.store.name == "ShelfSense - Kadıköy Şubesi"
    assert "STORE_NAME_IGNORED_EXISTING_STORE" not in categories(report)


def test_provided_name_for_existing_store_is_ignored_and_reported() -> None:
    repository = MemoryRepository()
    import_bundle(
        make_bundle(),
        repository,
        DEFAULT_THRESHOLDS,
        store_name="ShelfSense - Kadıköy Şubesi",
        uuid_factory=SequentialUUIDs(),
    )

    report = import_bundle(
        make_bundle(),
        repository,
        DEFAULT_THRESHOLDS,
        store_name="ShelfSense Market",
        uuid_factory=SequentialUUIDs(100),
    )

    assert repository.state.store.name == "ShelfSense - Kadıköy Şubesi"
    entry = next(
        item
        for item in report.entries
        if item.category == "STORE_NAME_IGNORED_EXISTING_STORE"
    )
    assert entry.details == {
        "store_external_id": "store-1",
        "provided_store_name": "ShelfSense Market",
        "preserved_store_name": "ShelfSense - Kadıköy Şubesi",
    }


def test_legacy_edge_defaults_true_reports_and_canonicalizes() -> None:
    plan = preflight_bundle(
        make_bundle(),
        MemoryRepository(),
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )

    edge = plan.edges[0]
    assert edge.is_bidirectional is True
    assert edge.from_node_id < edge.to_node_id
    assert "LEGACY_EDGE_DIRECTIONALITY_DEFAULTED" in categories(plan.report)


def test_explicit_directed_edge_preserves_source_direction() -> None:
    data = bundle_data()
    data["store"]["edges"][0]["is_bidirectional"] = False
    plan = preflight_bundle(
        make_bundle(data),
        MemoryRepository(),
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )
    nodes = {node.external_id: node.id for node in plan.nodes}
    edge = plan.edges[0]

    assert edge.is_bidirectional is False
    assert edge.from_node_id == nodes["node-shelf"]
    assert edge.to_node_id == nodes["node-entrance"]
    assert "LEGACY_EDGE_DIRECTIONALITY_DEFAULTED" not in categories(plan.report)


def test_explicit_bidirectional_edge_canonicalizes_without_fallback_report() -> None:
    data = bundle_data()
    data["store"]["edges"][0]["is_bidirectional"] = True
    plan = preflight_bundle(
        make_bundle(data),
        MemoryRepository(),
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )

    assert plan.edges[0].is_bidirectional is True
    assert plan.edges[0].from_node_id < plan.edges[0].to_node_id
    assert "LEGACY_EDGE_DIRECTIONALITY_DEFAULTED" not in categories(plan.report)


def test_side_maps_directly_to_side_description() -> None:
    data = bundle_data()
    data["store"]["shelf_blocks"][0]["side"] = "east face"
    plan = preflight_bundle(
        make_bundle(data),
        MemoryRepository(),
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )
    assert plan.shelves[0].side_description == "east face"


def test_missing_side_fails_as_source_structure_error(tmp_path) -> None:
    data = bundle_data()
    del data["store"]["shelf_blocks"][0]["side"]
    store_path = tmp_path / "store.json"
    product_path = tmp_path / "products.json"
    store_path.write_text(json.dumps(data["store"]), encoding="utf-8")
    product_path.write_text(json.dumps(data["products"]), encoding="utf-8")

    with pytest.raises(ImportAborted) as caught:
        preflight_from_files(
            store_path,
            product_path,
            store_name="Test Store",
            repository=MemoryRepository(),
        )

    assert caught.value.category == "INVALID_SOURCE_STRUCTURE"


def test_missing_store_source_never_falls_back_to_mock(tmp_path) -> None:
    missing_store_path = tmp_path / "data" / "store.json"
    product_path = tmp_path / "products.json"
    product_path.write_text(json.dumps(bundle_data()["products"]), encoding="utf-8")
    repository = MemoryRepository()

    with pytest.raises(ImportAborted) as caught:
        preflight_from_files(
            missing_store_path,
            product_path,
            store_name="Test Store",
            repository=repository,
        )

    assert caught.value.category == "REAL_STORE_SOURCE_NOT_FOUND"
    assert repository.read_calls == 0
    assert repository.apply_calls == 0


def test_weight_maps_to_three_decimal_distance_without_float_artifacts() -> None:
    data = bundle_data()
    data["store"]["edges"][0]["weight"] = "1.2345"
    plan = preflight_bundle(
        make_bundle(data),
        MemoryRepository(),
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )
    assert plan.edges[0].distance_m == Decimal("1.235")


def test_raf_onu_is_the_only_node_type_mapping() -> None:
    plan = preflight_bundle(
        make_bundle(),
        MemoryRepository(),
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )
    assert {node.node_type for node in plan.nodes} == {"giris", "raf_onu"}


def test_zero_entrance_aborts_before_database_read() -> None:
    data = bundle_data()
    data["store"]["nodes"][0]["kind"] = "kavsak"
    repository = MemoryRepository()

    with pytest.raises(ImportAborted) as caught:
        preflight_bundle(
            make_bundle(data),
            repository,
            DEFAULT_THRESHOLDS,
            store_name="Test Store",
        )

    assert caught.value.category == "ZERO_ENTRANCE_NODES"
    assert repository.read_calls == 0
    assert repository.apply_calls == 0


@pytest.mark.parametrize(
    ("mutation", "expected_collection"),
    [
        (
            lambda data: data["store"]["edges"][0].update(from_id="missing"),
            "store.json.nodes",
        ),
        (
            lambda data: data["store"]["shelf_blocks"][0].update(
                access_node_id="missing"
            ),
            "store.json.nodes",
        ),
        (
            lambda data: data["store"]["shelf_blocks"][0].update(aisle_id="missing"),
            "store.json.aisles",
        ),
        (
            lambda data: data["store"]["placements"][0].update(product_id=999),
            "product_mapping.products",
        ),
    ],
)
def test_invalid_source_references_abort_without_database_read(
    mutation, expected_collection
) -> None:
    data = bundle_data()
    mutation(data)
    repository = MemoryRepository()

    with pytest.raises(ImportAborted) as caught:
        preflight_bundle(
            make_bundle(data),
            repository,
            DEFAULT_THRESHOLDS,
            store_name="Test Store",
        )

    assert caught.value.category == "INVALID_SOURCE_REFERENCE"
    assert (
        caught.value.report.entries[-1].details["expected_source_collection"]
        == expected_collection
    )
    assert repository.read_calls == 0
    assert repository.apply_calls == 0


def test_mapping_shelf_and_slot_do_not_affect_relational_projection() -> None:
    first_data = bundle_data()
    second_data = deepcopy(first_data)
    second_data["products"]["products"][0]["shelf"] = "different"
    second_data["products"]["products"][0]["slot"] = "kasa"
    first = preflight_bundle(
        make_bundle(first_data),
        MemoryRepository(),
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )
    second = preflight_bundle(
        make_bundle(second_data),
        MemoryRepository(),
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )

    assert first.placements == second.placements
    assert first.levels == second.levels
    assert first.desired_placement_levels == second.desired_placement_levels


def test_raw_slot_is_persisted_while_parsed_atoms_drive_level_links() -> None:
    data = bundle_data()
    data["store"]["placements"][0]["slot"] = " B , d "
    plan = preflight_bundle(
        make_bundle(data),
        MemoryRepository(),
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )
    level_codes_by_id = {level.id: level.code for level in plan.levels}

    assert plan.placements[0].slot_code == " B , d "
    assert {
        level_codes_by_id[level_id] for _, level_id, _ in plan.desired_placement_levels
    } == {"B", "D"}


def test_product_name_validation_does_not_trim_persisted_source_value() -> None:
    data = bundle_data()
    data["products"]["products"][0]["name"] = "  sut sek  "
    plan = preflight_bundle(
        make_bundle(data),
        MemoryRepository(),
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )

    assert plan.products[0].name == "  sut sek  "


def test_product_external_ids_are_persisted_as_text() -> None:
    plan = preflight_bundle(
        make_bundle(),
        MemoryRepository(),
        DEFAULT_THRESHOLDS,
        store_name="Test Store",
        uuid_factory=SequentialUUIDs(),
    )

    assert plan.products[0].external_id == "1"


def test_explicit_null_directionality_is_not_treated_as_legacy_absence() -> None:
    data = bundle_data()
    data["store"]["edges"][0]["is_bidirectional"] = None

    with pytest.raises(ImportAborted) as caught:
        preflight_bundle(
            make_bundle(data),
            MemoryRepository(),
            DEFAULT_THRESHOLDS,
            store_name="Test Store",
        )

    assert caught.value.category == "INVALID_SOURCE_STRUCTURE"


@pytest.mark.parametrize("value", ["true", "false", 1, 0])
def test_explicit_directionality_requires_a_json_boolean(tmp_path, value) -> None:
    data = bundle_data()
    data["store"]["edges"][0]["is_bidirectional"] = value
    store_path = tmp_path / "store.json"
    product_path = tmp_path / "products.json"
    store_path.write_text(json.dumps(data["store"]), encoding="utf-8")
    product_path.write_text(json.dumps(data["products"]), encoding="utf-8")

    with pytest.raises(ImportAborted) as caught:
        preflight_from_files(
            store_path,
            product_path,
            store_name="Test Store",
            repository=MemoryRepository(),
        )

    assert caught.value.category == "INVALID_SOURCE_STRUCTURE"


def test_self_referencing_edge_fails_during_preflight() -> None:
    data = bundle_data()
    data["store"]["edges"][0]["to_id"] = "node-shelf"

    with pytest.raises(ImportAborted) as caught:
        preflight_bundle(
            make_bundle(data),
            MemoryRepository(),
            DEFAULT_THRESHOLDS,
            store_name="Test Store",
        )

    assert caught.value.category == "INVALID_SOURCE_VALUE"


def test_source_bundle_accepts_non_authoritative_debug_fields() -> None:
    data = bundle_data()
    data["store"]["placements"][0].update(product_name="debug", side="debug")
    bundle = SourceBundle.model_validate(
        {"store": data["store"], "products": data["products"]}
    )
    assert bundle.store.placements[0].product_external_id == "1"
