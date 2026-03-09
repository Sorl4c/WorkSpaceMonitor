from src.window import clean_terminal_title


def test_clean_terminal_title():
    assert clean_terminal_title("◇ Ready (WorkspaceMonitor)") == "WorkspaceMonitor"
