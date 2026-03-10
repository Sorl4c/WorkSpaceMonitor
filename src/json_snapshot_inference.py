from pathlib import Path
from typing import Any

from src.project_inference import infer_project_from_path, infer_project_root_for_terminal, infer_project_root_for_window


def is_system_path(path: str | None) -> bool:
    if not path:
        return True
    lowered = path.strip().lower()
    return lowered.startswith(("c:\\windows", "::{"))


def desktop_local_roots(desktop_windows: list[dict[str, Any]], terminals: list[dict[str, Any]]) -> list[str]:
    roots: list[str] = []
    for window in desktop_windows:
        for maybe_path in (window.get("explorer_path"),):
            inferred = infer_project_from_path(maybe_path)
            if inferred and not is_system_path(inferred[0]) and inferred[0] not in roots:
                roots.append(inferred[0])
    for terminal in terminals:
        root = infer_project_root_for_terminal(terminal)
        if root and not is_system_path(root) and root not in roots:
            roots.append(root)
    return roots


def normalize_terminal_cwd(
    process_name: str | None,
    title: str | None,
    terminal: dict[str, Any] | None,
    fallback_root: str | None,
) -> str | None:
    cli_context = (terminal or {}).get("cli_context") or {}
    active_worker = cli_context.get("active_worker") or {}
    title_lower = (title or "").strip().lower()
    process_lower = (process_name or "").lower()
    generic_terminal_titles = {
        "windows powershell",
        "cmd.exe",
        "símbolo del sistema",
        "sÃ­mbolo del sistema",
        "c:\\windows\\system32\\cmd.exe",
    }

    for candidate in (active_worker.get("cwd"), cli_context.get("terminal_cwd")):
        if candidate and not is_system_path(candidate):
            return candidate

    terminal_cwd = cli_context.get("terminal_cwd") or active_worker.get("cwd")
    if process_lower in {"windowsterminal.exe", "powershell.exe", "pwsh.exe", "cmd.exe"} and fallback_root:
        if not terminal_cwd or is_system_path(terminal_cwd) or title_lower in generic_terminal_titles:
            return fallback_root
    return terminal_cwd


def infer_snapshot_window(
    window: dict[str, Any],
    terminal: dict[str, Any] | None,
    all_terminals: list[dict[str, Any]],
    fallback_root: str | None,
) -> dict[str, Any]:
    project_root = infer_project_root_for_window(window, all_terminals)
    process_name = (window.get("process_name") or "").lower()
    title = window.get("title") or ""
    if (not project_root or is_system_path(project_root)) and process_name == "code.exe" and fallback_root:
        if "visual studio code" in title.lower() or "vscode" in title.lower():
            project_root = fallback_root
    terminal_cwd = normalize_terminal_cwd(window.get("process_name"), title, terminal, fallback_root)
    if process_name in {"windowsterminal.exe", "powershell.exe", "pwsh.exe", "cmd.exe"} and fallback_root:
        if not project_root or is_system_path(project_root):
            project_root = terminal_cwd if terminal_cwd and not is_system_path(terminal_cwd) else fallback_root
    return {"project_root": project_root, "terminal_cwd": terminal_cwd}


def infer_snapshot_terminal(terminal: dict[str, Any], fallback_root: str | None) -> dict[str, Any]:
    terminal_cwd = normalize_terminal_cwd(terminal.get("name"), terminal.get("name"), terminal, fallback_root)
    project_root = infer_project_root_for_terminal(terminal)
    if (not project_root or is_system_path(project_root)) and terminal_cwd and not is_system_path(terminal_cwd):
        project_root = terminal_cwd
    return {"terminal_cwd": terminal_cwd, "project_root": project_root}


def dominant_project_root(inferred_project_roots: dict[str, int], fallback_root: str | None) -> str | None:
    if inferred_project_roots:
        return max(inferred_project_roots.items(), key=lambda item: item[1])[0]
    return fallback_root


def editor_open_elsewhere(project_root: str | None, current_windows_elsewhere: list[dict[str, Any]], terminals: list[dict[str, Any]]) -> bool:
    if not project_root:
        return False
    project_name = Path(project_root).name.lower()

    current_editor_projects_elsewhere = {
        infer_project_root_for_window(window, terminals)
        for window in current_windows_elsewhere
        if (window.get("process_name") or "").lower() in {"code.exe", "cursor.exe"}
    }
    current_editor_projects_elsewhere.discard(None)
    if project_root in current_editor_projects_elsewhere:
        return True

    current_editor_titles_elsewhere = {
        (window.get("title") or "").strip().lower()
        for window in current_windows_elsewhere
        if (window.get("process_name") or "").lower() in {"code.exe", "cursor.exe"}
    }
    return any(project_name and project_name in editor_title for editor_title in current_editor_titles_elsewhere)
