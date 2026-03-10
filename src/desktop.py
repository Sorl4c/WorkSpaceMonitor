try:
    from pyvda import get_virtual_desktops as pyvda_get_desktops
    from pyvda import VirtualDesktop
except Exception:  # pragma: no cover - depends on Windows env
    pyvda_get_desktops = None
    VirtualDesktop = None


def get_virtual_desktops() -> list[dict]:
    if pyvda_get_desktops is None:
        return [{"id": "desktop-1", "number": 1, "name": "Desktop 1"}]

    desktops = []
    for vd in pyvda_get_desktops():
        desktops.append({"id": str(vd.id), "number": vd.number, "name": vd.name})
    return desktops


def create_virtual_desktop() -> dict:
    if VirtualDesktop is None:
        raise RuntimeError("Virtual desktop creation is not available")
    desktop = VirtualDesktop.create()
    return {"id": str(desktop.id), "number": desktop.number, "name": desktop.name}
