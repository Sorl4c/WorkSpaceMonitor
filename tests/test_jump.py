from unittest.mock import patch

from src.jump import get_window_desktop, jump_to_window


@patch("src.jump._get_virtual_desktops")
@patch("src.jump._get_app_view_class")
def test_get_window_desktop_returns_matching_desktop(mock_get_app_view_class, mock_get_virtual_desktops):
    mock_get_app_view_class.return_value.return_value.desktop_id = "desktop-2"
    mock_get_virtual_desktops.return_value = [
        {"id": "desktop-1", "number": 1, "name": "Desktop 1"},
        {"id": "desktop-2", "number": 2, "name": "Desktop 2"},
    ]

    desktop = get_window_desktop(100)

    assert desktop == {"id": "desktop-2", "number": 2, "name": "Desktop 2"}


@patch("src.jump.win32gui", None)
def test_jump_to_window_requires_windows_api():
    try:
        jump_to_window(1)
    except RuntimeError as exc:
        assert "only available on Windows" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError")
