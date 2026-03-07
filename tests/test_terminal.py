import os
import tempfile
import sqlite3
from unittest.mock import patch, MagicMock
from src.terminal import TerminalTracker, detect_terminals

def test_terminal_tracker_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        tracker = TerminalTracker(db_path)
        
        # Test schema creation implicitly done in init
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='terminals'")
        assert cursor.fetchone() is not None
        conn.close()

        # Test assigning a name
        tracker.set_name(1234, "Backend Server")
        
        # Test retrieving a name
        name = tracker.get_name(1234)
        assert name == "Backend Server"
        
        # Test retrieving non-existent name
        assert tracker.get_name(9999) is None

@patch('psutil.process_iter')
def test_detect_terminals(mock_process_iter):
    mock_proc1 = MagicMock()
    mock_proc1.info = {'pid': 100, 'name': 'WindowsTerminal.exe'}
    
    mock_proc2 = MagicMock()
    mock_proc2.info = {'pid': 101, 'name': 'cmd.exe'}
    
    mock_proc3 = MagicMock()
    mock_proc3.info = {'pid': 102, 'name': 'chrome.exe'}
    
    mock_process_iter.return_value = [mock_proc1, mock_proc2, mock_proc3]
    
    terminals = detect_terminals()
    assert len(terminals) == 2
    assert terminals[0]['pid'] == 100
    assert terminals[1]['pid'] == 101
