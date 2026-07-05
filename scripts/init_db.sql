-- init_db.sql — Day 04 eComBot seed schema
-- Runs once on first Postgres container start.
-- Idempotent: all statements use IF NOT EXISTS / ON CONFLICT DO NOTHING.

-- ── Bookings ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    order_id      VARCHAR(20)  PRIMARY KEY,
    carrier   VARCHAR(20)  NOT NULL,
    eta  DATE         NOT NULL,
    status          VARCHAR(20)  NOT NULL DEFAULT 'Confirmed',
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ── Products ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    product_id    VARCHAR(20) NOT NULL,
    product_name          VARCHAR(50) NOT NULL,
    category           VARCHAR(50) NOT NULL,
    price_usd        NUMERIC(10,2) NOT NULL,
    PRIMARY KEY (product_id)
);

-- ── Durable conversation history ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS session_history (
    id          BIGSERIAL    PRIMARY KEY,
    session_id  VARCHAR(100) NOT NULL,
    user_id     VARCHAR(100) NOT NULL,
    role        VARCHAR(20)  NOT NULL,   -- 'user' | 'model'
    content     TEXT         NOT NULL,
    tool_calls  JSONB,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_sh_session ON session_history (session_id, created_at);

-- ── orders seed data ─────────────────────────────────────────────────────
INSERT INTO orders (order_id, status, eta, carrier)
VALUES
    ('ORD-001', 'Shipped', '2026-06-05', 'BlueDart'),
    ('ORD-002', 'Processing', '2026-06-07', 'DTDC'),
    ('ORD-003', 'Delivered', '2026-05-30', 'FedEx')
ON CONFLICT (order_id) DO NOTHING;

-- ── products seed data ──────────────────────────────────────────────────────
INSERT INTO products (product_id, product_name, category, price_usd)
VALUES
    ('PROD-001', 'Laptop', 'Electronics', 1200.00),
    ('PROD-002', 'Smartphone', 'Electronics', 800.00),
    ('PROD-003', 'Headphones', 'Electronics', 150.00)
ON CONFLICT (product_id) DO NOTHING;