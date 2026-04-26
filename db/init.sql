-- Runs automatically when the PostgreSQL container starts for the first time.
-- If the volume already has data this file is skipped entirely.

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(15),
    role VARCHAR(20) NOT NULL DEFAULT 'worker',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    must_change_password BOOLEAN NOT NULL DEFAULT TRUE,
    token_version INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

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
    type VARCHAR(20) NOT NULL DEFAULT 'sale',    -- 'sale' | 'product_repay' | 'return' (more types later)
    total_amount NUMERIC(10, 2) NOT NULL,
    amount_paid NUMERIC(10, 2) NOT NULL,
    remaining_amount NUMERIC(10, 2) GENERATED ALWAYS AS (total_amount - amount_paid) STORED,
    cash_amount NUMERIC(10, 2) DEFAULT 0,         -- cash portion of amount_paid
    upi_amount  NUMERIC(10, 2) DEFAULT 0,         -- UPI portion (cash + upi must equal amount_paid)
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
    cash_amount NUMERIC(10, 2),                   -- how the principal was disbursed
    upi_amount  NUMERIC(10, 2),                   -- cash + upi must equal principal
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS loan_repayments (
    id SERIAL PRIMARY KEY,
    loan_id INT NOT NULL REFERENCES loans(id) ON DELETE CASCADE,
    amount NUMERIC(10, 2) NOT NULL,
    repay_date DATE NOT NULL DEFAULT CURRENT_DATE,
    cash_amount NUMERIC(10, 2) DEFAULT 0,         -- breakdown of the repayment
    upi_amount  NUMERIC(10, 2) DEFAULT 0,         -- cash + upi must equal amount
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
('sweet', 'Rasgulla',     'kg',  NULL, 150.00, 'Soft and spongy rasgulla'),

-- Cattle Feed (Tiwana Nutrition catalogue — prices are approximate dealer rates, adjust after import)
('cattle_feed', 'Tiwana Calf Starter Plus', 'bag', 50, 1400.00, 'Balanced starter feed for young calves; supports early growth and immunity.'),
('cattle_feed', 'Tiwana Calf Grower',       'bag', 50, 1300.00, 'For calves aged 3-6 months; builds stronger future dairy animals.'),
('cattle_feed', 'Tiwana 35 Protein',        'bag', 50, 1500.00, 'High-protein (35%) formulation for growing and high-demand animals.'),
('cattle_feed', 'Tiwana Heifer Dry',        'bag', 50, 1200.00, 'Nutritional support for first-time pregnant heifers.'),
('cattle_feed', 'Tiwana Dry Bovine',        'bag', 50, 1150.00, 'Formulated for the dry cow period before calving.'),
('cattle_feed', 'Tiwana T-20 Dry',          'bag', 50, 1150.00, 'Alternative dry-cow feed with balanced minerals.'),
('cattle_feed', 'Tiwana T-20 Fresher',      'bag', 50, 1250.00, 'Post-calving nutrition for fresh cows to boost early-lactation recovery.'),
('cattle_feed', 'Tiwana 8000',              'bag', 50, 1250.00, 'Balanced diet for milking animals yielding up to 18 L/day.'),
('cattle_feed', 'Tiwana Milk Plus',         'bag', 50, 1300.00, 'Enhanced formulation to improve milk yield in lactating animals.'),
('cattle_feed', 'Tiwana 10000',             'bag', 50, 1400.00, 'Premium milking range for high-yielding dairy animals.'),
('cattle_feed', 'Tiwana Silage Plus',       'bag', 50, 1100.00, 'Feed supplement for silage-based diets.'),

-- Wholesale / bulk boxes
('wholesale', 'Rasgulla Box',    'box', 20, 3000.00, '20kg bulk rasgulla for events and wholesale orders.'),
('wholesale', 'Gulab Jamun Box', 'box', 20, 3200.00, '20kg bulk gulab jamun for events and wholesale orders.'),
('wholesale', 'Dahi Box',        'box', 15,  900.00, '15kg bulk dahi for wholesale orders.')
ON CONFLICT (category, name) DO NOTHING;
