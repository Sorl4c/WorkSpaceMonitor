import pystray
from src.tray import create_tray_icon

def test_create_tray_icon():
    icon = create_tray_icon()
    assert isinstance(icon, pystray.Icon)
    assert icon.title == "Workspace Monitor"
