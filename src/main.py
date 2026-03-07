from fastapi import FastAPI
from src.desktop import get_virtual_desktops

app = FastAPI(title="Workspace Monitor")

@app.get("/")
def read_root():
    return {"status": "running", "message": "Workspace Monitor Daemon"}

@app.get("/desktops")
def read_desktops():
    return get_virtual_desktops()
