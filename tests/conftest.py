import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def mock_cursor():
    cursor = MagicMock()
    cursor.__enter__ = MagicMock(return_value=cursor)
    cursor.__exit__ = MagicMock(return_value=False)
    return cursor


@pytest.fixture
def mock_conn(mock_cursor):
    conn = MagicMock()
    conn.cursor.return_value = mock_cursor
    return conn


@pytest.fixture
def client(mock_conn):
    from app.main import app
    from app.db import get_connection

    def override_get_connection():
        yield mock_conn

    app.dependency_overrides[get_connection] = override_get_connection
    with patch("app.main.init_pool"):
        with TestClient(app) as c:
            yield c
    app.dependency_overrides.clear()
