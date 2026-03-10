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
    main.snapshot_service = snapshot_service.__class__(
        main.persistence,
        lambda: {"desktops": [], "windows": [], "terminals": []},
        app_version="test",
    )
    main.launch_service = main.launch_service.__class__(main.persistence)

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


def test_json_snapshot_api_flow(tmp_path):
    from src import main
    from src.json_snapshot_service import JsonSnapshotService

    main.json_snapshot_service = JsonSnapshotService(
        lambda: {
            "desktops": [{"id": "desk-5", "number": 5, "name": "Desktop 5"}],
            "windows": [],
            "terminals": [],
        },
        snapshot_path=str(tmp_path / "current_desktop_snapshot.json"),
    )

    saved = asyncio.run(main.create_json_desktop_snapshot("desk-5", {"title": "Desk 5", "note": "Later"}))
    assert saved["desktop"]["number"] == 5

    loaded = asyncio.run(main.get_json_snapshot())
    assert loaded["title"] == "Desk 5"


def test_singleton_tools_api_flow():
    from src import main

    main.singleton_tools_service = main.singleton_tools_service.__class__()
    result = asyncio.run(main.get_singleton_tools())
    assert "items" in result
    assert isinstance(result["items"], list)
