from src.project_inference import infer_project_from_path


def test_infer_project_from_path():
    root, name = infer_project_from_path("/repos/workspace-monitor")
    assert root.endswith("workspace-monitor")
    assert name == "workspace-monitor"
