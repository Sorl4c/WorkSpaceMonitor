from src.persistence import SQLitePersistence


def test_snapshot_roundtrip(tmp_path):
    db = SQLitePersistence(str(tmp_path / "wm.db"))
    project_id = db.upsert_project("/repo/a", "a")
    assert project_id > 0

    snapshot_id = db.create_snapshot(
        {
            "snapshot": {
                "capture_mode": "manual",
                "captured_at": "2026-03-08T00:00:00Z",
                "app_version": "test",
                "status": "valid",
                "desktop_count": 1,
                "window_count": 1,
                "terminal_count": 1,
            },
            "desktops": [{"desktop_guid": "d-1", "desktop_number": 1, "desktop_name": "Desktop 1"}],
            "windows": [{"desktop_guid": "d-1", "hwnd_at_capture": 10, "title": "Code", "project_id": project_id}],
            "terminals": [{"terminal_pid": 100, "terminal_name": "cmd.exe", "terminal_cwd": "/repo/a"}],
        }
    )
    assert snapshot_id > 0
    latest = db.latest_snapshot()
    assert latest["id"] == snapshot_id
    detail = db.snapshot_detail(snapshot_id)
    assert len(detail["desktops"]) == 1
    assert len(detail["windows"]) == 1
    assert len(detail["terminals"]) == 1
