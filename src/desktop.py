try:
    from pyvda import get_virtual_desktops as pyvda_get_desktops
except Exception:  # pragma: no cover - depends on Windows env
    pyvda_get_desktops = None


def get_virtual_desktops() -> list[dict]:
    if pyvda_get_desktops is None:
        return [{"id": "desktop-1", "number": 1, "name": "Desktop 1"}]

    desktops = []
    for vd in pyvda_get_desktops():
        desktops.append({"id": str(vd.id), "number": vd.number, "name": vd.name})
    return desktops
