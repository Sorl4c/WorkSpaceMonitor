import uiautomation as auto
import time
import psutil
import win32gui
import win32process
import win32con

def get_browser_tabs():
    """Extract browser tabs and active URL."""
    browsers = ["chrome.exe", "msedge.exe", "firefox.exe"]
    browser_data = []
    
    # Get all windows first to handle Z-order later
    all_hwnds = []
    def enum_handler(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            all_hwnds.append(hwnd)
    win32gui.EnumWindows(enum_handler, None)

    for hwnd in all_hwnds:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            proc = psutil.Process(pid)
            if proc.name().lower() in browsers:
                title = win32gui.GetWindowText(hwnd)
                start_time = time.time()
                
                # UIA search
                window_control = auto.WindowControl(searchDepth=1, Name=title)
                if not window_control.Exists(0):
                    continue
                
                # 1. Get Active URL
                url = None
                # Search for Address bar
                addr = window_control.EditControl(searchDepth=10, Name='Address and search bar')
                if not addr.Exists(0):
                    addr = window_control.EditControl(searchDepth=10) # Fallback
                
                if addr.Exists(0):
                    try:
                        url = addr.GetValuePattern().Value
                    except:
                        pass
                
                # 2. Try to list tabs (Experimental)
                tabs = []
                tab_items = window_control.TabItemControl(searchDepth=10) # This might only find one
                # Usually tabs are children of a 'Tab' control or 'Pane'
                # Let's try to find all TabItems
                all_tabs = window_control.FindAll(searchDepth=10, searchFilter={'ControlType': auto.ControlType.TabItemControl})
                for t in all_tabs:
                    tabs.append(t.Name)

                elapsed = (time.time() - start_time) * 1000
                browser_data.append({
                    "hwnd": hwnd,
                    "browser": proc.name(),
                    "active_title": title,
                    "active_url": url,
                    "tabs": tabs,
                    "elapsed_ms": elapsed
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
            
    return browser_data

def get_z_order(hwnds):
    """Sort hwnds by Z-order (top to bottom)."""
    ordered = []
    curr = win32gui.GetWindow(win32gui.GetForegroundWindow(), win32con.GW_HWNDFIRST)
    while curr:
        if curr in hwnds:
            ordered.append(curr)
        curr = win32gui.GetWindow(curr, win32con.GW_HWNDNEXT)
    return ordered

def get_deep_cli_context():
    """Find terminals and their most 'interesting' child process."""
    terminal_procs = ["WindowsTerminal.exe", "cmd.exe", "pwsh.exe", "powershell.exe"]
    results = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] in terminal_procs:
            children = proc.children(recursive=True)
            # Filter children to find the 'leaf' worker (e.g., python, node, git)
            interesting_child = None
            for child in reversed(children):
                try:
                    if child.name().lower() not in ["conhost.exe", "openconsole.exe", "wslhost.exe"]:
                        interesting_child = {
                            "pid": child.pid,
                            "name": child.name(),
                            "cwd": child.cwd(),
                            "cmdline": child.cmdline()
                        }
                        break
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    continue
            
            results.append({
                "terminal_pid": proc.info['pid'],
                "terminal_name": proc.info['name'],
                "worker": interesting_child,
                "cwd": proc.cwd() if hasattr(proc, 'cwd') else None
            })
    return results

if __name__ == "__main__":
    print("--- Prototyping Browser Tabs & URLs ---")
    browsers = get_browser_tabs()
    for b in browsers:
        print(f"Browser: {b['browser']} | URL: {b['active_url']}")
        print(f"  Tabs ({len(b['tabs'])}): {b['tabs'][:5]}...")
        print(f"  Time: {b['elapsed_ms']:.2f}ms")

    print("\n--- Prototyping Deep CLI Context ---")
    cli_ctx = get_deep_cli_context()
    for c in cli_ctx:
        print(f"Terminal: {c['terminal_name']} ({c['terminal_pid']})")
        if c['worker']:
            print(f"  Active Worker: {c['worker']['name']} in {c['worker']['cwd']}")
            print(f"  Cmd: {' '.join(c['worker']['cmdline'][:5])}")
        else:
            print(f"  Idle (CWD: {c['cwd']})")

    print("\n--- Z-Order ---")
    hwnds = [b['hwnd'] for b in browsers]
    ordered = get_z_order(hwnds)
    print(f"Z-Order (top-most first): {ordered}")
