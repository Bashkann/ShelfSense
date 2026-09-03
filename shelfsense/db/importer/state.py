"""Importer database snapshots and immutable write plans."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from shelfsense.db.importer.report import ImportReport


@dataclass(frozen=True)
class ImportThresholds:
    max_missing_shelves: int
    max_missing_shelf_ratio: Decimal
    max_missing_edges: int
    max_missing_edge_ratio: Decimal
    max_missing_placements: int
    max_missing_placement_ratio: Decimal


@dataclass(frozen=True)
class StoreRecord:
    id: UUID
    external_id: str
    name: str
    is_active: bool = True


@dataclass(frozen=True)
class NodeRecord:
    id: UUID
    store_id: UUID
    external_id: str
    node_type: str
    x_m: Decimal
    y_m: Decimal


@dataclass(frozen=True)
class AisleRecord:
    id: UUID
    store_id: UUID
    external_id: str
    name: str
    aisle_number: int | None


@dataclass(frozen=True)
class ProductRecord:
    id: UUID
    store_id: UUID
    external_id: str
    name: str
    category: str
    unit: str


@dataclass(frozen=True)
class EdgeRecord:
    id: UUID
    store_id: UUID
    from_node_id: UUID
    to_node_id: UUID
    distance_m: Decimal
    is_bidirectional: bool


@dataclass(frozen=True)
class ShelfRecord:
    id: UUID
    store_id: UUID
    aisle_id: UUID
    access_node_id: UUID
    external_id: str
    x_m: Decimal
    y_m: Decimal
    size_x_m: Decimal
    size_y_m: Decimal
    facing: str
    side_description: str
    is_active: bool = True


@dataclass(frozen=True)
class LevelRecord:
    id: UUID
    store_id: UUID
    shelf_block_id: UUID
    code: str
    level_order: int
    description: str


@dataclass(frozen=True)
class PlacementRecord:
    id: UUID
    store_id: UUID
    product_id: UUID
    shelf_block_id: UUID
    slot_code: str


@dataclass
class DatabaseState:
    """Current rows scoped to one store external ID."""

    store: StoreRecord | None = None
    nodes: dict[str, NodeRecord] = field(default_factory=dict)
    aisles: dict[str, AisleRecord] = field(default_factory=dict)
    products: dict[str, ProductRecord] = field(default_factory=dict)
    edges: dict[tuple[UUID, UUID], EdgeRecord] = field(default_factory=dict)
    shelves: dict[str, ShelfRecord] = field(default_factory=dict)
    levels: dict[tuple[UUID, str], LevelRecord] = field(default_factory=dict)
    placements: dict[tuple[UUID, UUID], PlacementRecord] = field(default_factory=dict)
    placement_levels: set[tuple[UUID, UUID]] = field(default_factory=set)


@dataclass
class ImportPlan:
    """Fully preflighted desired state and exact write operations."""

    store: StoreRecord
    store_is_new: bool
    nodes: tuple[NodeRecord, ...]
    aisles: tuple[AisleRecord, ...]
    products: tuple[ProductRecord, ...]
    edges: tuple[EdgeRecord, ...]
    shelves: tuple[ShelfRecord, ...]
    levels: tuple[LevelRecord, ...]
    placements: tuple[PlacementRecord, ...]
    desired_placement_levels: set[tuple[UUID, UUID, UUID]]
    insert_ids: dict[str, set[UUID]]
    update_ids: dict[str, set[UUID]]
    aisle_numbers_to_clear: set[UUID]
    level_orders_to_stage: dict[UUID, int]
    edge_ids_to_delete: set[UUID]
    shelf_ids_to_deactivate: set[UUID]
    placement_ids_to_delete: set[UUID]
    placement_levels_to_delete: set[tuple[UUID, UUID]]
    placement_levels_to_insert: set[tuple[UUID, UUID, UUID]]
    report: ImportReport


class ImportRepository(Protocol):
    """Read-current-state and atomic-apply boundary."""

    def read_store_state(self, store_external_id: str) -> DatabaseState:
        """Read without changing database state."""

    def apply_plan(self, plan: ImportPlan) -> None:
        """Apply the complete plan atomically or raise."""
