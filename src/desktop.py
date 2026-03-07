from pyvda import get_virtual_desktops as pyvda_get_desktops

def get_virtual_desktops() -> list[dict]:
    desktops = []
    for vd in pyvda_get_desktops():
        desktops.append({
            "id": str(vd.id),
            "number": vd.number,
            "name": vd.name
        })
    return desktops
