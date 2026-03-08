import time

import win32con
import win32gui
import win32process

def _get_app_view_class():
    from pyvda import AppView

    return AppView


def _get_virtual_desktop_class():
    from pyvda import VirtualDesktop

    return VirtualDesktop


def _get_virtual_desktops():
    from src.desktop import get_virtual_desktops

    return get_virtual_desktops()


def get_window_desktop(hwnd: int) -> dict | None:
    """Resolve the virtual desktop metadata for a window handle."""
    try:
        desktop_id = str(_get_app_view_class()(hwnd).desktop_id)
    except Exception:
        return None

    for desktop in _get_virtual_desktops():
        if desktop["id"] == desktop_id:
            return desktop

    return {"id": desktop_id, "number": None, "name": None}


def go_to_window_desktop(hwnd: int) -> dict | None:
    """Switch to the desktop that owns the window when it is known."""
    desktop = get_window_desktop(hwnd)
    if not desktop or desktop["number"] is None:
        return desktop

    _get_virtual_desktop_class()(desktop["number"]).go()
    return desktop


def focus_window(hwnd: int) -> None:
    """Attempt to bring a window to the foreground after restoring it."""
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    else:
        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)

    win32gui.BringWindowToTop(hwnd)
    win32gui.SetForegroundWindow(hwnd)
    win32gui.SetActiveWindow(hwnd)


def jump_to_window(hwnd: int, desktop_settle_delay: float = 0.15) -> dict:
    """Move the user to the window's desktop and try to focus the window."""
    if not win32gui.IsWindow(hwnd):
        raise ValueError(f"Invalid hwnd: {hwnd}")

    desktop = go_to_window_desktop(hwnd)

    if desktop and desktop["number"] is not None and desktop_settle_delay > 0:
        time.sleep(desktop_settle_delay)

    focus_window(hwnd)
    _, pid = win32process.GetWindowThreadProcessId(hwnd)

    return {
        "hwnd": hwnd,
        "title": win32gui.GetWindowText(hwnd),
        "pid": pid,
        "desktop": desktop,
    }
