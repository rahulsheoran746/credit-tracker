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

-- Future Orders: customer pre-books bulk items / cattle feed for a later pickup
-- date. Optional token money is held on the order row (not as a transaction)
-- and applied at fulfillment time.
CREATE TABLE IF NOT EXISTS future_orders (
    id SERIAL PRIMARY KEY,
    member_id INT NOT NULL REFERENCES members(id),
    pickup_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',     -- 'pending' | 'fulfilled' | 'cancelled'
    token_cash NUMERIC(10, 2) NOT NULL DEFAULT 0,
    token_upi  NUMERIC(10, 2) NOT NULL DEFAULT 0,
    notes TEXT,
    cancel_reason TEXT,
    refund_due NUMERIC(10, 2) NOT NULL DEFAULT 0,      -- set on fulfill if token > final bill, or on cancel
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
    price NUMERIC(10, 2) NOT NULL,                     -- locked at order creation
    amount NUMERIC(10, 2) NOT NULL                     -- price * quantity (snapshot)
);

CREATE INDEX IF NOT EXISTS idx_future_orders_member         ON future_orders(member_id);
CREATE INDEX IF NOT EXISTS idx_future_orders_status_pickup  ON future_orders(status, pickup_date);
CREATE INDEX IF NOT EXISTS idx_future_order_items_order     ON future_order_items(future_order_id);
INSERT INTO products (category, name, unit, unit_size, price, description) VALUES
  -- Cattle Feed
  ('cattle_feed', 'Tiwana Calf Starter Plus', 'bag', 25,   1000.00, 'Balanced starter feed for young calves; supports early growth and immunity.'),
  ('cattle_feed', 'Tiwana Calf Grower',       'bag', 50,   1200.00, 'For calves aged 3-6 months; builds stronger future dairy animals.'),
  ('cattle_feed', 'Tiwana 35 Protein',        'bag', 50,   1950.00, 'High-protein (35%) formulation for growing and high-demand animals.'),
  ('cattle_feed', 'Tiwana Heifer Dry',        'bag', 50,   1600.00, 'Nutritional support for first-time pregnant heifers.'),
  ('cattle_feed', 'Tiwana Dry Bovine',        'bag', 50,   1650.00, 'Formulated for the dry cow period before calving.'),
  ('cattle_feed', 'Tiwana T-20 Dry',          'bag', 50,   1950.00, 'Alternative dry-cow feed with balanced minerals.'),
  ('cattle_feed', 'Tiwana T-20 Fresher',      'bag', 50,   1800.00, 'Post-calving nutrition for fresh cows to boost early-lactation recovery.'),
  ('cattle_feed', 'Tiwana 8000',              'bag', 50,   1380.00, 'Balanced diet for milking animals yielding up to 18 L/day.'),
  ('cattle_feed', 'Tiwana Milk Plus',         'bag', 50,   1550.00, 'Enhanced formulation to improve milk yield in lactating animals.'),
  ('cattle_feed', 'Tiwana 10000',             'bag', 50,   1650.00, 'Premium milking range for high-yielding dairy animals.'),
  ('cattle_feed', 'Tiwana Silage Plus',       'bag', 50,   1100.00, 'Feed supplement for silage-based diets.'),
  ('cattle_feed', 'Tarragon Calf Care',       'bag', 25,   1000.00, 'Starter feed for young calves; promotes rumen development, immunity, and healthy early growth.'),
  ('cattle_feed', 'Tarragon Grow & Gain',     'bag', 50,   1800.00, 'Growth feed (~24% protein) for calves 4–9 months; supports weight gain, bone strength, and early maturity.'),
  ('cattle_feed', 'Tarragon Heifer Dry',      'bag', 50,   1600.00, 'Specialized feed for heifers and dry animals; improves reproductive health and prepares for calving.'),
  ('cattle_feed', 'Tarragon Healthy Mother',  'bag', 50,   2000.00, 'Formulated for pregnant cattle; supports fetal development and maintains body condition before calving.'),
  ('cattle_feed', 'Tarragon Milk Promax-30',  'bag', 50,   1650.00, 'High-protein (~30%) lactation feed; enhances milk yield, improves fat %, and supports overall productivity.'),
  ('cattle_feed', 'Tarragon Milk Turbo-40',   'bag', 50,   1850.00, 'Premium high-energy (~40%) feed for high-yielding animals; maximizes milk output and energy balance.'),
  ('cattle_feed', 'Tarragon Milk Max 20',     'bag', 50,   1450.00, 'Balanced (~20% protein) feed for regular milk production; maintains animal health and milk consistency.'),
  ('cattle_feed', 'Tarragon MILK CARE',       'bag', 50,   1550.00, 'Daily maintenance feed for lactating cattle; supports steady milk yield and digestive health.'),
  ('cattle_feed', 'Tarragon Milk Force-15',   'bag', 50,   1350.00, 'Cost-effective (~15% protein) feed for moderate milk producers; improves fat content and feed efficiency.'),
  ('cattle_feed', 'Tarragon Milk Boost-10',   'bag', 50,   1250.00, 'Economical (~10% protein) ration for low-yield animals; maintains production and improves milk quality.'),
  ('cattle_feed', 'Tarragon Milk Strength 50','bag', 50,   1150.00, 'Mineral-rich strength formula; enhances immunity, stamina, and supports recovery in weak animals.'),
  ('cattle_feed', 'Tarragon Ultra Buff',      'bag', 50,   1350.00, 'Bypass fat-based supplement; increases milk fat %, energy levels, and improves body condition.'),
  ('cattle_feed', 'Tarragon Mega Buff',       'bag', 50,   1350.00, 'Advanced bypass fat formula; boosts energy density, milk fat, and supports peak lactation performance.'),
  ('cattle_feed', 'Tarragon CremeFlex-20',    'bag', 50,   1400.00, 'Fat-enhancing (~20%) lactation feed; improves milk creaminess, fat %, and overall yield stability.'),
  ('cattle_feed', 'Tarragon CremeFlex-30',    'bag', 50,   1500.00, 'High-fat (~30%) formulation for superior milk fat and SNF; ideal for premium dairy output.'),
  ('cattle_feed', 'Moti Khal',                'bag', 48,   2100.00, 'Kachi Ghani khal'),
  ('cattle_feed', 'Kadi Khal',                'bag', 48,   1900.00, 'Gujarat khal'),
  ('cattle_feed', 'Bindola',                  'bag', 48,   2400.00, 'Cotton seeds for cattles'),

  -- Sweets
  ('sweet',       'Mawa Barfi',               'kg',  NULL,  400.00, 'Pure milk Mawa Barfi'),
  ('sweet',       'Besan barfi',              'kg',  NULL,  350.00, 'Pure Desi ghee besan burfi'),
  ('sweet',       'Bhujia',                   'kg',  NULL,  200.00, 'Hand made Bhujia'),
  ('sweet',       'Boondi',                   'kg',  NULL,  280.00, 'Pure Desi ghee besan boondi'),
  ('sweet',       'Dahi',                     'kg',  NULL,   60.00, 'Dahi'),
  ('sweet',       'Ghee',                     'kg',  NULL,  800.00, 'Pure desi ghee'),
  ('sweet',       'Gulab Jamun',              'kg',  NULL,  160.00, 'Pure Ghee Gulab Jamun'),
  ('sweet',       'Jalebi',                   'kg',  NULL,  300.00, 'Desi Ghee jalebi'),
  ('sweet',       'Kaju katli',               'kg',  NULL,  700.00, 'Pure Kaju Katlis contains only Kaju'),
  ('sweet',       'Kalakand',                 'kg',  NULL,  400.00, 'Milk cake made with condensed milk'),
  ('sweet',       'Laddu',                    'kg',  NULL,  300.00, 'Classic desi ghee besan boondi laddu'),
  ('sweet',       'Matar',                    'kg',  NULL,  100.00, 'Green frosted pees'),
  ('sweet',       'Paneer',                   'kg',  NULL,  300.00, 'Panner with high protein'),
  ('sweet',       'Peda',                     'kg',  NULL,  400.00, 'Milk-based peda'),
  ('sweet',       'Rajbhog',                  'kg',  NULL,  200.00, 'Sponge rajbhog with kesar and pista'),
  ('sweet',       'Rasgulla',                 'kg',  NULL,  150.00, 'Soft and spongy rasgulla'),
  ('sweet',       'Gajar Pankh',              'kg',  NULL,  500.00, 'Delicious Gajar Pankh with desi ghee'),
  ('sweet',       'Mawa',                     'kg',  NULL,  300.00, 'Pure milk mawa'),
  ('sweet',       'Gond Laddu',               'kg',  NULL,  400.00, 'Pure desi ghee gond ke laddu'),

  -- Wholesale / Bulk
  ('wholesale',   'Rasgulla Box',             'box', 20,   2050.00, '20kg bulk rasgulla for events and wholesale orders.'),
  ('wholesale',   'Gulab Jamun Box',          'box', 20,   2150.00, '20kg bulk gulab jamun for events and wholesale orders.'),
  ('wholesale',   'Dahi Box',                 'box', 15,   800.00,  '15kg bulk dahi for wholesale orders.'),
  ('wholesale',   'Rajbhog Box ',             'box', 20,   2650.00, '20kg bulk rajbhog for events and wholesale orders.'),
  ('wholesale',   'Safal Matar bag',          'box', 5,    450.00,  'Safal matar bag packed .'),
  ('wholesale',   'Rasmalai Tikki',           'box', 1,    8.00,    'Rasmalai tikki per piece.'),
  ('wholesale',   'Mawa',                     'box', 1,    300.00,  'Fikha mawa for halwa, gulabjamun.'),
  ('wholesale',   'Amul Cream',               'box', 1,    240.00,  'Fikha mawa for halwa, gulabjamun.'),
  ('wholesale',   'Amul Butter',              'box', 0.5,  290.00,  'Fikha mawa for halwa, gulabjamun.'),
  ('wholesale',   'Paneer Wholesale',         'box', 1,    300.00, 'Bulk paneer with rich protein.')
  ON CONFLICT (category, name) DO NOTHING;
