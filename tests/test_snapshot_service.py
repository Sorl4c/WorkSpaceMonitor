from src.persistence import SQLitePersistence
from src.snapshot_service import SnapshotService


def test_capture_desktop_scope_and_restore(tmp_path):
    def fake_gather():
        return {
            "desktops": [{"id": "d-1", "number": 1, "name": "Desktop 1"}, {"id": "d-2", "number": 2, "name": "Desktop 2"}],
            "windows": [
                {"hwnd": 1, "title": "/repo/a - Visual Studio Code", "desktop_id": "d-1", "pid": 99, "process_name": "Code.exe"},
                {"hwnd": 2, "title": "GitHub - Chrome", "desktop_id": "d-2", "pid": 10, "process_name": "chrome.exe"},
            ],
            "terminals": [{"pid": 99, "name": "cmd.exe", "cli_context": {"terminal_cwd": "/repo/a", "active_worker": None}}],
        }

    db = SQLitePersistence(str(tmp_path / "wm.db"))
    service = SnapshotService(db, fake_gather, app_version="test")
    result = service.capture_and_persist("manual", "desktop", "Desk", "N", "d-1")
    detail = db.snapshot_detail(result["snapshot_id"])
    plan = service.build_restore_plan(result["snapshot_id"], fake_gather())
    restore = service.execute_restore(result["snapshot_id"], fake_gather())

    assert detail["snapshot"]["scope"] == "desktop"
    assert detail["snapshot"]["captured_desktop_guid"] == "d-1"
    assert len(detail["windows"]) == 1
    assert plan["summary"]["matched"] == 1
    assert "items" in restore
