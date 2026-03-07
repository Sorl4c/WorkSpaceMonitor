from src.window import get_all_windows

def test_get_all_windows():
    windows = get_all_windows()
    assert isinstance(windows, list)
    if len(windows) > 0:
        window = windows[0]
        assert "hwnd" in window
        assert "title" in window
        assert "desktop_id" in window
        assert "pid" in window
        assert isinstance(window["pid"], int)
