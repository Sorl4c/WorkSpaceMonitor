from src.project_inference import infer_project_from_path


def test_infer_project_from_valid_local_path():
    inferred = infer_project_from_path(r"C:\local\AppsPython\WorkspaceMonitor")
    assert inferred is not None
    assert inferred[1] == "WorkspaceMonitor"


def test_infer_project_rejects_browserish_titles():
    assert infer_project_from_path("view-source:https:\\alpinejs.dev\\component\\dropdown") is None
    assert infer_project_from_path("Issues · Sorl4c\\WorkSpaceMonitor") is None
