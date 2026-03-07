import win32gui
from pyvda import AppView

def get_all_windows() -> list[dict]:
    windows = []
    
    def enum_handler(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        
        title = win32gui.GetWindowText(hwnd)
        if not title:
            return
            
        try:
            app_view = AppView(hwnd)
            desktop_id = str(app_view.desktop_id)
        except Exception:
            desktop_id = None
            
        windows.append({
            "hwnd": hwnd,
            "title": title,
            "desktop_id": desktop_id
        })
        
    win32gui.EnumWindows(enum_handler, None)
    return windows
