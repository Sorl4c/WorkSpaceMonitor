import win32gui
import win32process
import re
from pyvda import AppView

TERMINAL_PROCESS_NAMES = {"windowsterminal.exe", "powershell.exe", "pwsh.exe", "cmd.exe", "alacritty.exe"}

def clean_terminal_title(title: str) -> str:
    """Extrae el nombre del proyecto o comando relevante de un título de terminal."""
    # 1. Patrón: ◇ Ready (Proyecto) -> Proyecto
    ready_match = re.search(r'◇\s+Ready\s*\((.*?)\)', title)
    if ready_match:
        return ready_match.group(1)
    
    # 2. Patrón: root@CAAB-PC: /ruta/hacia/algo -> /ruta/hacia/algo
    wsl_match = re.search(r':\s+(/[^\s]+)', title)
    if wsl_match:
        return wsl_match.group(1)
        
    # 3. Patrón: Administrador: Windows PowerShell - C:\Ruta -> C:\Ruta
    path_match = re.search(r'-\s+([a-zA-Z]:\\.*)', title)
    if path_match:
        return path_match.group(1)

    # 4. Si el título es muy genérico, mantenemos el original o devolvemos None
    if title in ["Windows PowerShell", "Command Prompt", "cmd.exe"]:
        return title
        
    return title

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
            
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        
        # Identificar si es una terminal para limpiar el nombre
        clean_name = title
        try:
            import psutil
            pname = psutil.Process(pid).name().lower()
            if pname in TERMINAL_PROCESS_NAMES:
                clean_name = clean_terminal_title(title)
        except:
            pass
            
        windows.append({
            "hwnd": hwnd,
            "title": title,
            "clean_name": clean_name, # Nuevo campo para el Dashboard
            "desktop_id": desktop_id,
            "pid": pid
        })
        
    win32gui.EnumWindows(enum_handler, None)
    return windows
