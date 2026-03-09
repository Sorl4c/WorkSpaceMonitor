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


@patch("src.jump.time.sleep")
@patch("src.jump.win32process.GetWindowThreadProcessId", return_value=(1, 999))
@patch("src.jump.win32gui.GetWindowText", return_value="Editor")
@patch("src.jump.focus_window", side_effect=Exception("foreground denied"))
@patch("src.jump.go_to_window_desktop")
@patch("src.jump.win32gui.IsWindow", return_value=True)
def test_jump_to_window_returns_partial_when_focus_fails(
    mock_is_window,
    mock_go_to_window_desktop,
    mock_focus_window,
    mock_get_window_text,
    mock_get_window_thread_process_id,
    mock_sleep,
):
    mock_go_to_window_desktop.return_value = {"id": "desktop-3", "number": 3, "name": "Desktop 3"}

    result = jump_to_window(12345)

    assert result["hwnd"] == 12345
    assert result["pid"] == 999
    assert result["focused"] is False
    assert "foreground denied" in result["focus_error"]
