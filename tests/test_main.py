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

@patch('src.main.get_all_windows')
def test_read_windows(mock_get_all_windows):
    mock_get_all_windows.return_value = [{"hwnd": 123, "title": "Test Window", "desktop_id": "1"}]
    response = client.get("/windows")
    assert response.status_code == 200
    assert response.json() == [{"hwnd": 123, "title": "Test Window", "desktop_id": "1"}]

@patch('src.main.detect_terminals')
@patch('src.main.terminal_tracker.get_name')
def test_read_terminals(mock_get_name, mock_detect_terminals):
    mock_detect_terminals.return_value = [{"pid": 123, "name": "cmd.exe"}]
    mock_get_name.return_value = "Test Terminal"
    response = client.get("/terminals")
    assert response.status_code == 200
    assert response.json() == [{"pid": 123, "name": "cmd.exe", "custom_name": "Test Terminal"}]

@patch('src.main.terminal_tracker.get_name')
def test_read_terminal(mock_get_name):
    mock_get_name.return_value = "Test Terminal"
    response = client.get("/terminals/123")
    assert response.status_code == 200
    assert response.json() == {"pid": 123, "name": "Test Terminal"}

    mock_get_name.return_value = None
    response = client.get("/terminals/456")
    assert response.status_code == 200
    assert response.json() == {"pid": 456, "name": None}

@patch('src.main.terminal_tracker.set_name')
def test_update_terminal(mock_set_name):
    response = client.post("/terminals/123", json={"name": "New Terminal"})
    assert response.status_code == 200
    assert response.json() == {"pid": 123, "name": "New Terminal"}
    mock_set_name.assert_called_once_with(123, "New Terminal")
