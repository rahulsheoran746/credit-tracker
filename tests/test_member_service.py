import pytest
from app.services.member_service import create_or_get_member
from app.schemas.member_schema import MemberCreate


def _member(phone="9876543210", name="Ramesh Kumar"):
    return MemberCreate(name=name, phone=phone, village="Bansur", city="Alwar", state="Rajasthan")


def test_returns_existing_member(mock_conn, mock_cursor):
    mock_cursor.fetchone.return_value = (5,)
    result = create_or_get_member(mock_conn, _member())
    assert result == {"id": 5, "message": "Existing member returned"}
    mock_conn.commit.assert_not_called()


def test_creates_new_member(mock_conn, mock_cursor):
    mock_cursor.fetchone.side_effect = [None, (1,)]
    result = create_or_get_member(mock_conn, _member())
    assert result == {"id": 1, "message": "New member created"}
    mock_conn.commit.assert_called_once()


def test_invalid_phone_too_short(mock_conn):
    with pytest.raises(ValueError, match="10 digits"):
        create_or_get_member(mock_conn, _member(phone="12345"))


def test_invalid_phone_non_digits(mock_conn):
    with pytest.raises(ValueError, match="10 digits"):
        create_or_get_member(mock_conn, _member(phone="98765abcde"))


def test_invalid_phone_too_long(mock_conn):
    with pytest.raises(ValueError, match="10 digits"):
        create_or_get_member(mock_conn, _member(phone="98765432101"))


def test_empty_name_raises(mock_conn):
    with pytest.raises(ValueError, match="Name cannot be empty"):
        create_or_get_member(mock_conn, _member(name="   "))
