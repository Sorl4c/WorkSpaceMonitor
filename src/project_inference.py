from pathlib import Path


def infer_project_from_path(path: str | None) -> tuple[str, str] | None:
    if not path:
        return None
    normalized = str(Path(path).expanduser())
    inferred_name = Path(normalized).name or normalized
    return normalized, inferred_name


def infer_project_candidates(terminals: list[dict], windows: list[dict]) -> list[dict]:
    candidates: dict[str, dict] = {}
    for terminal in terminals:
        cli_context = terminal.get("cli_context") or {}
        for maybe_path in [
            cli_context.get("terminal_cwd"),
            (cli_context.get("active_worker") or {}).get("cwd"),
        ]:
            candidate = infer_project_from_path(maybe_path)
            if candidate:
                root_path, inferred_name = candidate
                candidates[root_path] = {"root_path": root_path, "inferred_name": inferred_name}

    for window in windows:
        title = (window.get("title") or "").strip()
        if " - " in title:
            possible = title.split(" - ")[0]
            if "/" in possible or "\\" in possible:
                candidate = infer_project_from_path(possible)
                if candidate:
                    root_path, inferred_name = candidate
                    candidates[root_path] = {"root_path": root_path, "inferred_name": inferred_name}
    return list(candidates.values())
