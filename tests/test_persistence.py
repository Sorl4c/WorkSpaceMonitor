from src.persistence import SQLitePersistence


def test_snapshot_roundtrip_with_scope_and_metadata(tmp_path):
    db = SQLitePersistence(str(tmp_path / "wm.db"))
    project = db.create_project({"manual_name": "A", "root_path": "/repo/a"})

    snapshot_id = db.create_snapshot(
        {
            "snapshot": {
                "scope": "desktop",
                "title": "Checkpoint",
                "note": "keep this",
                "capture_mode": "manual",
                "captured_at": "2026-03-08T00:00:00Z",
                "app_version": "test",
                "status": "valid",
                "desktop_count": 1,
                "window_count": 1,
                "terminal_count": 1,
                "captured_desktop_guid": "d-1",
                "captured_desktop_number": 1,
                "inferred_project_id": project["id"],
            },
            "desktops": [{"desktop_guid": "d-1", "desktop_number": 1, "desktop_name": "Desktop 1"}],
            "windows": [{"desktop_guid": "d-1", "hwnd_at_capture": 10, "title": "Code", "project_id": project["id"], "window_rect": {"x": 0}}],
            "terminals": [{"terminal_pid": 100, "terminal_name": "cmd.exe", "terminal_cwd": "/repo/a"}],
        }
    )
    detail = db.snapshot_detail(snapshot_id)
    assert detail["snapshot"]["scope"] == "desktop"
    assert detail["snapshot"]["title"] == "Checkpoint"
    assert detail["windows"][0]["window_rect_json"] is not None


def test_project_and_profiles_crud(tmp_path):
    db = SQLitePersistence(str(tmp_path / "wm.db"))
    project = db.create_project({"manual_name": "A", "root_path": "/repo/a"})
    terminal = db.add_project_terminal(project["id"], {"name": "t1", "cwd": "/repo/a", "preferred_zone": "left"})
    app = db.add_project_app(project["id"], {"app_type": "vscode", "display_name": "Code", "launch_target": "/repo/a"})
    loaded = db.get_project(project["id"])
    assert loaded
    assert len(loaded["terminal_profiles"]) == 1
    assert len(loaded["app_profiles"]) == 1
    assert terminal["preferred_zone"] == "left"
    assert app["app_type"] == "vscode"
