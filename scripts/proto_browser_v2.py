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
    
    # Get all windows
    all_hwnds = []
    def enum_handler(hwnd, _):
        all_hwnds.append(hwnd)
    win32gui.EnumWindows(enum_handler, None)
    
    print(f"Total HWNDs found: {len(all_hwnds)}")

    for hwnd in all_hwnds:
        if not win32gui.IsWindowVisible(hwnd):
            continue
            
        title = win32gui.GetWindowText(hwnd)
        if not title:
            continue
            
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            proc = psutil.Process(pid)
            pname = proc.name().lower()
            if pname in browsers:
                print(f"Found {pname} window: '{title}' (HWND: {hwnd})")
                start_time = time.time()
                
                # UIA search
                # We use the HWND directly to create the control, which is MUCH faster
                window_control = auto.ControlFromHandle(hwnd)
                
                # 1. Get Active URL
                url = None
                # Search for Address bar
                # In Edge/Chrome, it's an Edit control.
                # Sometimes it's deep, so we limit depth but use a specific name if possible
                addr = window_control.EditControl(searchDepth=10, Name='Address and search bar')
                if not addr.Exists(0):
                    # Localized version or different Edge version?
                    # Try finding by ControlType and see if it looks like a URL
                    edits = window_control.FindAll(searchDepth=10, searchFilter={'ControlType': auto.ControlType.EditControl})
                    for edit in edits:
                        val = edit.GetValuePattern().Value
                        if val and (val.startswith('http') or '.' in val):
                            url = val
                            break
                else:
                    url = addr.GetValuePattern().Value
                
                # 2. Tabs
                tabs = []
                # Finding all tabs can be slow, let's just find the first 10
                all_tabs = window_control.FindAll(searchDepth=10, searchFilter={'ControlType': auto.ControlType.TabItemControl})
                for t in all_tabs:
                    tabs.append(t.Name)

                elapsed = (time.time() - start_time) * 1000
                browser_data.append({
                    "hwnd": hwnd,
                    "browser": pname,
                    "active_title": title,
                    "active_url": url,
                    "tabs": tabs,
                    "elapsed_ms": elapsed
                })
        except Exception as e:
            # print(f"Error processing {hwnd}: {e}")
            continue
            
    return browser_data

if __name__ == "__main__":
    print("--- Prototyping Browser Tabs & URLs ---")
    browsers = get_browser_tabs()
    for b in browsers:
        print(f"Browser: {b['browser']} | URL: {b['active_url']}")
        print(f"  Tabs ({len(b['tabs'])}): {b['tabs']}")
        print(f"  Time: {b['elapsed_ms']:.2f}ms")
