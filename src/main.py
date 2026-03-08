from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
import time
import os
import psutil
from src.desktop import get_virtual_desktops
from src.window import get_all_windows
from src.terminal import detect_terminals
from src.jump import focus_window, jump_to_window
from pyvda import VirtualDesktop

app = FastAPI(title="Workspace Monitor")

# Variable para activar/desactivar el log de rendimiento en consola
DEBUG_PERFORMANCE = True

def gather_state():
    """Función síncrona que recopila el estado. La aislamos para ejecutarla en un hilo."""
    state = {
        "desktops": get_virtual_desktops(),
        "windows": get_all_windows(),
        "terminals": detect_terminals()
    }
    return state

async def event_generator(request: Request):
    my_process = psutil.Process(os.getpid())
    my_process.cpu_percent() # Init CPU counter

    while True:
        if await request.is_disconnected():
            break
            
        t0 = time.time()
        
        # Ejecutamos la recolección en un hilo secundario para NO bloquear FastAPI
        state = await asyncio.to_thread(gather_state)
            
        t1 = time.time()
        
        if DEBUG_PERFORMANCE:
            elapsed_ms = (t1 - t0) * 1000
            ram_mb = my_process.memory_info().rss / (1024 * 1024)
            cpu_usage = my_process.cpu_percent()
            
            print(f"[DEBUG] Estado recopilado en {elapsed_ms:.2f}ms")
            print(f"[DEBUG] Daemon Consume: {ram_mb:.2f} MB RAM | CPU: {cpu_usage}%")
            print("-" * 40)
            
        yield {"data": json.dumps(state)}
        await asyncio.sleep(2)

@app.get("/api/snapshot")
async def get_snapshot():
    """Retorna el estado actual del workspace una sola vez."""
    state = await asyncio.to_thread(gather_state)
    return state

@app.post("/api/windows/{hwnd}/focus")
async def api_focus_window(hwnd: int):
    """Enfoca una ventana específica."""
    try:
        await asyncio.to_thread(focus_window, hwnd)
        return {"status": "success", "hwnd": hwnd}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/windows/{hwnd}/jump")
async def api_jump_to_window(hwnd: int):
    """Acción completa: cambia de escritorio y enfoca la ventana."""
    try:
        result = await asyncio.to_thread(jump_to_window, hwnd)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/desktops/{desktop_num}/go")
async def api_go_to_desktop(desktop_num: int):
    """Cambia al escritorio virtual especificado por su número."""
    try:
        # Usamos pyvda directamente para el cambio de escritorio
        await asyncio.to_thread(lambda: VirtualDesktop(desktop_num).go())
        return {"status": "success", "desktop": desktop_num}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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
    return detect_terminals()

app.mount("/", StaticFiles(directory="static", html=True), name="static")
