-- Runs automatically when the PostgreSQL container starts for the first time.
-- If the volume already has data this file is skipped entirely.

CREATE TABLE IF NOT EXISTS members (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(15),
    village VARCHAR(100),
    city VARCHAR(100),
    state VARCHAR(100),
    UNIQUE(name, phone)
);

CREATE TABLE IF NOT EXISTS sweets (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    rate_per_kg NUMERIC(10, 2) NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    member_id INT NOT NULL REFERENCES members(id),
    total_amount NUMERIC(10, 2) NOT NULL,
    amount_paid NUMERIC(10, 2) NOT NULL,
    remaining_amount NUMERIC(10, 2) GENERATED ALWAYS AS (total_amount - amount_paid) STORED,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transaction_sweets (
    id SERIAL PRIMARY KEY,
    transaction_id INT REFERENCES transactions(id) ON DELETE CASCADE,
    total_amount NUMERIC(10, 2) NOT NULL,
    amount_given NUMERIC(10, 2) NOT NULL,
    remaining_amount NUMERIC(10, 2) NOT NULL,
    items JSONB NOT NULL,
    notes TEXT
);

INSERT INTO items (name) VALUES
('sweets'), ('money_borrow'), ('cattle_feed'), ('bulk_items'), ('repay')
ON CONFLICT (name) DO NOTHING;

INSERT INTO sweets (name, rate_per_kg, description) VALUES
('Barfi', 400.00, 'Pure milk Mawa Barfi'),
('Besan barfi', 350.00, 'Pure Desi ghee besan burfi'),
('Bhujia', 200.00, 'Hand made Bhujia'),
('Boondi', 260.00, 'Pure Desi ghee besan boondi'),
('Dahi', 60.00, 'Dahi'),
('Ghee', 750.00, 'Pure desi ghee'),
('Gulab Jamun', 160.00, 'Pure Ghee Gulab Jamun'),
('Kaju katli', 700.00, 'Pure Kaju Katlis contains only Kaju'),
('Kalakand', 400.00, 'Milk cake made with condensed milk'),
('Laddu', 280.00, 'Classic besan laddu'),
('Matar', 100.00, 'Green frosted pees'),
('Paneer', 300.00, 'Panner with high protein'),
('Peda', 400.00, 'Milk-based peda'),
('Rajbhog', 180.00, 'Sponge rajbhog with kesar and pista'),
('Rasgulla', 150.00, 'Soft and spongy rasgulla')
ON CONFLICT (name) DO NOTHING;
