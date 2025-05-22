# credit-tracker
table structures
-- CREATE TABLE IF NOT EXISTS sweets (
--     id SERIAL PRIMARY KEY,
--     name TEXT NOT NULL UNIQUE,
--     rate_per_kg NUMERIC(10, 2) NOT NULL,
--     description TEXT
-- );
-- INSERT INTO sweets (name, rate_per_kg, description) VALUES
-- ('Laddu', 280.00, 'Classic besan laddu'),
-- ('Boondi', 260.00, 'Pure Desi ghee besan boondi'),
-- ('Barfi', 400.00, 'Pure milk Mawa Barfi'),
-- ('Peda', 400.00, 'Milk-based peda'),
-- ('Kalakand', 400.00, 'Milk cake made with condensed milk'),
-- ('Besan barfi', 350.00, 'Pure Desi ghee besan burfi'),
-- ('Kaju katli', 700.00, 'Pure Kaju Katlis contains only Kaju'),
-- ('Rasgulla', 150.00, 'Soft and spongy rasgulla'),
-- ('Gulab Jamun', 160.00, 'Pure Ghee Gulab Jamun'),
-- ('Rajbhog', 180.00, 'Sponge rajbhog with kesar and pista'),
-- ('Ghee', 750.00, 'Pure desi ghee'),
-- ('Dahi', 60.00, 'Dahi'),
-- ('Bhujia', 200.00, 'Hand made Bhujia'),
-- ('Paneer', 300.00, 'Panner with high protein'),
-- ('Matar', 100.00, 'Green frosted pees')
-- ;

-- CREATE TABLE members (
--     id SERIAL PRIMARY KEY,
--     name VARCHAR(100) NOT NULL,
--     phone VARCHAR(15),
--     village VARCHAR(100),
--     city VARCHAR(100),
--     state VARCHAR(100),
--     UNIQUE(name, phone)
-- );

-- CREATE TABLE IF NOT EXISTS items (
--     id SERIAL PRIMARY KEY,
--     name TEXT UNIQUE NOT NULL  -- e.g., 'sweet', 'money_borrow', 'cattle_feed', 'bulk_items'
-- );


-- INSERT INTO items (name) VALUES 
-- ('sweets'),
-- ('money_borrow'),
-- ('cattle_feed'),
-- ('bulk_items'),
-- ('repay')
-- ON CONFLICT (name) DO NOTHING;


-- CREATE TABLE transactions (
--     id SERIAL PRIMARY KEY,
--     member_id INT REFERENCES members(id),
--     total_amount NUMERIC(10, 2) NOT NULL,
--     amount_paid NUMERIC(10, 2) NOT NULL,
--     remaining_amount NUMERIC(10, 2) GENERATED ALWAYS AS (total_amount - amount_paid) STORED,
--     description TEXT,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- CREATE TABLE transaction_sweets (
--     id SERIAL PRIMARY KEY,
--     transaction_id INT REFERENCES transactions(id) ON DELETE CASCADE,
--     total_amount NUMERIC(10, 2) NOT NULL,
--     amount_given NUMERIC(10, 2) NOT NULL,
--     remaining_amount NUMERIC(10, 2) NOT NULL,
--     items JSONB NOT NULL, -- List of sweet items with qty, rate, amount
--     notes TEXT
-- );





