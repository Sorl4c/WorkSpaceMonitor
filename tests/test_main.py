from fastapi.testclient import TestClient
from src.main import app
from unittest.mock import patch

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "running", "message": "Workspace Monitor Daemon"}

@patch('src.main.get_virtual_desktops')
def test_read_desktops(mock_get_virtual_desktops):
    mock_get_virtual_desktops.return_value = [{"id": "1", "number": 1, "name": "Desktop 1"}]
    response = client.get("/desktops")
    assert response.status_code == 200
    assert response.json() == [{"id": "1", "number": 1, "name": "Desktop 1"}]
