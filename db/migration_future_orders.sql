-- Migration: add Future Orders feature.
-- Run on existing DBs (init.sql is skipped once the volume has data).
--
-- Apply with:
--   docker exec -i shiv-postgres psql -U shiv_credit_tracker -d shiv_credit_tracker \
--     < db/migration_future_orders.sql

CREATE TABLE IF NOT EXISTS future_orders (
    id SERIAL PRIMARY KEY,
    member_id INT NOT NULL REFERENCES members(id),
    pickup_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    token_cash NUMERIC(10, 2) NOT NULL DEFAULT 0,
    token_upi  NUMERIC(10, 2) NOT NULL DEFAULT 0,
    notes TEXT,
    cancel_reason TEXT,
    refund_due NUMERIC(10, 2) NOT NULL DEFAULT 0,
    fulfilled_transaction_id INT REFERENCES transactions(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS future_order_items (
    id SERIAL PRIMARY KEY,
    future_order_id INT NOT NULL REFERENCES future_orders(id) ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES products(id),
    category VARCHAR(20) NOT NULL,
    name TEXT NOT NULL,
    unit VARCHAR(10) NOT NULL,
    quantity NUMERIC(10, 3) NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    amount NUMERIC(10, 2) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_future_orders_member         ON future_orders(member_id);
CREATE INDEX IF NOT EXISTS idx_future_orders_status_pickup  ON future_orders(status, pickup_date);
CREATE INDEX IF NOT EXISTS idx_future_order_items_order     ON future_order_items(future_order_id);
