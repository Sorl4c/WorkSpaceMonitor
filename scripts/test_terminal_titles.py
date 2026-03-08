import win32gui
import win32process
import psutil
import os

TERMINAL_PROCESS_NAMES = ["windowsterminal.exe", "powershell.exe", "pwsh.exe", "cmd.exe", "alacritty.exe"]

def test_terminal_titles():
    print(f"{'PID':<8} | {'Process Name':<20} | {'Window Title'}")
    print("-" * 80)
    
    # Get all windows
    def enum_handler(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        
        title = win32gui.GetWindowText(hwnd)
        if not title:
            return
            
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        
        try:
            proc = psutil.Process(pid)
            pname = proc.name().lower()
            
            if pname in TERMINAL_PROCESS_NAMES:
                cwd = "N/A"
                try:
                    cwd = proc.cwd()
                except: pass
                
                print(f"{pid:<8} | {pname:<20} | {title}")
                print(f"{' ':<8} | {'[psutil.cwd()]':<20} | {cwd}")
                print("-" * 80)
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    win32gui.EnumWindows(enum_handler, None)

if __name__ == "__main__":
    test_terminal_titles()
