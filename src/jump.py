import logging
import time

logger = logging.getLogger(__name__)

try:
    import win32con
    import win32gui
    import win32process
except Exception:  # pragma: no cover
    win32con = None
    win32gui = None
    win32process = None


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
    try:
        desktop_id = str(_get_app_view_class()(hwnd).desktop_id)
    except Exception:
        return None
    for desktop in _get_virtual_desktops():
        if desktop["id"] == desktop_id:
            return desktop
    return {"id": desktop_id, "number": None, "name": None}


def go_to_window_desktop(hwnd: int) -> dict | None:
    desktop = get_window_desktop(hwnd)
    if not desktop or desktop["number"] is None:
        return desktop
    _get_virtual_desktop_class()(desktop["number"]).go()
    return desktop


def focus_window(hwnd: int) -> None:
    if win32gui is None or win32con is None:
        return
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    else:
        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
    win32gui.BringWindowToTop(hwnd)
    win32gui.SetForegroundWindow(hwnd)
    win32gui.SetActiveWindow(hwnd)


def jump_to_window(hwnd: int, desktop_settle_delay: float = 0.15) -> dict:
    if win32gui is None or win32process is None:
        raise RuntimeError("jump_to_window is only available on Windows")
    if not win32gui.IsWindow(hwnd):
        raise ValueError(f"Invalid hwnd: {hwnd}")

    desktop = go_to_window_desktop(hwnd)
    logger.info("jump_sequence desktop=%s hwnd=%s risk=taskbar_focus_flashing", desktop, hwnd)
    if desktop and desktop["number"] is not None and desktop_settle_delay > 0:
        time.sleep(desktop_settle_delay)
    focus_window(hwnd)
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    return {"hwnd": hwnd, "title": win32gui.GetWindowText(hwnd), "pid": pid, "desktop": desktop}
