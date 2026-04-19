# Credit Tracker

A backend API for tracking sweet shop sales, credit, and payments. Members (customers) can buy sweets on credit, make partial payments, and the system tracks their outstanding balance.

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10 |
| Framework | FastAPI 0.115 |
| Server | Uvicorn |
| Database | PostgreSQL 17 |
| DB Driver | psycopg2-binary |
| Validation | Pydantic v2 |
| Config | python-dotenv |
| Container | Docker (PostgreSQL only) |

---

## Project Structure

```
credit-tracker/
├── app/
│   ├── main.py                    # FastAPI app entry point, startup events
│   ├── db.py                      # Connection pool (ThreadedConnectionPool)
│   ├── config.py                  # Reads .env variables
│   ├── models/                    # Pydantic domain models
│   ├── schemas/                   # Request / response schemas
│   │   ├── member_schema.py
│   │   ├── transaction_schema.py
│   │   └── sweet_schema.py
│   ├── services/                  # Business logic layer
│   │   ├── member_service.py
│   │   ├── transaction_service.py
│   │   └── sweet_service.py
│   └── routes/                    # API endpoint definitions
│       ├── member_routes.py
│       ├── transaction_routes.py
│       └── sweet_routes.py
├── docker-compose.yaml            # PostgreSQL container setup
├── Dockerfile                     # App container (used for production deploy)
├── requirements.txt
└── .env                           # DB credentials (do not share publicly)
```

---

## Running on a New / Different Machine

No manual SQL steps needed. The `db/init.sql` file runs automatically when the PostgreSQL container starts for the first time, creating all tables and seeding the sweets catalog.

### Option A — Full Docker (recommended for new machines)

Everything runs in containers — no Python install needed on the host machine.

```bash
# 1. Install Docker
sudo apt-get install -y docker.io docker-compose
sudo systemctl start docker
sudo usermod -aG docker $USER
newgrp docker

# 2. Clone the repo
git clone <repo-url>
cd credit-tracker

# 3. Start everything (DB + app)
docker-compose up -d

# 4. Verify both containers are running
docker ps
```

App will be available at **http://localhost:8000**

> Tables and seed data are created automatically on first start via `db/init.sql`.
> On subsequent starts the init file is skipped — existing data is preserved.

### Option B — Local dev (DB in Docker, app via uvicorn)

Use this when you want hot-reload while writing code.

```bash
# Start only the database
docker-compose up -d postgres

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run the app
uvicorn app.main:app --reload --port 8000
```

---

## Prerequisites

- Python 3.10+
- Docker
- DBVisualizer (or any PostgreSQL client to run setup SQL)

---

## Local Setup — Step by Step

### 1. Clone the repository

```bash
git clone <repo-url>
cd credit-tracker
```

### 2. Create the `.env` file

Create a `.env` file in the project root with the following content:

```env
DB_HOST=localhost
DB_NAME=credit_tracker
DB_USER=credit_user
DB_PASSWORD=credit_pass123
DB_PORT=5433
```

> Port is `5433` because Docker maps the container's internal `5432` to `5433` on your machine.

### 3. Start PostgreSQL via Docker

```bash
# Start only the database container in background
sudo docker-compose up -d postgres

# Verify it is running and healthy
sudo docker ps | grep postgres-retail
```

You should see `(healthy)` in the output.

### 4. Connect DBVisualizer to the database

| Field | Value |
|---|---|
| Host | `localhost` |
| Port | `5433` |
| Database | `credit_tracker` |
| User | `credit_user` |
| Password | `credit_pass123` |

### 5. Run the database setup SQL

Open DBVisualizer (or any SQL client) and run the following SQL statements in order.

#### Create tables

```sql
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
```

#### Seed reference data

```sql
INSERT INTO items (name) VALUES
('sweets'),
('money_borrow'),
('cattle_feed'),
('bulk_items'),
('repay')
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
```

### 6. Create Python virtual environment and install dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
```

### 7. Run the server

```bash
uvicorn app.main:app --reload --port 8000
```

Server starts at: **http://localhost:8000**  
Swagger UI (interactive docs): **http://localhost:8000/docs**

---

## API Endpoints

### Health Check
```
GET /
```

### Members

| Method | Endpoint | Description |
|---|---|---|
| POST | `/members` | Create a new member or return existing (matched by name + phone) |

### Sweets

| Method | Endpoint | Description |
|---|---|---|
| GET | `/sweets` | List all sweets with price per kg |
| GET | `/sweets/{id}/calculate-amount` | Given quantity (kg), returns total amount |
| GET | `/sweets/{id}/calculate-quantity` | Given amount (₹), returns quantity in kg |

### Transactions

| Method | Endpoint | Description |
|---|---|---|
| POST | `/transactions/` | Record a sweet purchase (supports partial payment) |
| POST | `/member/transactions` | Get full transaction history and outstanding balance for a member |

---

## Testing the Full Sweets Flow (Postman / curl)

Run these requests in order to test the complete flow.

### 1. Health check
```bash
curl -X GET http://localhost:8000/
```

### 2. List all sweets
```bash
curl -X GET http://localhost:8000/sweets
```

### 3. Calculate amount for a quantity
```bash
curl -X GET "http://localhost:8000/sweets/10/calculate-amount?quantity=0.5"
```

### 4. Calculate quantity for an amount
```bash
curl -X GET "http://localhost:8000/sweets/10/calculate-quantity?amount=200"
```

### 5. Create a member
```bash
curl -X POST http://localhost:8000/members \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ramesh Kumar",
    "phone": "9876543210",
    "village": "Bansur",
    "city": "Alwar",
    "state": "Rajasthan"
  }'
```

### 6. Record a sweet purchase (partial payment)
```bash
curl -X POST http://localhost:8000/transactions/ \
  -H "Content-Type: application/json" \
  -d '{
    "member": {
      "name": "Ramesh Kumar",
      "phone": "9876543210",
      "village": "Bansur",
      "city": "Alwar",
      "state": "Rajasthan"
    },
    "transactions": [
      {
        "transaction_type": "sweets",
        "items": [
          {
            "item_id": 10,
            "name": "Laddu",
            "quantity_kg": 0.5,
            "rate_per_kg": 280.00,
            "amount": 140.00
          },
          {
            "item_id": 1,
            "name": "Barfi",
            "quantity_kg": 0.25,
            "rate_per_kg": 400.00,
            "amount": 100.00
          }
        ],
        "total_amount": 240.00,
        "amount_given": 100.00,
        "notes": "Partial payment"
      }
    ],
    "transaction_date": "2026-04-19T10:30:00",
    "description": "April purchase"
  }'
```

### 7. Get member transaction history
```bash
curl -X POST http://localhost:8000/member/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ramesh Kumar",
    "phone": "9876543210"
  }'
```

---

## How the Connection Pool Works

Instead of opening a new database connection on every request (slow), the app maintains a pool of 1–10 reusable connections.

```
App starts → init_pool() creates 1 connection ready to use
Request arrives → borrows a connection from pool
Request finishes → connection returned to pool (not closed)
Next request → reuses the same connection instantly
```

This is configured in `app/db.py` using `psycopg2.pool.ThreadedConnectionPool`.

---

## Features Planned (Not Yet Implemented)

- [ ] Cattle feed transactions
- [ ] Money borrow / repay transactions
- [ ] Bulk item transactions
- [ ] Authentication / API key protection
- [ ] Payment recording against existing credit
