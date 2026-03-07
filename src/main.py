from fastapi import FastAPI
from pydantic import BaseModel
from src.desktop import get_virtual_desktops
from src.window import get_all_windows
from src.terminal import TerminalTracker, detect_terminals

app = FastAPI(title="Workspace Monitor")
terminal_tracker = TerminalTracker()

class TerminalNameRequest(BaseModel):
    name: str

@app.get("/")
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

