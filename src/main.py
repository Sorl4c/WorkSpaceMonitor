import asyncio
import json
from typing import Any

try:
    from fastapi import FastAPI, HTTPException, Response
    from fastapi.staticfiles import StaticFiles
except Exception:  # pragma: no cover
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail

    class Response:
        def __init__(self, status_code: int = 200):
            self.status_code = status_code

    class FastAPI:
        def __init__(self, *args, **kwargs):
            pass

        def get(self, *args, **kwargs):
            return lambda fn: fn

        def post(self, *args, **kwargs):
            return lambda fn: fn

        def mount(self, *args, **kwargs):
            return None

    class StaticFiles:
        def __init__(self, *args, **kwargs):
            pass

from src.desktop import get_virtual_desktops
from src.jump import focus_window, jump_to_window
from src.persistence import SQLitePersistence
from src.snapshot_service import SnapshotService
from src.terminal import detect_terminals
from src.window import get_all_windows

APP_VERSION = "0.2.0"
app = FastAPI(title="Workspace Monitor")
persistence = SQLitePersistence()


def gather_state() -> dict[str, Any]:
    return {"desktops": get_virtual_desktops(), "windows": get_all_windows(), "terminals": detect_terminals()}


snapshot_service = SnapshotService(persistence=persistence, gather_state_fn=gather_state, app_version=APP_VERSION)


@app.get("/api/snapshot")
async def get_snapshot():
    return await asyncio.to_thread(gather_state)


@app.post("/api/snapshots")
async def create_snapshot():
    return await asyncio.to_thread(snapshot_service.capture_and_persist, "manual")


@app.get("/api/snapshots/latest")
async def latest_snapshot():
    data = await asyncio.to_thread(persistence.latest_snapshot)
    if not data:
        raise HTTPException(status_code=404, detail="No snapshots found")
    return data


@app.get("/api/snapshots")
async def list_snapshots(limit: int = 10):
    return {"items": await asyncio.to_thread(persistence.recent_snapshots, limit)}


@app.get("/api/snapshots/{snapshot_id}")
async def snapshot_detail(snapshot_id: int):
    data = await asyncio.to_thread(persistence.snapshot_detail, snapshot_id)
    if not data:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return data


@app.post("/api/snapshots/{snapshot_id}/restore-plan")
async def restore_plan(snapshot_id: int):
    current_state = await asyncio.to_thread(gather_state)
    try:
        return await asyncio.to_thread(snapshot_service.build_restore_plan, snapshot_id, current_state)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/windows/{hwnd}/focus")
async def api_focus_window(hwnd: int):
    await asyncio.to_thread(focus_window, hwnd)
    return {"status": "success", "hwnd": hwnd}


@app.post("/api/windows/{hwnd}/jump")
async def api_jump_to_window(hwnd: int):
    try:
        data = await asyncio.to_thread(jump_to_window, hwnd)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"status": "success" if data.get("focused") else "partial", "data": data}

@app.post("/api/desktops/{desktop_num}/go")
async def api_go_to_desktop(desktop_num: int):
    try:
        from pyvda import VirtualDesktop

        await asyncio.to_thread(lambda: VirtualDesktop(desktop_num).go())
        return {"status": "success", "desktop": desktop_num}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)

@app.get("/desktops")
def read_desktops():
    return get_virtual_desktops()


@app.get("/windows")
def read_windows():
    return get_all_windows()


@app.get("/terminals")
def read_terminals():
    return detect_terminals()

@app.get("/api/status")
def read_root():
    return {"status": "running", "message": "Workspace Monitor Daemon"}


@app.get("/events")
async def events_deprecated():
    return {"status": "deprecated", "message": "SSE is deprecated; use snapshot endpoints."}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
