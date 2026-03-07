import os
import tempfile
import sqlite3
from src.terminal import TerminalTracker

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
