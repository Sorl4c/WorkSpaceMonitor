from src.json_snapshot_service import JsonSnapshotService


def test_capture_desktop_json_snapshot(tmp_path):
    service = JsonSnapshotService(
        lambda: {
            "desktops": [{"id": "desk-5", "number": 5, "name": "Desktop 5"}],
            "windows": [
                {
                    "hwnd": 11,
                    "pid": 222,
                    "title": r"C:\repo\app - Visual Studio Code",
                    "clean_name": "app",
                    "process_name": "Code.exe",
                    "desktop_id": "desk-5",
                    "rect": {"x": 10, "y": 10, "width": 100, "height": 100},
                }
            ],
            "terminals": [{"pid": 222, "name": "cmd.exe", "cli_context": {"terminal_cwd": r"C:\repo\app", "active_worker": None}}],
        },
        snapshot_path=str(tmp_path / "current_desktop_snapshot.json"),
    )

    snapshot = service.capture_desktop("desk-5", "Desk 5", "Investigando algo")
    assert snapshot["desktop"]["number"] == 5
    assert snapshot["window_count"] == 1
    assert snapshot["terminal_count"] == 1
    assert snapshot["dominant_project_root"] == r"C:\repo\app"


def test_build_restore_plan_from_json_snapshot(tmp_path):
    service = JsonSnapshotService(
        lambda: {
            "desktops": [{"id": "desk-5", "number": 5, "name": "Desktop 5"}],
            "windows": [],
            "terminals": [],
        },
        snapshot_path=str(tmp_path / "current_desktop_snapshot.json"),
    )
    service._write(
        {
            "version": 1,
            "scope": "desktop",
            "captured_at": "2026-03-10T00:00:00Z",
            "title": "Desk 5",
            "note": "Resume later",
            "desktop": {"id": "desk-5", "number": 5, "name": "Desktop 5"},
            "window_count": 1,
            "terminal_count": 1,
            "windows": [
                {
                    "title": "C:\\repo\\app - Visual Studio Code",
                    "process_name": "Code.exe",
                    "project_root": r"C:\repo\app",
                    "terminal_cwd": r"C:\repo\app",
                }
            ],
            "terminals": [{"name": "cmd.exe", "terminal_cwd": r"C:\repo\app"}],
        }
    )
    plan = service.build_restore_plan()
    assert plan["summary"]["restorable"] >= 1


def test_restore_plan_marks_explorer_paths_restorable(tmp_path):
    service = JsonSnapshotService(
        lambda: {"desktops": [], "windows": [], "terminals": []},
        snapshot_path=str(tmp_path / "current_desktop_snapshot.json"),
    )
    service._write(
        {
            "version": 1,
            "scope": "desktop",
            "captured_at": "2026-03-10T00:00:00Z",
            "title": "Desk 5",
            "note": "Resume later",
            "desktop": {"id": "desk-5", "number": 5, "name": "Desktop 5"},
            "window_count": 2,
            "terminal_count": 1,
            "windows": [
                {
                    "title": "Descargas - Explorador de archivos",
                    "process_name": "explorer.exe",
                    "explorer_path": r"C:\Users\carlos\Downloads",
                },
                {
                    "title": "cmd.exe",
                    "process_name": "WindowsTerminal.exe",
                    "terminal_cwd": r"C:\Windows\System32",
                },
            ],
            "terminals": [{"name": "WindowsTerminal.exe", "terminal_cwd": r"C:\Windows\System32"}],
        }
    )
    plan = service.build_restore_plan()
    actions = [item["action"]["type"] for item in plan["items"] if item.get("action")]
    assert "explorer" in actions
    assert actions.count("terminal") == 1


def test_restore_plan_marks_editor_already_open_elsewhere(tmp_path):
    service = JsonSnapshotService(
        lambda: {
            "desktops": [{"id": "desk-5", "number": 5, "name": "Desktop 5"}],
            "windows": [
                {
                    "title": "idea2.md - WorkspaceMonitor - Visual Studio Code",
                    "process_name": "Code.exe",
                    "desktop_id": "desk-2",
                    "pid": 999,
                }
            ],
            "terminals": [],
        },
        snapshot_path=str(tmp_path / "current_desktop_snapshot.json"),
    )
    service._write(
        {
            "version": 1,
            "scope": "desktop",
            "captured_at": "2026-03-10T00:00:00Z",
            "title": "Desk 5",
            "note": "Resume later",
            "desktop": {"id": "desk-5", "number": 5, "name": "Desktop 5"},
            "window_count": 1,
            "terminal_count": 0,
            "windows": [
                {
                    "title": "Welcome - Visual Studio Code",
                    "process_name": "Code.exe",
                    "project_root": r"C:\local\AppsPython\WorkspaceMonitor",
                }
            ],
            "terminals": [],
        }
    )
    plan = service.build_restore_plan()
    code_item = next(item for item in plan["items"] if item["process_name"] == "Code.exe")
    assert code_item["status"] == "already_open_elsewhere"
