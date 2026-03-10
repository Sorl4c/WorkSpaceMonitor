from src.json_snapshot_inference import editor_open_elsewhere, infer_snapshot_window


def test_infer_snapshot_window_uses_fallback_root_for_generic_terminal():
    window = {"process_name": "WindowsTerminal.exe", "title": "Windows PowerShell", "pid": 1}
    terminal = {"pid": 1, "cli_context": {"terminal_cwd": r"C:\Windows\System32", "active_worker": None}}

    inferred = infer_snapshot_window(window, terminal, [terminal], r"C:\local\AppsPython\WorkspaceMonitor")

    assert inferred["terminal_cwd"] == r"C:\local\AppsPython\WorkspaceMonitor"
    assert inferred["project_root"] == r"C:\local\AppsPython\WorkspaceMonitor"


def test_editor_open_elsewhere_matches_project_name_in_title():
    assert editor_open_elsewhere(
        r"C:\local\AppsPython\WorkspaceMonitor",
        [{"process_name": "Code.exe", "title": "idea2.md - WorkspaceMonitor - Visual Studio Code", "pid": 20}],
        [],
    )
