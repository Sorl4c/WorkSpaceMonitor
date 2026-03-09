from src.launch_service import LaunchService
from src.persistence import SQLitePersistence


def test_zone_rect_mapping(tmp_path):
    service = LaunchService(SQLitePersistence(str(tmp_path / "wm.db")))
    rect = service.zone_rect("left", (0, 0, 1000, 800))
    assert rect == {"x": 0, "y": 0, "width": 500, "height": 800}


def test_launch_plan_itemized(tmp_path):
    db = SQLitePersistence(str(tmp_path / "wm.db"))
    root_path = str(tmp_path)
    project = db.create_project({"manual_name": "proj", "root_path": root_path})
    db.add_project_terminal(project["id"], {"name": "shell", "cwd": root_path})
    db.add_project_app(project["id"], {"app_type": "custom", "display_name": "Echo", "launch_target": "echo", "launch_args": ["ok"]})
    service = LaunchService(db)
    result = service.launch_project(project["id"])
    assert result["project_id"] == project["id"]
    assert len(result["items"]) == 2
