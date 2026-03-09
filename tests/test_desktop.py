from src.desktop import get_virtual_desktops


def test_get_virtual_desktops_always_list():
    desktops = get_virtual_desktops()
    assert isinstance(desktops, list)
    assert desktops
