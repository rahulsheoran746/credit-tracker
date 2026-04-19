import pytest
from app.services.transaction_service import TransactionService
from app.schemas.transaction_schema import MemberQuery

MEMBER_INFO = {"name": "Ramesh", "phone": "9876543210", "village": "Bansur", "city": "Alwar", "state": "Rajasthan"}

SWEET_ITEM = {"item_id": 10, "name": "Laddu", "quantity_kg": 0.5, "rate_per_kg": 280.0, "amount": 140.0}

PAYLOAD = {
    "member": MEMBER_INFO,
    "transactions": [{
        "transaction_type": "sweets",
        "items": [SWEET_ITEM],
        "total_amount": 140.0,
        "amount_given": 100.0,
        "notes": None,
    }],
    "description": "Test",
    "transaction_date": "2026-04-19T10:00:00",
}


def test_get_or_create_member_existing(mock_conn, mock_cursor):
    mock_cursor.fetchone.return_value = (3,)
    assert TransactionService(mock_conn).get_or_create_member(MEMBER_INFO) == 3


def test_get_or_create_member_new(mock_conn, mock_cursor):
    mock_cursor.fetchone.side_effect = [None, (7,)]
    assert TransactionService(mock_conn).get_or_create_member(MEMBER_INFO) == 7


def test_insert_transaction_returns_id(mock_conn, mock_cursor):
    mock_cursor.fetchone.return_value = (10,)
    assert TransactionService(mock_conn).insert_transaction(1, 500.0, 200.0) == 10


def test_process_payload_success(mock_conn, mock_cursor):
    mock_cursor.fetchone.side_effect = [(2,), (15,)]  # member exists, transaction inserted
    result = TransactionService(mock_conn).process_transaction_payload(PAYLOAD)
    assert result == {"status": "success", "member_id": 2, "transactions_processed": 1}
    mock_conn.commit.assert_called_once()


def test_process_payload_rollback_on_error(mock_conn, mock_cursor):
    mock_cursor.fetchone.side_effect = [(2,), Exception("DB error")]
    with pytest.raises(Exception, match="DB error"):
        TransactionService(mock_conn).process_transaction_payload(PAYLOAD)
    mock_conn.rollback.assert_called_once()
    mock_conn.commit.assert_not_called()


def test_get_member_transactions_found(mock_conn, mock_cursor):
    mock_cursor.fetchone.return_value = (
        "Ramesh", "9876543210", 500.0, 200.0, 300.0,
        [{"transaction_id": 1, "transaction_date": "2026-04-19T10:00:00",
          "total_amount": 500.0, "amount_paid": 200.0, "remaining_amount": 300.0,
          "items": [SWEET_ITEM]}]
    )
    result = TransactionService(mock_conn).get_member_transactions(
        MemberQuery(name="Ramesh", phone="9876543210")
    )
    assert result is not None
    assert result.name == "Ramesh"
    assert result.total_amount == 500.0
    assert result.remaining_amount == 300.0


def test_get_member_transactions_not_found(mock_conn, mock_cursor):
    mock_cursor.fetchone.return_value = None
    result = TransactionService(mock_conn).get_member_transactions(
        MemberQuery(name="Unknown", phone="0000000000")
    )
    assert result is None
