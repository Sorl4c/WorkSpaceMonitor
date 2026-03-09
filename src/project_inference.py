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
        for maybe_path in (
            cli_context.get("terminal_cwd"),
            (cli_context.get("active_worker") or {}).get("cwd"),
        ):
            candidate = infer_project_from_path(maybe_path)
            if candidate:
                root_path, inferred_name = candidate
                candidates[root_path] = {"root_path": root_path, "inferred_name": inferred_name}

    for window in windows:
        title = (window.get("title") or "").strip()
        if " - " not in title:
            continue
        possible = title.split(" - ")[0]
        if "/" not in possible and "\\" not in possible:
            continue
        candidate = infer_project_from_path(possible)
        if candidate:
            root_path, inferred_name = candidate
            candidates[root_path] = {"root_path": root_path, "inferred_name": inferred_name}
    return list(candidates.values())


def infer_project_root_for_terminal(terminal: dict) -> str | None:
    cli_context = terminal.get("cli_context") or {}
    for maybe_path in (
        cli_context.get("terminal_cwd"),
        (cli_context.get("active_worker") or {}).get("cwd"),
    ):
        candidate = infer_project_from_path(maybe_path)
        if candidate:
            return candidate[0]
    return None


def infer_project_root_for_window(window: dict, terminals: list[dict]) -> str | None:
    window_pid = window.get("pid")
    for terminal in terminals:
        if terminal.get("pid") != window_pid:
            continue
        inferred_root = infer_project_root_for_terminal(terminal)
        if inferred_root:
            return inferred_root

    title = (window.get("title") or "").strip()
    if " - " in title:
        possible = title.split(" - ")[0]
        if "/" in possible or "\\" in possible:
            candidate = infer_project_from_path(possible)
            if candidate:
                return candidate[0]
    return None


def infer_window_hwnd_for_terminal(terminal: dict, windows: list[dict]) -> int | None:
    terminal_pid = terminal.get("pid")
    if terminal_pid is None:
        return None

    for window in windows:
        if window.get("pid") == terminal_pid:
            return window.get("hwnd")
    return None
