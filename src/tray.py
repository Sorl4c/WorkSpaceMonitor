import pystray
from PIL import Image

def create_tray_icon() -> pystray.Icon:
    # Create a simple solid color image for the icon placeholder
    image = Image.new('RGB', (64, 64), color=(0, 0, 0))
    menu = pystray.Menu(
        pystray.MenuItem("Exit", lambda: None)
    )
    return pystray.Icon("workspace_monitor", image, "Workspace Monitor", menu)
