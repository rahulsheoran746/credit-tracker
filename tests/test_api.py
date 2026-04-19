MEMBER_PAYLOAD = {
    "name": "Ramesh Kumar",
    "phone": "9876543210",
    "village": "Bansur",
    "city": "Alwar",
    "state": "Rajasthan",
}

TRANSACTION_PAYLOAD = {
    "member": MEMBER_PAYLOAD,
    "transactions": [{
        "transaction_type": "sweets",
        "items": [{"item_id": 10, "name": "Laddu", "quantity_kg": 0.5, "rate_per_kg": 280.0, "amount": 140.0}],
        "total_amount": 140.0,
        "amount_given": 100.0,
        "notes": "Partial payment",
    }],
    "transaction_date": "2026-04-19T10:30:00",
    "description": "April purchase",
}


# ── Health ────────────────────────────────────────────────────────────────────

def test_health_check(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "message" in resp.json()


# ── Sweets ────────────────────────────────────────────────────────────────────

def test_list_sweets(client, mock_cursor):
    mock_cursor.fetchall.return_value = [(1, "Barfi", 400.0, "Pure milk Mawa Barfi")]
    resp = client.get("/sweets")
    assert resp.status_code == 200
    assert resp.json()[0]["name"] == "Barfi"


def test_calculate_amount(client, mock_cursor):
    mock_cursor.fetchone.return_value = (10, "Laddu", 280.0, "Classic besan laddu")
    resp = client.get("/sweets/10/calculate-amount?quantity=0.5")
    assert resp.status_code == 200
    assert resp.json()["amount"] == 140.0


def test_calculate_amount_sweet_not_found(client, mock_cursor):
    mock_cursor.fetchone.return_value = None
    resp = client.get("/sweets/999/calculate-amount?quantity=1")
    assert resp.status_code == 404


def test_calculate_quantity(client, mock_cursor):
    mock_cursor.fetchone.return_value = (10, "Laddu", 280.0, "Classic besan laddu")
    resp = client.get("/sweets/10/calculate-quantity?amount=140")
    assert resp.status_code == 200
    assert resp.json()["quantity"] == 0.5


def test_calculate_quantity_sweet_not_found(client, mock_cursor):
    mock_cursor.fetchone.return_value = None
    resp = client.get("/sweets/999/calculate-quantity?amount=100")
    assert resp.status_code == 404


# ── Members ───────────────────────────────────────────────────────────────────

def test_create_member(client, mock_cursor):
    mock_cursor.fetchone.side_effect = [None, (1,)]
    resp = client.post("/members", json=MEMBER_PAYLOAD)
    assert resp.status_code == 200
    assert resp.json()["message"] == "New member created"


def test_get_existing_member(client, mock_cursor):
    mock_cursor.fetchone.return_value = (5,)
    resp = client.post("/members", json=MEMBER_PAYLOAD)
    assert resp.status_code == 200
    assert resp.json()["id"] == 5


def test_create_member_invalid_phone(client):
    resp = client.post("/members", json={**MEMBER_PAYLOAD, "phone": "123"})
    assert resp.status_code == 422


def test_create_member_empty_name(client):
    resp = client.post("/members", json={**MEMBER_PAYLOAD, "name": "   "})
    assert resp.status_code == 422


# ── Transactions ──────────────────────────────────────────────────────────────

def test_process_transaction(client, mock_cursor):
    mock_cursor.fetchone.side_effect = [(2,), (10,)]
    resp = client.post("/transactions/", json=TRANSACTION_PAYLOAD)
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
    assert resp.json()["member_id"] == 2


def test_get_member_transactions(client, mock_cursor):
    mock_cursor.fetchone.return_value = (
        "Ramesh Kumar", "9876543210", 140.0, 100.0, 40.0,
        [{"transaction_id": 1, "transaction_date": "2026-04-19T10:30:00",
          "total_amount": 140.0, "amount_paid": 100.0, "remaining_amount": 40.0,
          "items": [{"item_id": 10, "name": "Laddu", "quantity_kg": 0.5,
                     "rate_per_kg": 280.0, "amount": 140.0}]}]
    )
    resp = client.post("/member/transactions", json={"name": "Ramesh Kumar", "phone": "9876543210"})
    assert resp.status_code == 200
    assert resp.json()["remaining_amount"] == 40.0


def test_get_member_transactions_not_found(client, mock_cursor):
    mock_cursor.fetchone.return_value = None
    resp = client.post("/member/transactions", json={"name": "Ghost", "phone": "0000000000"})
    assert resp.status_code == 404
