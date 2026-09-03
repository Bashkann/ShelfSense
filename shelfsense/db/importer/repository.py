"""SQLAlchemy Core repository for atomic importer writes."""

from collections.abc import Iterable
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine, RowMapping

from shelfsense.db.importer.state import (
    AisleRecord,
    DatabaseState,
    EdgeRecord,
    ImportPlan,
    LevelRecord,
    NodeRecord,
    PlacementRecord,
    ProductRecord,
    ShelfRecord,
    StoreRecord,
)


class SqlImportRepository:
    """Read importer state and apply one plan in one transaction."""

    def __init__(self, engine: Engine):
        self.engine = engine

    def read_store_state(self, store_external_id: str) -> DatabaseState:
        """Read a consistent store-scoped snapshot without writes."""

        with self.engine.connect() as connection:
            store_row = (
                connection.execute(
                    text(
                        "SELECT id, external_id, name, is_active "
                        "FROM stores WHERE external_id = :external_id"
                    ),
                    {"external_id": store_external_id},
                )
                .mappings()
                .one_or_none()
            )
            if store_row is None:
                return DatabaseState()

            store = _store(store_row)
            store_id = store.id
            nodes = {
                row["external_id"]: _node(row)
                for row in _rows(
                    connection,
                    "SELECT id, store_id, external_id, node_type, x_m, y_m "
                    "FROM navigation_nodes WHERE store_id = :store_id",
                    store_id,
                )
            }
            aisles = {
                row["external_id"]: _aisle(row)
                for row in _rows(
                    connection,
                    "SELECT id, store_id, external_id, name, aisle_number "
                    "FROM aisles WHERE store_id = :store_id",
                    store_id,
                )
            }
            products = {
                row["external_id"]: _product(row)
                for row in _rows(
                    connection,
                    "SELECT id, store_id, external_id, name, category, unit "
                    "FROM products WHERE store_id = :store_id",
                    store_id,
                )
            }
            edge_rows = _rows(
                connection,
                "SELECT id, store_id, from_node_id, to_node_id, distance_m, "
                "is_bidirectional FROM navigation_edges WHERE store_id = :store_id",
                store_id,
            )
            edges = {
                (row["from_node_id"], row["to_node_id"]): _edge(row)
                for row in edge_rows
            }
            shelves = {
                row["external_id"]: _shelf(row)
                for row in _rows(
                    connection,
                    "SELECT id, store_id, aisle_id, access_node_id, external_id, "
                    "x_m, y_m, size_x_m, size_y_m, facing, side_description, "
                    "is_active FROM shelf_blocks WHERE store_id = :store_id",
                    store_id,
                )
            }
            level_rows = _rows(
                connection,
                "SELECT id, store_id, shelf_block_id, code, level_order, description "
                "FROM shelf_levels WHERE store_id = :store_id",
                store_id,
            )
            levels = {
                (row["shelf_block_id"], row["code"]): _level(row) for row in level_rows
            }
            placement_rows = _rows(
                connection,
                "SELECT id, store_id, product_id, shelf_block_id, slot_code "
                "FROM product_placements WHERE store_id = :store_id",
                store_id,
            )
            placements = {
                (row["product_id"], row["shelf_block_id"]): _placement(row)
                for row in placement_rows
            }
            placement_levels = {
                (row["placement_id"], row["shelf_level_id"])
                for row in connection.execute(
                    text(
                        "SELECT ppl.placement_id, ppl.shelf_level_id "
                        "FROM product_placement_levels ppl "
                        "JOIN product_placements pp ON pp.id = ppl.placement_id "
                        "WHERE pp.store_id = :store_id"
                    ),
                    {"store_id": store_id},
                ).mappings()
            }
            return DatabaseState(
                store=store,
                nodes=nodes,
                aisles=aisles,
                products=products,
                edges=edges,
                shelves=shelves,
                levels=levels,
                placements=placements,
                placement_levels=placement_levels,
            )

    def apply_plan(self, plan: ImportPlan) -> None:
        """Apply all mutations inside a single SQLAlchemy transaction."""

        with self.engine.begin() as connection:
            self._write_store(connection, plan)
            self._write_nodes(connection, plan)
            self._write_aisles(connection, plan)
            self._write_products(connection, plan)
            self._delete_edges(connection, plan.edge_ids_to_delete)
            self._write_edges(connection, plan)
            self._write_shelves(connection, plan)
            self._deactivate_shelves(connection, plan.shelf_ids_to_deactivate)
            self._write_levels(connection, plan)
            self._delete_placements(connection, plan.placement_ids_to_delete)
            self._write_placements(connection, plan)
            self._delete_placement_levels(connection, plan.placement_levels_to_delete)
            self._insert_placement_levels(connection, plan.placement_levels_to_insert)

    def _write_store(self, connection: Connection, plan: ImportPlan) -> None:
        if not plan.store_is_new:
            return
        connection.execute(
            text(
                "INSERT INTO stores (id, external_id, name) "
                "VALUES (:id, :external_id, :name)"
            ),
            _params(plan.store),
        )

    def _write_nodes(self, connection: Connection, plan: ImportPlan) -> None:
        statement = text(
            "INSERT INTO navigation_nodes "
            "(id, store_id, external_id, node_type, x_m, y_m) "
            "VALUES (:id, :store_id, :external_id, :node_type, :x_m, :y_m) "
            "ON CONFLICT (store_id, external_id) DO UPDATE SET "
            "node_type = EXCLUDED.node_type, x_m = EXCLUDED.x_m, y_m = EXCLUDED.y_m"
        )
        self._write_changed(connection, statement, plan.nodes, plan, "navigation_nodes")

    def _write_aisles(self, connection: Connection, plan: ImportPlan) -> None:
        for aisle_id in plan.aisle_numbers_to_clear:
            connection.execute(
                text("UPDATE aisles SET aisle_number = NULL WHERE id = :id"),
                {"id": aisle_id},
            )
        statement = text(
            "INSERT INTO aisles "
            "(id, store_id, external_id, name, aisle_number) "
            "VALUES (:id, :store_id, :external_id, :name, :aisle_number) "
            "ON CONFLICT (store_id, external_id) DO UPDATE SET "
            "name = EXCLUDED.name, aisle_number = EXCLUDED.aisle_number"
        )
        self._write_changed(connection, statement, plan.aisles, plan, "aisles")

    def _write_products(self, connection: Connection, plan: ImportPlan) -> None:
        statement = text(
            "INSERT INTO products (id, store_id, external_id, name, category, unit) "
            "VALUES (:id, :store_id, :external_id, :name, :category, :unit) "
            "ON CONFLICT (store_id, external_id) DO UPDATE SET "
            "name = EXCLUDED.name, category = EXCLUDED.category, unit = EXCLUDED.unit"
        )
        self._write_changed(connection, statement, plan.products, plan, "products")

    def _write_edges(self, connection: Connection, plan: ImportPlan) -> None:
        statement = text(
            "INSERT INTO navigation_edges "
            "(id, store_id, from_node_id, to_node_id, distance_m, is_bidirectional) "
            "VALUES (:id, :store_id, :from_node_id, :to_node_id, :distance_m, "
            ":is_bidirectional) "
            "ON CONFLICT (store_id, from_node_id, to_node_id) DO UPDATE SET "
            "distance_m = EXCLUDED.distance_m, "
            "is_bidirectional = EXCLUDED.is_bidirectional"
        )
        self._write_changed(connection, statement, plan.edges, plan, "navigation_edges")

    def _write_shelves(self, connection: Connection, plan: ImportPlan) -> None:
        statement = text(
            "INSERT INTO shelf_blocks "
            "(id, store_id, aisle_id, access_node_id, external_id, x_m, y_m, "
            "size_x_m, size_y_m, facing, side_description) "
            "VALUES (:id, :store_id, :aisle_id, :access_node_id, :external_id, "
            ":x_m, :y_m, :size_x_m, :size_y_m, :facing, :side_description) "
            "ON CONFLICT (store_id, external_id) DO UPDATE SET "
            "aisle_id = EXCLUDED.aisle_id, access_node_id = EXCLUDED.access_node_id, "
            "x_m = EXCLUDED.x_m, y_m = EXCLUDED.y_m, "
            "size_x_m = EXCLUDED.size_x_m, size_y_m = EXCLUDED.size_y_m, "
            "facing = EXCLUDED.facing, side_description = EXCLUDED.side_description"
        )
        self._write_changed(connection, statement, plan.shelves, plan, "shelf_blocks")

    def _write_levels(self, connection: Connection, plan: ImportPlan) -> None:
        for level_id, temporary_order in plan.level_orders_to_stage.items():
            connection.execute(
                text("UPDATE shelf_levels SET level_order = :value WHERE id = :id"),
                {"id": level_id, "value": temporary_order},
            )
        statement = text(
            "INSERT INTO shelf_levels "
            "(id, store_id, shelf_block_id, code, level_order, description) "
            "VALUES (:id, :store_id, :shelf_block_id, :code, :level_order, "
            ":description) "
            "ON CONFLICT (shelf_block_id, code) DO UPDATE SET "
            "level_order = EXCLUDED.level_order, description = EXCLUDED.description"
        )
        self._write_changed(connection, statement, plan.levels, plan, "shelf_levels")

    def _write_placements(self, connection: Connection, plan: ImportPlan) -> None:
        statement = text(
            "INSERT INTO product_placements "
            "(id, store_id, product_id, shelf_block_id, slot_code) "
            "VALUES (:id, :store_id, :product_id, :shelf_block_id, :slot_code) "
            "ON CONFLICT (store_id, product_id, shelf_block_id) DO UPDATE SET "
            "slot_code = EXCLUDED.slot_code"
        )
        self._write_changed(
            connection, statement, plan.placements, plan, "product_placements"
        )

    @staticmethod
    def _write_changed(
        connection: Connection,
        statement: Any,
        records: Iterable[Any],
        plan: ImportPlan,
        table: str,
    ) -> None:
        changed_ids = plan.insert_ids.get(table, set()) | plan.update_ids.get(
            table, set()
        )
        parameters = [_params(record) for record in records if record.id in changed_ids]
        if parameters:
            connection.execute(statement, parameters)

    @staticmethod
    def _delete_edges(connection: Connection, ids: set[UUID]) -> None:
        _delete_ids(connection, "navigation_edges", ids)

    @staticmethod
    def _deactivate_shelves(connection: Connection, ids: set[UUID]) -> None:
        for record_id in ids:
            connection.execute(
                text("UPDATE shelf_blocks SET is_active = false WHERE id = :id"),
                {"id": record_id},
            )

    @staticmethod
    def _delete_placements(connection: Connection, ids: set[UUID]) -> None:
        _delete_ids(connection, "product_placements", ids)

    @staticmethod
    def _delete_placement_levels(
        connection: Connection, identities: set[tuple[UUID, UUID]]
    ) -> None:
        statement = text(
            "DELETE FROM product_placement_levels "
            "WHERE placement_id = :placement_id AND shelf_level_id = :shelf_level_id"
        )
        for placement_id, shelf_level_id in identities:
            connection.execute(
                statement,
                {"placement_id": placement_id, "shelf_level_id": shelf_level_id},
            )

    @staticmethod
    def _insert_placement_levels(
        connection: Connection, identities: set[tuple[UUID, UUID, UUID]]
    ) -> None:
        statement = text(
            "INSERT INTO product_placement_levels "
            "(placement_id, shelf_level_id, shelf_block_id) "
            "VALUES (:placement_id, :shelf_level_id, :shelf_block_id) "
            "ON CONFLICT (placement_id, shelf_level_id) DO NOTHING"
        )
        if identities:
            connection.execute(
                statement,
                [
                    {
                        "placement_id": placement_id,
                        "shelf_level_id": level_id,
                        "shelf_block_id": shelf_id,
                    }
                    for placement_id, level_id, shelf_id in identities
                ],
            )


def _rows(connection: Connection, query: str, store_id: UUID) -> Iterable[RowMapping]:
    return connection.execute(text(query), {"store_id": store_id}).mappings()


def _delete_ids(connection: Connection, table: str, ids: set[UUID]) -> None:
    if table not in {"navigation_edges", "product_placements"}:
        raise ValueError(f"unsupported delete table: {table}")
    statement = text(f"DELETE FROM {table} WHERE id = :id")
    for record_id in ids:
        connection.execute(statement, {"id": record_id})


def _params(record: Any) -> dict[str, Any]:
    return dict(vars(record))


def _store(row: RowMapping) -> StoreRecord:
    return StoreRecord(**row)


def _node(row: RowMapping) -> NodeRecord:
    return NodeRecord(**row)


def _aisle(row: RowMapping) -> AisleRecord:
    return AisleRecord(**row)


def _product(row: RowMapping) -> ProductRecord:
    return ProductRecord(**row)


def _edge(row: RowMapping) -> EdgeRecord:
    return EdgeRecord(**row)


def _shelf(row: RowMapping) -> ShelfRecord:
    return ShelfRecord(**row)


def _level(row: RowMapping) -> LevelRecord:
    return LevelRecord(**row)


def _placement(row: RowMapping) -> PlacementRecord:
    return PlacementRecord(**row)
