from app.services.sweet_service import SweetService

LADDU_ROW = (10, "Laddu", 280.00, "Classic besan laddu")
BARFI_ROW = (1, "Barfi", 400.00, "Pure milk Mawa Barfi")
LADDU_DICT = {"id": 10, "name": "Laddu", "rate_per_kg": 280.0, "description": "Classic besan laddu"}
BARFI_DICT = {"id": 1, "name": "Barfi", "rate_per_kg": 400.0, "description": "Pure milk Mawa Barfi"}


def test_get_all_sweets_returns_list(mock_conn, mock_cursor):
    mock_cursor.fetchall.return_value = [BARFI_ROW, LADDU_ROW]
    result = SweetService(mock_conn).get_all_sweets()
    assert result == [BARFI_DICT, LADDU_DICT]


def test_get_all_sweets_empty_catalog(mock_conn, mock_cursor):
    mock_cursor.fetchall.return_value = []
    assert SweetService(mock_conn).get_all_sweets() == []


def test_get_sweet_by_id_found(mock_conn, mock_cursor):
    mock_cursor.fetchone.return_value = LADDU_ROW
    assert SweetService(mock_conn).get_sweet_by_id(10) == LADDU_DICT


def test_get_sweet_by_id_not_found(mock_conn, mock_cursor):
    mock_cursor.fetchone.return_value = None
    assert SweetService(mock_conn).get_sweet_by_id(999) is None


def test_rate_per_kg_is_float(mock_conn, mock_cursor):
    mock_cursor.fetchone.return_value = LADDU_ROW
    result = SweetService(mock_conn).get_sweet_by_id(10)
    assert isinstance(result["rate_per_kg"], float)
