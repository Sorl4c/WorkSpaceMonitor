import asyncio
from typing import Any

try:
    from fastapi import FastAPI, HTTPException, Response
    from fastapi.responses import FileResponse
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

        def patch(self, *args, **kwargs):
            return lambda fn: fn

        def delete(self, *args, **kwargs):
            return lambda fn: fn

        def mount(self, *args, **kwargs):
            return None

    class StaticFiles:
        def __init__(self, *args, **kwargs):
            pass

    class FileResponse:
        def __init__(self, path: str):
            self.path = path

from src.desktop import get_virtual_desktops
from src.json_snapshot_service import JsonSnapshotService
from src.jump import focus_window, jump_to_window
from src.launch_service import LaunchService
from src.persistence import SQLitePersistence
from src.snapshot_service import SnapshotService
from src.terminal import detect_terminals
from src.window import get_all_windows

APP_VERSION = "0.2.0"
app = FastAPI(title="Workspace Monitor")
persistence = SQLitePersistence()
launch_service = LaunchService(persistence)


def gather_state() -> dict[str, Any]:
    return {"desktops": get_virtual_desktops(), "windows": get_all_windows(), "terminals": detect_terminals()}


snapshot_service = SnapshotService(persistence=persistence, gather_state_fn=gather_state, app_version=APP_VERSION)
json_snapshot_service = JsonSnapshotService(gather_state_fn=gather_state)


@app.get("/api/snapshot")
async def get_snapshot():
    return await asyncio.to_thread(gather_state)


@app.post("/api/snapshots")
async def create_snapshot(payload: dict[str, Any] | None = None):
    payload = payload or {}
    return await asyncio.to_thread(
        snapshot_service.capture_and_persist,
        payload.get("capture_mode", "manual"),
        "full",
        payload.get("title"),
        payload.get("note"),
        None,
    )


@app.post("/api/snapshots/desktop/{desktop_id}")
async def create_desktop_snapshot(desktop_id: str, payload: dict[str, Any] | None = None):
    payload = payload or {}
    return await asyncio.to_thread(
        snapshot_service.capture_and_persist,
        payload.get("capture_mode", "manual"),
        "desktop",
        payload.get("title"),
        payload.get("note"),
        desktop_id,
    )


@app.get("/api/snapshots/latest")
async def latest_snapshot():
    data = await asyncio.to_thread(persistence.latest_snapshot)
    if not data:
        raise HTTPException(status_code=404, detail="No snapshots found")
    return data


@app.get("/api/json-snapshot")
async def get_json_snapshot():
    data = await asyncio.to_thread(json_snapshot_service.get_current_snapshot)
    if not data:
        raise HTTPException(status_code=404, detail="No current desktop snapshot found")
    return data


@app.post("/api/json-snapshot/desktop/{desktop_id}")
async def create_json_desktop_snapshot(desktop_id: str, payload: dict[str, Any] | None = None):
    payload = payload or {}
    try:
        return await asyncio.to_thread(
            json_snapshot_service.capture_desktop,
            desktop_id,
            payload.get("title"),
            payload.get("note"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/json-snapshot/restore")
async def restore_json_snapshot():
    try:
        return await asyncio.to_thread(json_snapshot_service.restore_current_snapshot)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/json-snapshot/restore-plan")
async def restore_json_snapshot_plan():
    try:
        return await asyncio.to_thread(json_snapshot_service.build_restore_plan)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/snapshots")
async def list_snapshots(limit: int = 10, scope: str | None = None, desktop_number: int | None = None, project_id: int | None = None):
    return {"items": await asyncio.to_thread(persistence.recent_snapshots, limit, scope, desktop_number, project_id)}


@app.get("/api/snapshots/{snapshot_id}")
async def snapshot_detail(snapshot_id: int):
    data = await asyncio.to_thread(persistence.snapshot_detail, snapshot_id)
    if not data:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return data


@app.patch("/api/snapshots/{snapshot_id}")
async def patch_snapshot(snapshot_id: int, payload: dict[str, Any]):
    data = await asyncio.to_thread(persistence.update_snapshot, snapshot_id, payload)
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


@app.post("/api/snapshots/{snapshot_id}/restore")
async def restore_snapshot(snapshot_id: int):
    current_state = await asyncio.to_thread(gather_state)
    try:
        return await asyncio.to_thread(snapshot_service.execute_restore, snapshot_id, current_state)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/projects")
async def list_projects():
    return {"items": await asyncio.to_thread(persistence.list_projects)}


@app.post("/api/projects")
async def create_project(payload: dict[str, Any]):
    try:
        return await asyncio.to_thread(persistence.create_project, payload)
    except Exception as exc:
        detail = str(exc).lower()
        if "unique" in detail or "constraint" in detail:
            raise HTTPException(status_code=400, detail="Project root_path already exists") from exc
        raise


@app.get("/api/projects/{project_id}")
async def project_detail(project_id: int):
    data = await asyncio.to_thread(persistence.get_project, project_id)
    if not data:
        raise HTTPException(status_code=404, detail="Project not found")
    return data


@app.patch("/api/projects/{project_id}")
async def patch_project(project_id: int, payload: dict[str, Any]):
    data = await asyncio.to_thread(persistence.update_project, project_id, payload)
    if not data:
        raise HTTPException(status_code=404, detail="Project not found")
    return data


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: int):
    await asyncio.to_thread(persistence.delete_project, project_id)
    return {"status": "deleted", "project_id": project_id}


@app.post("/api/projects/{project_id}/terminals")
async def create_project_terminal(project_id: int, payload: dict[str, Any]):
    try:
        return await asyncio.to_thread(persistence.add_project_terminal, project_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.patch("/api/project-terminals/{profile_id}")
async def patch_project_terminal(profile_id: int, payload: dict[str, Any]):
    try:
        data = await asyncio.to_thread(persistence.update_project_terminal, profile_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not data:
        raise HTTPException(status_code=404, detail="Profile not found")
    return data


@app.delete("/api/project-terminals/{profile_id}")
async def delete_project_terminal(profile_id: int):
    await asyncio.to_thread(persistence.delete_project_terminal, profile_id)
    return {"status": "deleted", "profile_id": profile_id}


@app.post("/api/projects/{project_id}/apps")
async def create_project_app(project_id: int, payload: dict[str, Any]):
    try:
        return await asyncio.to_thread(persistence.add_project_app, project_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.patch("/api/project-apps/{profile_id}")
async def patch_project_app(profile_id: int, payload: dict[str, Any]):
    try:
        data = await asyncio.to_thread(persistence.update_project_app, profile_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not data:
        raise HTTPException(status_code=404, detail="Profile not found")
    return data


@app.delete("/api/project-apps/{profile_id}")
async def delete_project_app(profile_id: int):
    await asyncio.to_thread(persistence.delete_project_app, profile_id)
    return {"status": "deleted", "profile_id": profile_id}


@app.post("/api/projects/{project_id}/launch")
async def launch_project(project_id: int):
    try:
        return await asyncio.to_thread(launch_service.launch_project, project_id)
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


@app.get("/studio")
def studio():
    return FileResponse("static/studio.html")


@app.get("/events")
async def events_deprecated():
    return {"status": "deprecated", "message": "SSE is deprecated; use snapshot endpoints."}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
