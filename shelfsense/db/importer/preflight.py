"""Global read-only preflight and projected-state planning."""

from collections import Counter, defaultdict
from collections.abc import Callable, Iterable
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Protocol, TypeVar
from uuid import UUID, uuid4

from shelfsense.config import Settings
from shelfsense.db.importer.levels import (
    LevelDefinition,
    LevelResolutionError,
    detect_template,
    validate_explicit_levels,
)
from shelfsense.db.importer.report import ImportReport, ThresholdResult, abort
from shelfsense.db.importer.slots import ParsedSlot, SlotSyntaxError, parse_slot
from shelfsense.db.importer.source import SourceBundle
from shelfsense.db.importer.state import (
    AisleRecord,
    DatabaseState,
    EdgeRecord,
    ImportPlan,
    ImportRepository,
    ImportThresholds,
    LevelRecord,
    NodeRecord,
    PlacementRecord,
    ProductRecord,
    ShelfRecord,
    StoreRecord,
)


class HasId(Protocol):
    id: UUID


T = TypeVar("T", bound=HasId)
THREE_PLACES = Decimal("0.001")
MAX_NUMERIC_8_3 = Decimal("99999.999")
ALLOWED_NODE_TYPES = {"giris", "cikis", "kavsak", "raf_onu", "kasa"}


def thresholds_from_settings(settings: Settings) -> ImportThresholds:
    """Build immutable importer thresholds through the application settings."""

    return ImportThresholds(
        max_missing_shelves=settings.import_max_missing_shelves,
        max_missing_shelf_ratio=settings.import_max_missing_shelf_ratio,
        max_missing_edges=settings.import_max_missing_edges,
        max_missing_edge_ratio=settings.import_max_missing_edge_ratio,
        max_missing_placements=settings.import_max_missing_placements,
        max_missing_placement_ratio=settings.import_max_missing_placement_ratio,
    )


def build_import_plan(
    bundle: SourceBundle,
    repository: ImportRepository,
    thresholds: ImportThresholds,
    report: ImportReport,
    *,
    store_name: str | None,
    uuid_factory: Callable[[], UUID] = uuid4,
) -> ImportPlan:
    """Run the complete global preflight gate without database writes."""

    source = bundle.store
    report.store_external_id = _required_text(report, source.store_id, "store.store_id")
    _validate_unique_source_identities(bundle, report)
    _validate_source_references(bundle, report)

    parsed_slots = _parse_all_slots(bundle, report)
    resolved_definitions = _resolve_all_levels(bundle, parsed_slots, report)
    normalized_node_types = _normalize_node_types(bundle, report)
    _validate_legacy_entrance(bundle, normalized_node_types, report)
    if sum(node_type == "giris" for node_type in normalized_node_types.values()) == 0:
        abort(report, "ZERO_ENTRANCE_NODES", store=source.store_id)

    state = repository.read_store_state(source.store_id)
    store = _resolve_store(state, source.store_id, store_name, report, uuid_factory)
    store_id = store.id

    insert_ids: dict[str, set[UUID]] = defaultdict(set)
    update_ids: dict[str, set[UUID]] = defaultdict(set)
    if state.store is None:
        report.stats("stores").inserted = 1
    else:
        report.stats("stores").unchanged = 1

    nodes = _project_nodes(
        bundle,
        state,
        store_id,
        normalized_node_types,
        report,
        insert_ids,
        update_ids,
        uuid_factory,
    )
    aisles, aisle_numbers_to_clear = _project_aisles(
        bundle,
        state,
        store_id,
        report,
        insert_ids,
        update_ids,
        uuid_factory,
    )
    products = _project_products(
        bundle,
        state,
        store_id,
        report,
        insert_ids,
        update_ids,
        uuid_factory,
    )
    edges = _project_edges(
        bundle,
        state,
        store_id,
        nodes,
        report,
        insert_ids,
        update_ids,
        uuid_factory,
    )
    shelves = _project_shelves(
        bundle,
        state,
        store_id,
        nodes,
        aisles,
        report,
        insert_ids,
        update_ids,
        uuid_factory,
    )
    levels, level_orders_to_stage = _project_levels(
        bundle,
        state,
        store_id,
        shelves,
        resolved_definitions,
        report,
        insert_ids,
        update_ids,
        uuid_factory,
    )
    placements = _project_placements(
        bundle,
        state,
        store_id,
        products,
        shelves,
        parsed_slots,
        report,
        insert_ids,
        update_ids,
        uuid_factory,
    )

    missing_shelves = _missing_shelves(state, shelves)
    shelf_threshold = _threshold(
        baseline=sum(shelf.is_active for shelf in state.shelves.values()),
        affected=[shelf.external_id for shelf in missing_shelves if shelf.is_active],
        max_count=thresholds.max_missing_shelves,
        max_ratio=thresholds.max_missing_shelf_ratio,
    )
    report.thresholds["shelf_blocks"] = shelf_threshold
    _enforce_threshold(report, shelf_threshold, "MISSING_SHELF_THRESHOLD_EXCEEDED")
    shelf_ids_to_deactivate = {shelf.id for shelf in missing_shelves if shelf.is_active}
    shelf_stats = report.stats("shelf_blocks")
    shelf_stats.deactivated = len(shelf_ids_to_deactivate)
    shelf_stats.retained_missing = len(missing_shelves)

    desired_edge_keys = {(edge.from_node_id, edge.to_node_id) for edge in edges}
    missing_edges = [
        edge for key, edge in state.edges.items() if key not in desired_edge_keys
    ]
    edge_threshold = _threshold(
        baseline=len(state.edges),
        affected=[str(edge.id) for edge in missing_edges],
        max_count=thresholds.max_missing_edges,
        max_ratio=thresholds.max_missing_edge_ratio,
    )
    report.thresholds["navigation_edges"] = edge_threshold
    _enforce_threshold(report, edge_threshold, "MISSING_EDGE_THRESHOLD_EXCEEDED")
    edge_ids_to_delete = {edge.id for edge in missing_edges}
    report.stats("navigation_edges").deleted = len(edge_ids_to_delete)
    _report_edge_changes(state, edges, missing_edges, report)

    desired_placement_keys = {
        (placement.product_id, placement.shelf_block_id) for placement in placements
    }
    missing_placements = [
        placement
        for key, placement in state.placements.items()
        if key not in desired_placement_keys
    ]
    placement_threshold = _threshold(
        baseline=len(state.placements),
        affected=[str(placement.id) for placement in missing_placements],
        max_count=thresholds.max_missing_placements,
        max_ratio=thresholds.max_missing_placement_ratio,
    )
    report.thresholds["product_placements"] = placement_threshold
    _enforce_threshold(
        report, placement_threshold, "MISSING_PLACEMENT_THRESHOLD_EXCEEDED"
    )
    placement_ids_to_delete = {placement.id for placement in missing_placements}
    report.stats("product_placements").deleted = len(placement_ids_to_delete)
    _report_products_losing_placements(state, products, placements, report)

    desired_links = _desired_placement_levels(placements, levels, parsed_slots)
    desired_link_pairs = {
        (placement_id, level_id) for placement_id, level_id, _ in desired_links
    }
    incoming_placement_ids = {placement.id for placement in placements}
    stale_links = {
        link
        for link in state.placement_levels
        if link[0] in incoming_placement_ids and link not in desired_link_pairs
    }
    current_links = state.placement_levels
    new_links = {
        link for link in desired_links if (link[0], link[1]) not in current_links
    }
    bridge_stats = report.stats("product_placement_levels")
    bridge_stats.deleted = len(stale_links)
    bridge_stats.inserted = len(new_links)
    bridge_stats.unchanged = len(desired_links) - len(new_links)

    return ImportPlan(
        store=store,
        store_is_new=state.store is None,
        nodes=tuple(nodes.values()),
        aisles=tuple(aisles.values()),
        products=tuple(products.values()),
        edges=tuple(edges),
        shelves=tuple(shelves.values()),
        levels=tuple(levels.values()),
        placements=tuple(placements),
        desired_placement_levels=desired_links,
        insert_ids=dict(insert_ids),
        update_ids=dict(update_ids),
        aisle_numbers_to_clear=aisle_numbers_to_clear,
        level_orders_to_stage=level_orders_to_stage,
        edge_ids_to_delete=edge_ids_to_delete,
        shelf_ids_to_deactivate=shelf_ids_to_deactivate,
        placement_ids_to_delete=placement_ids_to_delete,
        placement_levels_to_delete=stale_links,
        placement_levels_to_insert=new_links,
        report=report,
    )


def _validate_unique_source_identities(
    bundle: SourceBundle, report: ImportReport
) -> None:
    source = bundle.store
    collections: list[tuple[str, Iterable[Any], Callable[[Any], str]]] = [
        ("nodes", source.nodes, lambda row: row.id),
        ("aisles", source.aisles, lambda row: row.id),
        ("shelf_blocks", source.shelf_blocks, lambda row: row.id),
        ("products", bundle.products.products, lambda row: row.external_id),
    ]
    for collection, records, key in collections:
        values = [key(record) for record in records]
        duplicates = sorted(
            value for value, count in Counter(values).items() if count > 1
        )
        if duplicates:
            abort(
                report,
                "DUPLICATE_SOURCE_IDENTITY",
                collection=collection,
                duplicate_ids=duplicates,
            )


def _validate_source_references(bundle: SourceBundle, report: ImportReport) -> None:
    source = bundle.store
    node_ids = {node.id for node in source.nodes}
    aisle_ids = {aisle.id for aisle in source.aisles}
    shelf_ids = {shelf.id for shelf in source.shelf_blocks}
    product_ids = {product.external_id for product in bundle.products.products}
    if source.entrance_node_id is not None and source.entrance_node_id not in node_ids:
        abort(
            report,
            "INVALID_SOURCE_REFERENCE",
            offending_record={"entrance_node_id": source.entrance_node_id},
            missing_reference=source.entrance_node_id,
            expected_source_collection="store.json.nodes",
        )
    for edge in source.edges:
        if edge.from_id == edge.to_id:
            abort(
                report,
                "INVALID_SOURCE_VALUE",
                field=f"edge {edge.from_id}->{edge.to_id}",
                reason="navigation edge endpoints must be different",
            )
    checks = [
        (
            source.edges,
            "from_id",
            node_ids,
            "store.json.nodes",
        ),
        (source.edges, "to_id", node_ids, "store.json.nodes"),
        (
            source.shelf_blocks,
            "access_node_id",
            node_ids,
            "store.json.nodes",
        ),
        (
            source.shelf_blocks,
            "aisle_id",
            aisle_ids,
            "store.json.aisles",
        ),
        (
            source.placements,
            "shelf_block_id",
            shelf_ids,
            "store.json.shelf_blocks",
        ),
    ]
    for records, attribute, expected, collection in checks:
        for record in records:
            reference = str(getattr(record, attribute))
            if reference not in expected:
                abort(
                    report,
                    "INVALID_SOURCE_REFERENCE",
                    offending_record=record.model_dump(mode="json"),
                    missing_reference=reference,
                    expected_source_collection=collection,
                )
    for placement in source.placements:
        if placement.product_external_id not in product_ids:
            abort(
                report,
                "INVALID_SOURCE_REFERENCE",
                offending_record=placement.model_dump(mode="json"),
                missing_reference=placement.product_external_id,
                expected_source_collection="product_mapping.products",
            )


def _validate_legacy_entrance(
    bundle: SourceBundle, node_types: dict[str, str], report: ImportReport
) -> None:
    entrance_node_id = bundle.store.entrance_node_id
    if entrance_node_id is None:
        return
    if node_types[entrance_node_id] != "giris":
        abort(
            report,
            "INVALID_SOURCE_REFERENCE",
            offending_record={"entrance_node_id": entrance_node_id},
            invalid_reference=entrance_node_id,
            expected_node_type="giris",
            actual_node_type=node_types[entrance_node_id],
        )


def _parse_all_slots(
    bundle: SourceBundle, report: ImportReport
) -> dict[int, ParsedSlot]:
    parsed: dict[int, ParsedSlot] = {}
    for index, placement in enumerate(bundle.store.placements):
        try:
            parsed[index] = parse_slot(placement.slot)
        except SlotSyntaxError as error:
            abort(
                report,
                "INVALID_SLOT_SYNTAX",
                shelf_external_id=placement.shelf_block_id,
                product_external_id=placement.product_external_id,
                raw_slot=error.raw,
                normalized_slot=error.normalized,
                reason=error.reason,
            )
    return parsed


def _resolve_all_levels(
    bundle: SourceBundle,
    parsed_slots: dict[int, ParsedSlot],
    report: ImportReport,
) -> dict[str, tuple[LevelDefinition, ...]]:
    placement_indexes: dict[str, list[int]] = defaultdict(list)
    for index, placement in enumerate(bundle.store.placements):
        placement_indexes[placement.shelf_block_id].append(index)

    resolved: dict[str, tuple[LevelDefinition, ...]] = {}
    for shelf in bundle.store.shelf_blocks:
        indexes = placement_indexes[shelf.id]
        raw_slots = [bundle.store.placements[index].slot for index in indexes]
        parsed_codes = {code for index in indexes for code in parsed_slots[index].codes}
        try:
            if shelf.levels is not None:
                definitions = validate_explicit_levels(shelf.levels)
                available = {definition.code for definition in definitions}
                if not parsed_codes <= available:
                    abort(
                        report,
                        "UNSUPPORTED_EXPLICIT_LEVEL_STRUCTURE",
                        shelf_external_id=shelf.id,
                        raw_slot_values=raw_slots,
                        parsed_codes=sorted(parsed_codes),
                        explicit_codes=sorted(available),
                        reason="placement references a nonexistent explicit level",
                    )
                resolved[shelf.id] = definitions
            elif indexes:
                resolved[shelf.id] = detect_template(parsed_codes)
            else:
                report.add(
                    "SHELF_LEVELS_UNRESOLVED",
                    "warning",
                    shelf_external_id=shelf.id,
                    reason="no placements available for temporary template detection",
                )
                resolved[shelf.id] = ()
        except LevelResolutionError as error:
            details = {
                "shelf_external_id": shelf.id,
                "raw_slot_values": raw_slots,
                "parsed_codes": sorted(parsed_codes),
            }
            details.update(error.details)
            abort(
                report,
                error.category,
                **details,
            )
    return resolved


def _normalize_node_types(bundle: SourceBundle, report: ImportReport) -> dict[str, str]:
    result: dict[str, str] = {}
    for node in bundle.store.nodes:
        normalized = "raf_onu" if node.kind == "raf-onu" else node.kind
        if normalized not in ALLOWED_NODE_TYPES:
            abort(
                report,
                "INVALID_NODE_TYPE",
                node_external_id=node.id,
                source_value=node.kind,
                allowed=sorted(ALLOWED_NODE_TYPES),
            )
        result[node.id] = normalized
    return result


def _resolve_store(
    state: DatabaseState,
    external_id: str,
    store_name: str | None,
    report: ImportReport,
    uuid_factory: Callable[[], UUID],
) -> StoreRecord:
    provided = store_name.strip() if store_name is not None else ""
    if state.store is None:
        if not provided:
            abort(report, "STORE_NAME_REQUIRED", store_external_id=external_id)
        return StoreRecord(uuid_factory(), external_id, provided)
    if provided:
        report.add(
            "STORE_NAME_IGNORED_EXISTING_STORE",
            "info",
            store_external_id=external_id,
            provided_store_name=provided,
            preserved_store_name=state.store.name,
        )
    return state.store


def _project_nodes(
    bundle: SourceBundle,
    state: DatabaseState,
    store_id: UUID,
    node_types: dict[str, str],
    report: ImportReport,
    inserts: dict[str, set[UUID]],
    updates: dict[str, set[UUID]],
    uuid_factory: Callable[[], UUID],
) -> dict[str, NodeRecord]:
    result: dict[str, NodeRecord] = {}
    for source in bundle.store.nodes:
        current = state.nodes.get(source.id)
        row = NodeRecord(
            current.id if current else uuid_factory(),
            store_id,
            source.id,
            node_types[source.id],
            _numeric(report, source.x, f"node {source.id}.x"),
            _numeric(report, source.y, f"node {source.id}.y"),
        )
        result[source.id] = row
        _classify("navigation_nodes", current, row, report, inserts, updates)
    missing = [node for key, node in state.nodes.items() if key not in result]
    for node in missing:
        report.add(
            "MISSING_NAVIGATION_NODE",
            "warning",
            external_id=node.external_id,
        )
    report.stats("navigation_nodes").retained_missing = len(missing)
    return result


def _project_aisles(
    bundle: SourceBundle,
    state: DatabaseState,
    store_id: UUID,
    report: ImportReport,
    inserts: dict[str, set[UUID]],
    updates: dict[str, set[UUID]],
    uuid_factory: Callable[[], UUID],
) -> tuple[dict[str, AisleRecord], set[UUID]]:
    result: dict[str, AisleRecord] = {}
    clear: set[UUID] = set()
    for source in bundle.store.aisles:
        if source.aisle_number is not None and source.aisle_number <= 0:
            abort(
                report,
                "INVALID_SOURCE_VALUE",
                field=f"aisle {source.id}.aisle_number",
                value=source.aisle_number,
            )
        current = state.aisles.get(source.id)
        row = AisleRecord(
            current.id if current else uuid_factory(),
            store_id,
            source.id,
            _required_text(report, source.name, f"aisle {source.id}.name"),
            source.aisle_number,
        )
        result[source.id] = row
        _classify("aisles", current, row, report, inserts, updates)
        if current and current.aisle_number != row.aisle_number:
            clear.add(current.id)

    missing = [aisle for key, aisle in state.aisles.items() if key not in result]
    for aisle in missing:
        report.add("MISSING_AISLE", "warning", external_id=aisle.external_id)
    report.stats("aisles").retained_missing = len(missing)

    projected = [*result.values(), *missing]
    by_number: dict[int, list[str]] = defaultdict(list)
    for aisle in projected:
        if aisle.aisle_number is not None:
            by_number[aisle.aisle_number].append(aisle.external_id)
    conflicts = {
        number: sorted(ids) for number, ids in by_number.items() if len(ids) > 1
    }
    if conflicts:
        number, ids = min(conflicts.items())
        abort(
            report,
            "AISLE_NUMBER_PROJECTED_CONFLICT",
            store_id=str(store_id),
            aisle_number=number,
            conflicting_external_ids=ids,
        )
    return result, clear


def _project_products(
    bundle: SourceBundle,
    state: DatabaseState,
    store_id: UUID,
    report: ImportReport,
    inserts: dict[str, set[UUID]],
    updates: dict[str, set[UUID]],
    uuid_factory: Callable[[], UUID],
) -> dict[str, ProductRecord]:
    result: dict[str, ProductRecord] = {}
    for source in bundle.products.products:
        external_id = source.external_id
        current = state.products.get(external_id)
        _required_text(report, source.name, f"product {external_id}.name")
        row = ProductRecord(
            current.id if current else uuid_factory(),
            store_id,
            external_id,
            source.name,
            _required_text(report, source.category, f"product {external_id}.category"),
            _required_text(report, source.unit, f"product {external_id}.unit"),
        )
        result[external_id] = row
        _classify("products", current, row, report, inserts, updates)
    missing = [product for key, product in state.products.items() if key not in result]
    for product in missing:
        report.add(
            "MISSING_PRODUCT_REMOVED_FROM_CATALOG",
            "warning",
            external_id=product.external_id,
        )
    report.stats("products").retained_missing = len(missing)
    return result


def _project_edges(
    bundle: SourceBundle,
    state: DatabaseState,
    store_id: UUID,
    nodes: dict[str, NodeRecord],
    report: ImportReport,
    inserts: dict[str, set[UUID]],
    updates: dict[str, set[UUID]],
    uuid_factory: Callable[[], UUID],
) -> list[EdgeRecord]:
    result: list[EdgeRecord] = []
    identities: set[tuple[UUID, UUID]] = set()
    for source in bundle.store.edges:
        is_bidirectional = source.is_bidirectional
        if is_bidirectional is None and "is_bidirectional" in source.model_fields_set:
            abort(
                report,
                "INVALID_SOURCE_STRUCTURE",
                edge={"from_id": source.from_id, "to_id": source.to_id},
                field="is_bidirectional",
                reason="explicit is_bidirectional must be boolean",
            )
        if is_bidirectional is None:
            is_bidirectional = True
            report.add(
                "LEGACY_EDGE_DIRECTIONALITY_DEFAULTED",
                "info",
                store_external_id=bundle.store.store_id,
                source_from_id=source.from_id,
                source_to_id=source.to_id,
            )
        from_id = nodes[source.from_id].id
        to_id = nodes[source.to_id].id
        if is_bidirectional and to_id < from_id:
            from_id, to_id = to_id, from_id
        identity = (from_id, to_id)
        if identity in identities:
            abort(
                report,
                "DUPLICATE_SOURCE_IDENTITY",
                collection="edges",
                from_id=source.from_id,
                to_id=source.to_id,
            )
        identities.add(identity)
        current = state.edges.get(identity)
        distance = _numeric(
            report, source.weight, f"edge {source.from_id}->{source.to_id}.weight"
        )
        if distance <= 0:
            abort(
                report,
                "INVALID_SOURCE_VALUE",
                field=f"edge {source.from_id}->{source.to_id}.weight",
                value=str(distance),
            )
        row = EdgeRecord(
            current.id if current else uuid_factory(),
            store_id,
            from_id,
            to_id,
            distance,
            is_bidirectional,
        )
        result.append(row)
        _classify("navigation_edges", current, row, report, inserts, updates)
    return result


def _project_shelves(
    bundle: SourceBundle,
    state: DatabaseState,
    store_id: UUID,
    nodes: dict[str, NodeRecord],
    aisles: dict[str, AisleRecord],
    report: ImportReport,
    inserts: dict[str, set[UUID]],
    updates: dict[str, set[UUID]],
    uuid_factory: Callable[[], UUID],
) -> dict[str, ShelfRecord]:
    result: dict[str, ShelfRecord] = {}
    for source in bundle.store.shelf_blocks:
        current = state.shelves.get(source.id)
        size_x = _numeric(report, source.w, f"shelf {source.id}.w")
        size_y = _numeric(report, source.h, f"shelf {source.id}.h")
        if size_x <= 0 or size_y <= 0:
            abort(
                report,
                "INVALID_SOURCE_VALUE",
                field=f"shelf {source.id}.size",
                value=[str(size_x), str(size_y)],
            )
        row = ShelfRecord(
            current.id if current else uuid_factory(),
            store_id,
            aisles[source.aisle_id].id,
            nodes[source.access_node_id].id,
            source.id,
            _numeric(report, source.x, f"shelf {source.id}.x"),
            _numeric(report, source.y, f"shelf {source.id}.y"),
            size_x,
            size_y,
            source.facing,
            source.side,
            current.is_active if current else True,
        )
        result[source.id] = row
        _classify("shelf_blocks", current, row, report, inserts, updates)
    return result


def _project_levels(
    bundle: SourceBundle,
    state: DatabaseState,
    store_id: UUID,
    shelves: dict[str, ShelfRecord],
    definitions: dict[str, tuple[LevelDefinition, ...]],
    report: ImportReport,
    inserts: dict[str, set[UUID]],
    updates: dict[str, set[UUID]],
    uuid_factory: Callable[[], UUID],
) -> tuple[dict[tuple[UUID, str], LevelRecord], dict[UUID, int]]:
    result: dict[tuple[UUID, str], LevelRecord] = {}
    stage_orders: dict[UUID, int] = {}
    for shelf_source in bundle.store.shelf_blocks:
        shelf = shelves[shelf_source.id]
        desired_codes: set[str] = set()
        shelf_rows: list[LevelRecord] = []
        for definition in definitions[shelf_source.id]:
            desired_codes.add(definition.code)
            identity = (shelf.id, definition.code)
            current = state.levels.get(identity)
            row = LevelRecord(
                current.id if current else uuid_factory(),
                store_id,
                shelf.id,
                definition.code,
                definition.level_order,
                definition.description,
            )
            result[identity] = row
            shelf_rows.append(row)
            _classify("shelf_levels", current, row, report, inserts, updates)

        stale = [
            level
            for (shelf_id, code), level in state.levels.items()
            if shelf_id == shelf.id and code not in desired_codes
        ]
        for level in stale:
            report.add(
                "MISSING_SHELF_LEVEL",
                "warning",
                shelf_external_id=shelf_source.id,
                retained_level={
                    "code": level.code,
                    "order": level.level_order,
                    "id": str(level.id),
                },
            )
        report.stats("shelf_levels").retained_missing += len(stale)
        _validate_level_projection(report, shelf_source.id, shelf_rows, stale)

        changing = [
            row
            for row in shelf_rows
            if (current := state.levels.get((shelf.id, row.code)))
            and current.level_order != row.level_order
        ]
        current_shelf_levels = [
            level
            for (shelf_id, _), level in state.levels.items()
            if shelf_id == shelf.id
        ]
        max_order = max(
            [
                level.level_order
                for level in [*shelf_rows, *stale, *current_shelf_levels]
            ]
            or [0]
        )
        for offset, row in enumerate(changing, start=1):
            stage_orders[row.id] = max_order + offset
    return result, stage_orders


def _project_placements(
    bundle: SourceBundle,
    state: DatabaseState,
    store_id: UUID,
    products: dict[str, ProductRecord],
    shelves: dict[str, ShelfRecord],
    parsed_slots: dict[int, ParsedSlot],
    report: ImportReport,
    inserts: dict[str, set[UUID]],
    updates: dict[str, set[UUID]],
    uuid_factory: Callable[[], UUID],
) -> list[PlacementRecord]:
    result: list[PlacementRecord] = []
    identities: set[tuple[UUID, UUID]] = set()
    for index, source in enumerate(bundle.store.placements):
        product = products[source.product_external_id]
        shelf = shelves[source.shelf_block_id]
        identity = (product.id, shelf.id)
        if identity in identities:
            abort(
                report,
                "DUPLICATE_SOURCE_IDENTITY",
                collection="placements",
                product_external_id=source.product_external_id,
                shelf_external_id=source.shelf_block_id,
            )
        identities.add(identity)
        current = state.placements.get(identity)
        row = PlacementRecord(
            current.id if current else uuid_factory(),
            store_id,
            product.id,
            shelf.id,
            source.slot,
        )
        result.append(row)
        _classify("product_placements", current, row, report, inserts, updates)
    return result


def _missing_shelves(
    state: DatabaseState, shelves: dict[str, ShelfRecord]
) -> list[ShelfRecord]:
    return [shelf for key, shelf in state.shelves.items() if key not in shelves]


def _desired_placement_levels(
    placements: list[PlacementRecord],
    levels: dict[tuple[UUID, str], LevelRecord],
    parsed_slots: dict[int, ParsedSlot],
) -> set[tuple[UUID, UUID, UUID]]:
    desired: set[tuple[UUID, UUID, UUID]] = set()
    for index, placement in enumerate(placements):
        for code in parsed_slots[index].codes:
            level = levels[(placement.shelf_block_id, code)]
            desired.add((placement.id, level.id, placement.shelf_block_id))
    return desired


def _validate_level_projection(
    report: ImportReport,
    shelf_external_id: str,
    incoming: list[LevelRecord],
    retained: list[LevelRecord],
) -> None:
    projected = [*incoming, *retained]
    for attribute in ("code", "level_order"):
        grouped: dict[Any, list[LevelRecord]] = defaultdict(list)
        for level in projected:
            grouped[getattr(level, attribute)].append(level)
        for value, levels in grouped.items():
            if len(levels) > 1:
                incoming_level = next(
                    (level for level in levels if level in incoming), None
                )
                retained_level = next(
                    (level for level in levels if level in retained), None
                )
                abort(
                    report,
                    "SHELF_LEVEL_PROJECTED_CONFLICT",
                    shelf_external_id=shelf_external_id,
                    conflict_field=attribute,
                    conflict_value=value,
                    incoming_level=_level_details(incoming_level),
                    retained_level=_level_details(retained_level),
                )


def _threshold(
    *,
    baseline: int,
    affected: list[str],
    max_count: int,
    max_ratio: Decimal,
) -> ThresholdResult:
    missing_count = len(affected)
    ratio = Decimal(0) if baseline == 0 else Decimal(missing_count) / Decimal(baseline)
    return ThresholdResult(
        baseline,
        missing_count,
        ratio,
        max_count,
        max_ratio,
        sorted(affected),
    )


def _enforce_threshold(
    report: ImportReport, result: ThresholdResult, category: str
) -> None:
    all_missing = result.baseline > 0 and result.missing_count == result.baseline
    if all_missing or (
        result.missing_count > result.max_count
        and result.missing_ratio > result.max_ratio
    ):
        abort(
            report,
            category,
            baseline=result.baseline,
            missing_count=result.missing_count,
            missing_ratio=str(result.missing_ratio),
            max_count=result.max_count,
            max_ratio=str(result.max_ratio),
            all_missing=all_missing,
            affected_ids=result.affected_ids,
        )


def _report_edge_changes(
    state: DatabaseState,
    desired: list[EdgeRecord],
    missing: list[EdgeRecord],
    report: ImportReport,
) -> None:
    missing_pairs = {
        frozenset((edge.from_node_id, edge.to_node_id)): edge for edge in missing
    }
    for edge in desired:
        current = state.edges.get((edge.from_node_id, edge.to_node_id))
        pair = frozenset((edge.from_node_id, edge.to_node_id))
        old = missing_pairs.get(pair)
        if old or (current and current.is_bidirectional != edge.is_bidirectional):
            report.add(
                "EDGE_TOPOLOGY_OR_DIRECTION_CHANGED",
                "warning",
                unordered_node_pair=sorted(str(node_id) for node_id in pair),
                previous_edge_id=str((old or current).id),
                desired_edge_id=str(edge.id),
            )


def _report_products_losing_placements(
    state: DatabaseState,
    products: dict[str, ProductRecord],
    desired: list[PlacementRecord],
    report: ImportReport,
) -> None:
    before = Counter(placement.product_id for placement in state.placements.values())
    after = Counter(placement.product_id for placement in desired)
    for product in products.values():
        if before[product.id] > 0 and after[product.id] == 0:
            report.add(
                "PRODUCTS_WITH_NO_PLACEMENT_AFTER_IMPORT",
                "warning",
                product_external_id=product.external_id,
                previous_placement_count=before[product.id],
            )


def _classify(
    table: str,
    current: T | None,
    desired: T,
    report: ImportReport,
    inserts: dict[str, set[UUID]],
    updates: dict[str, set[UUID]],
) -> None:
    record_id = desired.id
    stats = report.stats(table)
    if current is None:
        inserts[table].add(record_id)
        stats.inserted += 1
    elif current != desired:
        updates[table].add(record_id)
        stats.updated += 1
    else:
        stats.unchanged += 1


def _numeric(report: ImportReport, value: Decimal, field: str) -> Decimal:
    normalized = value.quantize(THREE_PLACES, rounding=ROUND_HALF_UP)
    if abs(normalized) > MAX_NUMERIC_8_3:
        abort(
            report,
            "INVALID_SOURCE_VALUE",
            field=field,
            value=str(value),
            reason="outside NUMERIC(8,3) range",
        )
    return normalized


def _required_text(report: ImportReport, value: str, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        abort(report, "INVALID_SOURCE_STRUCTURE", field=field, reason="empty value")
    return normalized


def _level_details(level: LevelRecord | None) -> dict[str, Any] | None:
    if level is None:
        return None
    return {
        "id": str(level.id),
        "code": level.code,
        "order": level.level_order,
    }
