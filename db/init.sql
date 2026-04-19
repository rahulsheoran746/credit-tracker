-- Runs automatically when the PostgreSQL container starts for the first time.
-- If the volume already has data this file is skipped entirely.

CREATE TABLE IF NOT EXISTS members (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    father_name VARCHAR(100),
    phone VARCHAR(15) NOT NULL UNIQUE,
    village VARCHAR(100),
    city VARCHAR(100),
    state VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    category VARCHAR(20) NOT NULL,           -- 'sweet' | 'cattle_feed' (extensible)
    name TEXT NOT NULL,
    unit VARCHAR(10) NOT NULL,               -- 'kg' | 'bag'
    unit_size NUMERIC(10, 2),                -- e.g. 50 for a 50kg bag; NULL for sweets
    price NUMERIC(10, 2) NOT NULL,           -- per unit
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category, name)
);

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    member_id INT NOT NULL REFERENCES members(id),
    type VARCHAR(20) NOT NULL DEFAULT 'sale',    -- 'sale' | 'product_repay' (more types later)
    total_amount NUMERIC(10, 2) NOT NULL,
    amount_paid NUMERIC(10, 2) NOT NULL,
    remaining_amount NUMERIC(10, 2) GENERATED ALWAYS AS (total_amount - amount_paid) STORED,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transaction_items (
    id SERIAL PRIMARY KEY,
    transaction_id INT REFERENCES transactions(id) ON DELETE CASCADE,
    total_amount NUMERIC(10, 2) NOT NULL,
    amount_given NUMERIC(10, 2) NOT NULL,
    remaining_amount NUMERIC(10, 2) NOT NULL,
    items JSONB NOT NULL,                    -- [{product_id, category, name, unit, quantity, price, amount}]
    notes TEXT
);

CREATE TABLE IF NOT EXISTS loans (
    id SERIAL PRIMARY KEY,
    member_id INT NOT NULL REFERENCES members(id),
    principal NUMERIC(10, 2) NOT NULL,
    interest_rate_monthly NUMERIC(5, 2) NOT NULL,
    borrow_date DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS loan_repayments (
    id SERIAL PRIMARY KEY,
    loan_id INT NOT NULL REFERENCES loans(id) ON DELETE CASCADE,
    amount NUMERIC(10, 2) NOT NULL,
    repay_date DATE NOT NULL DEFAULT CURRENT_DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_loans_member      ON loans(member_id);
CREATE INDEX IF NOT EXISTS idx_loan_reps_loan    ON loan_repayments(loan_id);

INSERT INTO products (category, name, unit, unit_size, price, description) VALUES
('sweet', 'Barfi',        'kg',  NULL, 400.00, 'Pure milk Mawa Barfi'),
('sweet', 'Besan barfi',  'kg',  NULL, 350.00, 'Pure Desi ghee besan burfi'),
('sweet', 'Bhujia',       'kg',  NULL, 200.00, 'Hand made Bhujia'),
('sweet', 'Boondi',       'kg',  NULL, 260.00, 'Pure Desi ghee besan boondi'),
('sweet', 'Dahi',         'kg',  NULL,  60.00, 'Dahi'),
('sweet', 'Ghee',         'kg',  NULL, 750.00, 'Pure desi ghee'),
('sweet', 'Gulab Jamun',  'kg',  NULL, 160.00, 'Pure Ghee Gulab Jamun'),
('sweet', 'Kaju katli',   'kg',  NULL, 700.00, 'Pure Kaju Katlis contains only Kaju'),
('sweet', 'Kalakand',     'kg',  NULL, 400.00, 'Milk cake made with condensed milk'),
('sweet', 'Laddu',        'kg',  NULL, 280.00, 'Classic besan laddu'),
('sweet', 'Matar',        'kg',  NULL, 100.00, 'Green frosted pees'),
('sweet', 'Paneer',       'kg',  NULL, 300.00, 'Panner with high protein'),
('sweet', 'Peda',         'kg',  NULL, 400.00, 'Milk-based peda'),
('sweet', 'Rajbhog',      'kg',  NULL, 180.00, 'Sponge rajbhog with kesar and pista'),
('sweet', 'Rasgulla',     'kg',  NULL, 150.00, 'Soft and spongy rasgulla')
ON CONFLICT (category, name) DO NOTHING;
