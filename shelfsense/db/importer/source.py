"""JSON source loading and basic source models."""

import json
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, StrictBool, ValidationError, field_validator


class SourceLoadError(ValueError):
    """A source file could not be read or parsed."""

    def __init__(self, category: str, details: dict[str, Any]):
        self.category = category
        self.details = details
        super().__init__(category)


class SourceModel(BaseModel):
    """Base source model that ignores explicitly non-authoritative extras."""

    model_config = ConfigDict(extra="ignore")


class NodeSource(SourceModel):
    id: str
    x: Decimal
    y: Decimal
    kind: str


class EdgeSource(SourceModel):
    from_id: str
    to_id: str
    weight: Decimal
    is_bidirectional: StrictBool | None = None


class AisleSource(SourceModel):
    id: str
    name: str
    aisle_number: int | None = None


class ExplicitLevelSource(SourceModel):
    code: str
    order: int


class ShelfBlockSource(SourceModel):
    id: str
    aisle_id: str
    access_node_id: str
    x: Decimal
    y: Decimal
    w: Decimal
    h: Decimal
    facing: Literal["+x", "-x", "+y", "-y", "open"]
    side: str
    levels: list[ExplicitLevelSource] | None = None

    @field_validator("side")
    @classmethod
    def require_usable_side(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("side must contain a usable value")
        return normalized


class PlacementSource(SourceModel):
    product_id: int | str
    shelf_block_id: str
    slot: str

    @property
    def product_external_id(self) -> str:
        return str(self.product_id)


class StoreSource(SourceModel):
    store_id: str
    entrance_node_id: str | None = None
    nodes: list[NodeSource]
    edges: list[EdgeSource]
    aisles: list[AisleSource]
    shelf_blocks: list[ShelfBlockSource]
    placements: list[PlacementSource]


class ProductSource(SourceModel):
    id: int | str
    name: str
    category: str
    unit: str

    @property
    def external_id(self) -> str:
        return str(self.id)


class ProductMappingSource(SourceModel):
    products: list[ProductSource]


class SourceBundle(BaseModel):
    """Validated basic source documents."""

    store: StoreSource
    products: ProductMappingSource


def load_sources(store_path: str | Path, product_path: str | Path) -> SourceBundle:
    """Read both source documents without performing database work."""

    store_data = _read_json(
        Path(store_path), missing_category="REAL_STORE_SOURCE_NOT_FOUND"
    )
    product_data = _read_json(
        Path(product_path), missing_category="SOURCE_FILE_NOT_FOUND"
    )
    try:
        return SourceBundle(
            store=StoreSource.model_validate(store_data),
            products=ProductMappingSource.model_validate(product_data),
        )
    except ValidationError as error:
        raise SourceLoadError(
            "INVALID_SOURCE_STRUCTURE",
            {"errors": error.errors(include_url=False)},
        ) from error


def _read_json(path: Path, *, missing_category: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise SourceLoadError(missing_category, {"path": str(path)}) from error
    except json.JSONDecodeError as error:
        raise SourceLoadError(
            "INVALID_SOURCE_STRUCTURE",
            {"path": str(path), "line": error.lineno, "column": error.colno},
        ) from error
