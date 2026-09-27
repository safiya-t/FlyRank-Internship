from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.database import check_db_connection

client = TestClient(app)


def test_check_db_connection_success():
    """Verify check_db_connection reports success when engine connects."""
    with patch("app.database.engine.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        success, message = check_db_connection()
        assert success is True
        assert "successful" in message.lower()


def test_check_db_connection_failure():
    """Verify check_db_connection reports clear error on failure."""
    with patch("app.database.engine.connect", side_effect=Exception("Connection refused")):
        success, message = check_db_connection()
        assert success is False
        assert "Connection refused" in message


def test_health_db_endpoint_success():
    """Verify GET /health/db returns 200 when database is connected."""
    with patch("app.main.check_db_connection", return_value=(True, "Database connection successful!")):
        response = client.get("/health/db")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "database": "connected"}


def test_health_db_endpoint_failure():
    """Verify GET /health/db returns 503 with descriptive detail when database fails."""
    with patch("app.main.check_db_connection", return_value=(False, "Database connection failed!")):
        response = client.get("/health/db")
        assert response.status_code == 503
        assert "Database connection failed!" in response.json()["detail"]
