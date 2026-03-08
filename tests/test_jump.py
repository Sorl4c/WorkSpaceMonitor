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


@patch("src.jump.time.sleep")
@patch("src.jump.win32process.GetWindowThreadProcessId", return_value=(1, 999))
@patch("src.jump.win32gui.GetWindowText", return_value="Editor")
@patch("src.jump.focus_window")
@patch("src.jump.go_to_window_desktop")
@patch("src.jump.win32gui.IsWindow", return_value=True)
def test_jump_to_window_switches_desktop_then_focuses_window(
    mock_is_window,
    mock_go_to_window_desktop,
    mock_focus_window,
    mock_get_window_text,
    mock_get_window_thread_process_id,
    mock_sleep,
):
    mock_go_to_window_desktop.return_value = {"id": "desktop-3", "number": 3, "name": "Desktop 3"}

    result = jump_to_window(12345)

    assert result == {
        "hwnd": 12345,
        "title": "Editor",
        "pid": 999,
        "desktop": {"id": "desktop-3", "number": 3, "name": "Desktop 3"},
    }
    mock_go_to_window_desktop.assert_called_once_with(12345)
    mock_sleep.assert_called_once_with(0.15)
    mock_focus_window.assert_called_once_with(12345)


@patch("src.jump.win32gui.IsWindow", return_value=False)
def test_jump_to_window_rejects_invalid_hwnd(mock_is_window):
    try:
        jump_to_window(0)
    except ValueError as exc:
        assert str(exc) == "Invalid hwnd: 0"
    else:
        raise AssertionError("Expected jump_to_window to raise ValueError")
