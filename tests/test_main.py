import asyncio

from src.main import gather_state, persistence, snapshot_service


def test_gather_state_shape():
    state = gather_state()
    assert "desktops" in state
    assert "windows" in state
    assert "terminals" in state


def test_snapshot_and_projects_api_flow(tmp_path):
    from src import main

    main.persistence = persistence.__class__(str(tmp_path / "wm.db"))
    main.snapshot_service = snapshot_service.__class__(main.persistence, lambda: {"desktops": [], "windows": [], "terminals": []}, app_version="test")

    result = asyncio.run(main.create_snapshot({"title": "t"}))
    assert result["snapshot_id"] > 0

    project = asyncio.run(main.create_project({"manual_name": "proj", "root_path": "/repo/a"}))
    assert project["id"] > 0

    projects = asyncio.run(main.list_projects())
    assert projects["items"]


def test_studio_route_exists():
    from src import main

    response = main.studio()
    assert getattr(response, "path", "").endswith("static/studio.html")
