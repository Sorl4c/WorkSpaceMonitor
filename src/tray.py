try:
    import pystray
    from PIL import Image
except Exception:  # pragma: no cover
    pystray = None
    Image = None


def create_tray_icon():
    if pystray is None or Image is None:
        return None
    image = Image.new("RGB", (64, 64), color=(0, 0, 0))
    menu = pystray.Menu(pystray.MenuItem("Exit", lambda: None))
    return pystray.Icon("workspace_monitor", image, "Workspace Monitor", menu)
