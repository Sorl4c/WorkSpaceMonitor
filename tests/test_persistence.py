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


def test_project_schema_includes_github_and_terminal_profiles(tmp_path):
    db = SQLitePersistence(str(tmp_path / "wm.db"))
    with db.connect() as conn:
        project_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(projects)").fetchall()
        }
        assert "github_owner" in project_columns
        assert "github_repo" in project_columns
        assert "default_branch" in project_columns

        profile_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(project_terminal_profiles)").fetchall()
        }
        assert "project_id" in profile_columns
        assert "launch_command" in profile_columns
        assert "desktop_preference" in profile_columns
