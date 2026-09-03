CREATE FUNCTION set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

CREATE TABLE stores (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    external_id TEXT NOT NULL,
    name TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT pk_stores PRIMARY KEY (id),
    CONSTRAINT uq_stores_external_id UNIQUE (external_id)
);

CREATE TABLE navigation_nodes (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    store_id UUID NOT NULL,
    external_id TEXT NOT NULL,
    node_type TEXT NOT NULL,
    x_m NUMERIC(8, 3) NOT NULL,
    y_m NUMERIC(8, 3) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT pk_navigation_nodes PRIMARY KEY (id),
    CONSTRAINT uq_navigation_nodes_store_external_id
        UNIQUE (store_id, external_id),
    CONSTRAINT uq_navigation_nodes_store_id UNIQUE (store_id, id),
    CONSTRAINT chk_navigation_nodes_node_type
        CHECK (node_type IN ('giris', 'cikis', 'kavsak', 'raf_onu', 'kasa')),
    CONSTRAINT fk_navigation_nodes_store
        FOREIGN KEY (store_id) REFERENCES stores (id) ON DELETE NO ACTION
);

CREATE TABLE aisles (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    store_id UUID NOT NULL,
    external_id TEXT NOT NULL,
    name TEXT NOT NULL,
    aisle_number INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT pk_aisles PRIMARY KEY (id),
    CONSTRAINT uq_aisles_store_external_id UNIQUE (store_id, external_id),
    CONSTRAINT uq_aisles_store_aisle_number UNIQUE (store_id, aisle_number),
    CONSTRAINT uq_aisles_store_id UNIQUE (store_id, id),
    CONSTRAINT chk_aisles_positive_number
        CHECK (aisle_number IS NULL OR aisle_number > 0),
    CONSTRAINT fk_aisles_store
        FOREIGN KEY (store_id) REFERENCES stores (id) ON DELETE NO ACTION
);

CREATE TABLE products (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    store_id UUID NOT NULL,
    external_id TEXT NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT pk_products PRIMARY KEY (id),
    CONSTRAINT uq_products_store_external_id UNIQUE (store_id, external_id),
    CONSTRAINT uq_products_store_id UNIQUE (store_id, id),
    CONSTRAINT fk_products_store
        FOREIGN KEY (store_id) REFERENCES stores (id) ON DELETE NO ACTION
);

CREATE TABLE navigation_edges (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    store_id UUID NOT NULL,
    from_node_id UUID NOT NULL,
    to_node_id UUID NOT NULL,
    distance_m NUMERIC(8, 3) NOT NULL,
    is_bidirectional BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT pk_navigation_edges PRIMARY KEY (id),
    CONSTRAINT uq_navigation_edges_store_from_to
        UNIQUE (store_id, from_node_id, to_node_id),
    CONSTRAINT chk_navigation_edges_positive_distance CHECK (distance_m > 0),
    CONSTRAINT chk_navigation_edges_distinct_nodes
        CHECK (from_node_id <> to_node_id),
    CONSTRAINT chk_navigation_edges_canonical_bidirectional
        CHECK (NOT is_bidirectional OR from_node_id < to_node_id),
    CONSTRAINT fk_navigation_edges_store
        FOREIGN KEY (store_id) REFERENCES stores (id) ON DELETE NO ACTION,
    CONSTRAINT fk_navigation_edges_from_node
        FOREIGN KEY (store_id, from_node_id)
        REFERENCES navigation_nodes (store_id, id) ON DELETE NO ACTION,
    CONSTRAINT fk_navigation_edges_to_node
        FOREIGN KEY (store_id, to_node_id)
        REFERENCES navigation_nodes (store_id, id) ON DELETE NO ACTION
);

CREATE TABLE shelf_blocks (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    store_id UUID NOT NULL,
    aisle_id UUID NOT NULL,
    access_node_id UUID NOT NULL,
    external_id TEXT NOT NULL,
    x_m NUMERIC(8, 3) NOT NULL,
    y_m NUMERIC(8, 3) NOT NULL,
    size_x_m NUMERIC(8, 3) NOT NULL,
    size_y_m NUMERIC(8, 3) NOT NULL,
    facing TEXT NOT NULL,
    side_description TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT pk_shelf_blocks PRIMARY KEY (id),
    CONSTRAINT uq_shelf_blocks_store_external_id UNIQUE (store_id, external_id),
    CONSTRAINT uq_shelf_blocks_store_id UNIQUE (store_id, id),
    CONSTRAINT chk_shelf_blocks_positive_size_x CHECK (size_x_m > 0),
    CONSTRAINT chk_shelf_blocks_positive_size_y CHECK (size_y_m > 0),
    CONSTRAINT chk_shelf_blocks_facing
        CHECK (facing IN ('+x', '-x', '+y', '-y', 'open')),
    CONSTRAINT fk_shelf_blocks_store
        FOREIGN KEY (store_id) REFERENCES stores (id) ON DELETE NO ACTION,
    CONSTRAINT fk_shelf_blocks_aisle
        FOREIGN KEY (store_id, aisle_id)
        REFERENCES aisles (store_id, id) ON DELETE NO ACTION,
    CONSTRAINT fk_shelf_blocks_access_node
        FOREIGN KEY (store_id, access_node_id)
        REFERENCES navigation_nodes (store_id, id) ON DELETE NO ACTION
);

CREATE TABLE shelf_levels (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    store_id UUID NOT NULL,
    shelf_block_id UUID NOT NULL,
    code TEXT NOT NULL,
    level_order INTEGER NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT pk_shelf_levels PRIMARY KEY (id),
    CONSTRAINT uq_shelf_levels_block_code UNIQUE (shelf_block_id, code),
    CONSTRAINT uq_shelf_levels_block_order UNIQUE (shelf_block_id, level_order),
    CONSTRAINT uq_shelf_levels_block_id UNIQUE (shelf_block_id, id),
    CONSTRAINT chk_shelf_levels_positive_order CHECK (level_order > 0),
    CONSTRAINT fk_shelf_levels_shelf_block
        FOREIGN KEY (store_id, shelf_block_id)
        REFERENCES shelf_blocks (store_id, id) ON DELETE CASCADE
);

CREATE TABLE product_placements (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    store_id UUID NOT NULL,
    product_id UUID NOT NULL,
    shelf_block_id UUID NOT NULL,
    slot_code TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT pk_product_placements PRIMARY KEY (id),
    CONSTRAINT uq_product_placements_store_product_block
        UNIQUE (store_id, product_id, shelf_block_id),
    CONSTRAINT uq_product_placements_block_id UNIQUE (shelf_block_id, id),
    CONSTRAINT fk_product_placements_product
        FOREIGN KEY (store_id, product_id)
        REFERENCES products (store_id, id) ON DELETE NO ACTION,
    CONSTRAINT fk_product_placements_shelf_block
        FOREIGN KEY (store_id, shelf_block_id)
        REFERENCES shelf_blocks (store_id, id) ON DELETE NO ACTION
);

CREATE TABLE product_placement_levels (
    placement_id UUID NOT NULL,
    shelf_level_id UUID NOT NULL,
    shelf_block_id UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT pk_product_placement_levels
        PRIMARY KEY (placement_id, shelf_level_id),
    CONSTRAINT fk_product_placement_levels_placement
        FOREIGN KEY (shelf_block_id, placement_id)
        REFERENCES product_placements (shelf_block_id, id) ON DELETE CASCADE,
    CONSTRAINT fk_product_placement_levels_shelf_level
        FOREIGN KEY (shelf_block_id, shelf_level_id)
        REFERENCES shelf_levels (shelf_block_id, id) ON DELETE NO ACTION
);

CREATE TRIGGER trg_stores_set_updated_at
BEFORE UPDATE ON stores
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_navigation_nodes_set_updated_at
BEFORE UPDATE ON navigation_nodes
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_navigation_edges_set_updated_at
BEFORE UPDATE ON navigation_edges
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_aisles_set_updated_at
BEFORE UPDATE ON aisles
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_shelf_blocks_set_updated_at
BEFORE UPDATE ON shelf_blocks
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_shelf_levels_set_updated_at
BEFORE UPDATE ON shelf_levels
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_products_set_updated_at
BEFORE UPDATE ON products
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_product_placements_set_updated_at
BEFORE UPDATE ON product_placements
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE INDEX ix_navigation_nodes_store_node_type
    ON navigation_nodes (store_id, node_type);

CREATE INDEX ix_navigation_edges_store_to_node
    ON navigation_edges (store_id, to_node_id);

CREATE INDEX ix_shelf_blocks_store_aisle
    ON shelf_blocks (store_id, aisle_id);

CREATE INDEX ix_shelf_blocks_store_access_node
    ON shelf_blocks (store_id, access_node_id);

CREATE INDEX ix_products_store_category
    ON products (store_id, category);

CREATE INDEX ix_product_placement_levels_block_level
    ON product_placement_levels (shelf_block_id, shelf_level_id);
