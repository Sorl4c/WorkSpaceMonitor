from src.desktop import get_virtual_desktops

def test_get_virtual_desktops():
    desktops = get_virtual_desktops()
    assert isinstance(desktops, list)
    assert len(desktops) >= 1
    assert "id" in desktops[0]
    assert "number" in desktops[0]
