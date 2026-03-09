from src.persistence import SQLitePersistence
from src.snapshot_service import SnapshotService


def test_capture_and_restore_plan(tmp_path):
    def fake_gather():
        return {
            "desktops": [{"id": "d-1", "number": 1, "name": "Desktop 1"}],
            "windows": [
                {"hwnd": 1, "title": "Workspace - Visual Studio Code", "desktop_id": "d-1", "pid": 99, "process_name": "Code.exe"}
            ],
            "terminals": [{"pid": 99, "name": "cmd.exe", "cli_context": {"terminal_cwd": "/repo/a", "active_worker": None}}],
        }

    db = SQLitePersistence(str(tmp_path / "wm.db"))
    service = SnapshotService(db, fake_gather, app_version="test")
    result = service.capture_and_persist("manual")
    plan = service.build_restore_plan(result["snapshot_id"], fake_gather())
    assert plan["summary"]["matched"] == 1
