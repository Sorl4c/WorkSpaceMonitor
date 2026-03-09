import asyncio

from src.main import gather_state, persistence, snapshot_service


def test_gather_state_shape():
    state = gather_state()
    assert "desktops" in state
    assert "windows" in state
    assert "terminals" in state


def test_manual_snapshot_flow(tmp_path, monkeypatch):
    from src import main
    main.persistence = persistence.__class__(str(tmp_path / "wm.db"))
    main.snapshot_service = snapshot_service.__class__(main.persistence, main.gather_state, app_version="test")

    result = asyncio.run(main.create_snapshot())
    assert result["snapshot_id"] > 0
    listed = asyncio.run(main.list_snapshots(limit=5))
    assert listed["items"]
