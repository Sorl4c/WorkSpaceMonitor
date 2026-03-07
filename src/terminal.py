import sqlite3
import psutil

TERMINAL_PROCESS_NAMES = ["WindowsTerminal.exe", "cmd.exe", "pwsh.exe", "powershell.exe", "alacritty.exe"]

def detect_terminals() -> list[dict]:
    terminals = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] and proc.info['name'] in TERMINAL_PROCESS_NAMES:
                terminals.append({"pid": proc.info['pid'], "name": proc.info['name']})
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return terminals

class TerminalTracker:
    def __init__(self, db_path: str = "terminals.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        # sqlite3.connect(...) as conn only manages transactions, not closing.
        # We should explicitly close or just use the context manager properly.
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS terminals (
                    pid INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def set_name(self, pid: int, name: str):
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO terminals (pid, name) VALUES (?, ?)", 
                (pid, name)
            )
            conn.commit()
        finally:
            conn.close()

    def get_name(self, pid: int) -> str | None:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM terminals WHERE pid = ?", (pid,))
            result = cursor.fetchone()
            if result:
                return result[0]
            return None
        finally:
            conn.close()
