import uiautomation as auto
import time
import psutil
import win32gui
import win32process
import win32con
import json

def get_window_list():
    """Get all visible windows with basic info."""
    windows = []
    def enum_handler(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                windows.append({"hwnd": hwnd, "title": title, "pid": pid})
    win32gui.EnumWindows(enum_handler, None)
    return windows

def get_z_order(hwnds):
    """Return map of hwnd -> z_index (0 is top)."""
    z_map = {}
    curr = win32gui.GetWindow(win32gui.GetForegroundWindow(), win32con.GW_HWNDFIRST)
    idx = 0
    while curr:
        if curr in hwnds:
            z_map[curr] = idx
            idx += 1
        curr = win32gui.GetWindow(curr, win32con.GW_HWNDNEXT)
    return z_map

def get_browser_context(hwnd, pname):
    """Fast browser context extraction."""
    start = time.time()
    context = {"active_url": None, "tabs": []}
    
    try:
        # Use ControlFromHandle for speed
        ctrl = auto.ControlFromHandle(hwnd)
        
        # 1. Active URL (Optimized search)
        # Search for Edit control - usually the first one at shallow depth is the address bar
        # We try to find it without deep recursion first
        addr = ctrl.EditControl(searchDepth=5, Name='Address and search bar')
        if not addr.Exists(0):
            # Fallback: find any Edit control that looks like a URL
            for edit in ctrl.FindAll(searchDepth=5, searchFilter={'ControlType': auto.ControlType.EditControl}):
                val = edit.GetValuePattern().Value
                if val and ('.' in val or val.startswith('http')):
                    context["active_url"] = val
                    break
        else:
            context["active_url"] = addr.GetValuePattern().Value
            
        # 2. Tabs (Shallow)
        # Finding all tabs is slow, so we only do it if it's the foreground window
        if hwnd == win32gui.GetForegroundWindow():
            tabs = ctrl.FindAll(searchDepth=8, searchFilter={'ControlType': auto.ControlType.TabItemControl})
            context["tabs"] = [t.Name for t in tabs[:10]] # Limit to 10 for speed
            
    except Exception:
        pass
        
    context["elapsed_ms"] = (time.time() - start) * 1000
    return context

def get_cli_context(pid):
    """Deep CLI context."""
    try:
        proc = psutil.Process(pid)
        children = proc.children(recursive=True)
        worker = None
        # Find the most 'interesting' leaf process
        for child in reversed(children):
            try:
                if child.name().lower() not in ["conhost.exe", "openconsole.exe", "wslhost.exe", "svchost.exe"]:
                    worker = {
                        "name": child.name(),
                        "cwd": child.cwd(),
                        "cmdline": child.cmdline()
                    }
                    break
            except: continue
            
        return {
            "cwd": proc.cwd(),
            "cmdline": proc.cmdline(),
            "worker": worker
        }
    except:
        return None

def main():
    print("--- Workspace Monitor: Advanced Granularity Prototype ---")
    
    all_windows = get_window_list()
    hwnds = [w['hwnd'] for w in all_windows]
    z_map = get_z_order(hwnds)
    fg_hwnd = win32gui.GetForegroundWindow()
    
    browsers = ["chrome.exe", "msedge.exe", "firefox.exe"]
    terminals = ["windowsterminal.exe", "cmd.exe", "pwsh.exe", "powershell.exe"]
    
    enriched_windows = []
    
    # Process top 10 windows for demo
    sorted_windows = sorted(all_windows, key=lambda x: z_map.get(x['hwnd'], 999))
    
    for w in sorted_windows[:15]:
        hwnd = w['hwnd']
        pid = w['pid']
        try:
            proc = psutil.Process(pid)
            pname = proc.name().lower()
        except: continue
        
        # Base metadata
        rect = win32gui.GetWindowRect(hwnd)
        w_data = {
            "hwnd": hwnd,
            "title": w['title'],
            "process": pname,
            "is_focused": (hwnd == fg_hwnd),
            "z_order": z_map.get(hwnd, -1),
            "rect": {"x": rect[0], "y": rect[1], "w": rect[2]-rect[0], "h": rect[3]-rect[1]}
        }
        
        # Browser Context
        if pname in browsers:
            # ONLY extract URL if it's high in Z-order or focused to save time
            if w_data['is_focused'] or w_data['z_order'] < 3:
                w_data['browser'] = get_browser_context(hwnd, pname)
        
        # CLI Context
        if pname in terminals:
            w_data['cli'] = get_cli_context(pid)
            
        enriched_windows.append(w_data)
        
    print(json.dumps(enriched_windows, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
