from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
from src.desktop import get_virtual_desktops
from src.window import get_all_windows
from src.terminal import TerminalTracker, detect_terminals

app = FastAPI(title="Workspace Monitor")
terminal_tracker = TerminalTracker()

class TerminalNameRequest(BaseModel):
    name: str

async def event_generator(request: Request):
    while True:
        if await request.is_disconnected():
            break
            
        # In a real app we'd diff state here. For MVP, we'll push current state periodically.
        state = {
            "desktops": get_virtual_desktops(),
            "windows": get_all_windows(),
            "terminals": detect_terminals()
        }
        for t in state["terminals"]:
            t["custom_name"] = terminal_tracker.get_name(t["pid"])
            
        yield {"data": json.dumps(state)}
        await asyncio.sleep(2)

@app.get("/events")
async def sse_events(request: Request):
    return EventSourceResponse(event_generator(request))

@app.get("/api/status")
def read_root():
    return {"status": "running", "message": "Workspace Monitor Daemon"}

@app.get("/desktops")
def read_desktops():
    return get_virtual_desktops()

@app.get("/windows")
def read_windows():
    return get_all_windows()

@app.get("/terminals")
def read_terminals():
    terminals = detect_terminals()
    for t in terminals:
        custom_name = terminal_tracker.get_name(t["pid"])
        t["custom_name"] = custom_name
    return terminals

@app.get("/terminals/{pid}")
def read_terminal(pid: int):
    name = terminal_tracker.get_name(pid)
    if name:
        return {"pid": pid, "name": name}
    return {"pid": pid, "name": None}

@app.post("/terminals/{pid}")
def update_terminal(pid: int, request: TerminalNameRequest):
    terminal_tracker.set_name(pid, request.name)
    return {"pid": pid, "name": request.name}

app.mount("/", StaticFiles(directory="static", html=True), name="static")

