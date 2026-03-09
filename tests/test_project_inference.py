from src.project_inference import infer_project_candidates, infer_project_from_path


def test_infer_project_from_local_path_only():
    assert infer_project_from_path("/repo/a") is not None
    assert infer_project_from_path("https://github.com/org/repo") is None


def test_inference_ignores_browser_titles_without_path():
    candidates = infer_project_candidates([], [{"title": "GitHub - Chrome"}])
    assert candidates == []
