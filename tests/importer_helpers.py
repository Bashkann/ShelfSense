"""Synthetic importer fixtures and an atomic in-memory repository."""

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
from typing import Any
from uuid import UUID

from shelfsense.db.importer.source import SourceBundle
from shelfsense.db.importer.state import DatabaseState, ImportPlan, ImportThresholds

DEFAULT_THRESHOLDS = ImportThresholds(
    max_missing_shelves=3,
    max_missing_shelf_ratio=Decimal("0.20"),
    max_missing_edges=2,
    max_missing_edge_ratio=Decimal("0.10"),
    max_missing_placements=5,
    max_missing_placement_ratio=Decimal("0.15"),
)


class SequentialUUIDs:
    """Predictable UUID source for identity-preservation tests."""

    def __init__(self, start: int = 1):
        self.value = start

    def __call__(self) -> UUID:
        result = UUID(int=self.value)
        self.value += 1
        return result


class MemoryRepository:
    """Single-store repository test double with atomic plan application."""

    def __init__(self, state: DatabaseState | None = None):
        self.state = state or DatabaseState()
        self.read_calls = 0
        self.apply_calls = 0
        self.fail_during_apply = False
        self.observed_partial_write = False

    def read_store_state(self, store_external_id: str) -> DatabaseState:
        self.read_calls += 1
        if self.state.store and self.state.store.external_id != store_external_id:
            return DatabaseState()
        return deepcopy(self.state)

    def apply_plan(self, plan: ImportPlan) -> None:
        self.apply_calls += 1
        working = deepcopy(self.state)
        if plan.store_is_new:
            working.store = plan.store
        self._upsert(working.nodes, plan.nodes, lambda row: row.external_id)
        if self.fail_during_apply:
            self.observed_partial_write = working.store is not None and bool(
                working.nodes
            )
            raise RuntimeError("synthetic write failure")
        self._upsert(working.aisles, plan.aisles, lambda row: row.external_id)
        self._upsert(working.products, plan.products, lambda row: row.external_id)

        delete_edge_ids = plan.edge_ids_to_delete
        working.edges = {
            key: row
            for key, row in working.edges.items()
            if row.id not in delete_edge_ids
        }
        self._upsert(
            working.edges,
            plan.edges,
            lambda row: (row.from_node_id, row.to_node_id),
        )
        self._upsert(working.shelves, plan.shelves, lambda row: row.external_id)
        for key, row in list(working.shelves.items()):
            if row.id in plan.shelf_ids_to_deactivate:
                working.shelves[key] = replace(row, is_active=False)

        self._upsert(
            working.levels,
            plan.levels,
            lambda row: (row.shelf_block_id, row.code),
        )

        deleted_placement_ids = plan.placement_ids_to_delete
        working.placements = {
            key: row
            for key, row in working.placements.items()
            if row.id not in deleted_placement_ids
        }
        working.placement_levels = {
            link
            for link in working.placement_levels
            if link[0] not in deleted_placement_ids
        }
        self._upsert(
            working.placements,
            plan.placements,
            lambda row: (row.product_id, row.shelf_block_id),
        )
        working.placement_levels -= plan.placement_levels_to_delete
        working.placement_levels |= {
            (placement_id, level_id)
            for placement_id, level_id, _ in plan.placement_levels_to_insert
        }
        self.state = working

    @staticmethod
    def _upsert(target: dict, records: object, key) -> None:
        for row in records:
            target[key(row)] = row


def bundle_data() -> dict[str, Any]:
    """Return a minimal valid real-style source pair."""

    return {
        "store": {
            "store_id": "store-1",
            "entrance_node_id": "node-entrance",
            "nodes": [
                {"id": "node-entrance", "x": "0", "y": "0", "kind": "giris"},
                {"id": "node-shelf", "x": "2", "y": "0", "kind": "raf-onu"},
            ],
            "edges": [
                {"from_id": "node-shelf", "to_id": "node-entrance", "weight": "2"}
            ],
            "aisles": [{"id": "aisle-1", "name": "Aisle 1", "aisle_number": 1}],
            "shelf_blocks": [
                {
                    "id": "shelf-1",
                    "aisle_id": "aisle-1",
                    "access_node_id": "node-shelf",
                    "x": "2",
                    "y": "0",
                    "w": "1",
                    "h": "1",
                    "facing": "+x",
                    "side": "left wall",
                }
            ],
            "placements": [{"product_id": 1, "shelf_block_id": "shelf-1", "slot": "A"}],
        },
        "products": {
            "products": [
                {
                    "id": 1,
                    "name": "Flour",
                    "category": "dry_goods",
                    "unit": "kg",
                    "shelf": "ignored-mapping-shelf",
                    "slot": "ignored-mapping-slot",
                }
            ]
        },
    }


def make_bundle(data: dict[str, Any] | None = None) -> SourceBundle:
    values = deepcopy(data or bundle_data())
    return SourceBundle.model_validate(
        {"store": values["store"], "products": values["products"]}
    )


def categories(report) -> list[str]:
    return [entry.category for entry in report.entries]
