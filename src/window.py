import re

TERMINAL_PROCESS_NAMES = {"windowsterminal.exe", "powershell.exe", "pwsh.exe", "cmd.exe", "alacritty.exe"}

try:
    import win32gui
    import win32process
except Exception:  # pragma: no cover - windows only
    win32gui = None
    win32process = None

try:
    from pyvda import AppView
except Exception:  # pragma: no cover - windows only
    AppView = None


def clean_terminal_title(title: str) -> str:
    ready_match = re.search(r'◇\s+Ready\s*\((.*?)\)', title)
    if ready_match:
        return ready_match.group(1)
    wsl_match = re.search(r':\s+(/[^\s]+)', title)
    if wsl_match:
        return wsl_match.group(1)
    path_match = re.search(r'-\s+([a-zA-Z]:\\.*)', title)
    if path_match:
        return path_match.group(1)
    return title


def get_all_windows() -> list[dict]:
    if win32gui is None or win32process is None:
        return []

    windows = []

    def enum_handler(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        if not title:
            return
        try:
            desktop_id = str(AppView(hwnd).desktop_id) if AppView else None
        except Exception:
            desktop_id = None

        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process_name = None
        clean_name = title
        try:
            import psutil

            process_name = psutil.Process(pid).name()
            if process_name.lower() in TERMINAL_PROCESS_NAMES:
                clean_name = clean_terminal_title(title)
        except Exception:
            pass

        rect = None
        try:
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            rect = {"x": left, "y": top, "width": max(right - left, 0), "height": max(bottom - top, 0)}
        except Exception:
            rect = None

        windows.append({
            "hwnd": hwnd,
            "title": title,
            "clean_name": clean_name,
            "desktop_id": desktop_id,
            "pid": pid,
            "process_name": process_name,
            "rect": rect,
        })

    win32gui.EnumWindows(enum_handler, None)
    return windows
