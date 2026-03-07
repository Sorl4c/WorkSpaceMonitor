from fastapi import FastAPI

app = FastAPI(title="Workspace Monitor")

@app.get("/")
def read_root():
    return {"status": "running", "message": "Workspace Monitor Daemon"}
