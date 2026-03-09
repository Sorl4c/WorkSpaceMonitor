import json
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class SnapshotRecord:
    id: int
    capture_mode: str
    captured_at: str
    status: str
    desktop_count: int
    window_count: int
    terminal_count: int


class SQLitePersistence:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or self._default_path()
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _default_path(self) -> str:
        base = os.getenv("WORKSPACE_MONITOR_DATA_DIR")
        if base:
            return str(Path(base) / "workspace_monitor.db")
        home = Path.home() / ".workspace_monitor"
        return str(home / "workspace_monitor.db")

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    root_path TEXT UNIQUE NOT NULL,
                    inferred_name TEXT NOT NULL,
                    manual_name TEXT,
                    repository_url TEXT,
                    metadata_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS workspaces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    dominant_project_id INTEGER,
                    preferred_restore_strategy TEXT,
                    metadata_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(dominant_project_id) REFERENCES projects(id)
                );

                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    capture_mode TEXT NOT NULL,
                    captured_at TEXT NOT NULL,
                    app_version TEXT,
                    status TEXT NOT NULL,
                    desktop_count INTEGER NOT NULL,
                    window_count INTEGER NOT NULL,
                    terminal_count INTEGER NOT NULL,
                    notes_json TEXT
                );

                CREATE TABLE IF NOT EXISTS snapshot_desktops (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER NOT NULL,
                    desktop_guid TEXT,
                    desktop_number INTEGER,
                    desktop_name TEXT,
                    dominant_project_id INTEGER,
                    summary_json TEXT,
                    FOREIGN KEY(snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE,
                    FOREIGN KEY(dominant_project_id) REFERENCES projects(id)
                );

                CREATE TABLE IF NOT EXISTS snapshot_windows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER NOT NULL,
                    desktop_snapshot_id INTEGER,
                    hwnd_at_capture INTEGER,
                    pid_at_capture INTEGER,
                    process_name TEXT,
                    title TEXT,
                    clean_name TEXT,
                    semantic_type TEXT,
                    semantic_subtype TEXT,
                    importance TEXT,
                    tab_count INTEGER,
                    project_id INTEGER,
                    workspace_id INTEGER,
                    restore_hint_json TEXT,
                    FOREIGN KEY(snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE,
                    FOREIGN KEY(desktop_snapshot_id) REFERENCES snapshot_desktops(id) ON DELETE SET NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id),
                    FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
                );

                CREATE TABLE IF NOT EXISTS snapshot_terminals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER NOT NULL,
                    window_snapshot_id INTEGER,
                    terminal_pid INTEGER,
                    terminal_name TEXT,
                    terminal_cwd TEXT,
                    worker_name TEXT,
                    worker_cwd TEXT,
                    worker_cmdline_json TEXT,
                    FOREIGN KEY(snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE,
                    FOREIGN KEY(window_snapshot_id) REFERENCES snapshot_windows(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS restore_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    strategy TEXT,
                    summary_json TEXT,
                    FOREIGN KEY(snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS restore_task_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    restore_task_id INTEGER NOT NULL,
                    window_snapshot_id INTEGER,
                    action_type TEXT,
                    status TEXT,
                    message TEXT,
                    diagnostics_json TEXT,
                    FOREIGN KEY(restore_task_id) REFERENCES restore_tasks(id) ON DELETE CASCADE,
                    FOREIGN KEY(window_snapshot_id) REFERENCES snapshot_windows(id) ON DELETE SET NULL
                );

                CREATE INDEX IF NOT EXISTS idx_snapshots_captured_at ON snapshots(captured_at DESC);
                CREATE INDEX IF NOT EXISTS idx_snapshot_desktops_snapshot_id ON snapshot_desktops(snapshot_id);
                CREATE INDEX IF NOT EXISTS idx_snapshot_windows_snapshot_id ON snapshot_windows(snapshot_id);
                CREATE INDEX IF NOT EXISTS idx_snapshot_terminals_snapshot_id ON snapshot_terminals(snapshot_id);
                """
            )

    def now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def upsert_project(self, root_path: str, inferred_name: str) -> int:
        now = self.now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO projects(root_path, inferred_name, created_at, updated_at)
                VALUES(?, ?, ?, ?)
                ON CONFLICT(root_path) DO UPDATE SET
                  inferred_name=excluded.inferred_name,
                  updated_at=excluded.updated_at
                """,
                (root_path, inferred_name, now, now),
            )
            row = conn.execute("SELECT id FROM projects WHERE root_path = ?", (root_path,)).fetchone()
            return row["id"]

    def create_snapshot(self, payload: dict[str, Any]) -> int:
        with self.connect() as conn:
            snapshot = payload["snapshot"]
            cur = conn.execute(
                """
                INSERT INTO snapshots(capture_mode, captured_at, app_version, status, desktop_count, window_count, terminal_count, notes_json)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot["capture_mode"],
                    snapshot["captured_at"],
                    snapshot.get("app_version"),
                    snapshot.get("status", "valid"),
                    snapshot["desktop_count"],
                    snapshot["window_count"],
                    snapshot["terminal_count"],
                    json.dumps(snapshot.get("notes", {})),
                ),
            )
            snapshot_id = cur.lastrowid
            desktop_map = {}
            for desktop in payload.get("desktops", []):
                dcur = conn.execute(
                    """
                    INSERT INTO snapshot_desktops(snapshot_id, desktop_guid, desktop_number, desktop_name, dominant_project_id, summary_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        snapshot_id,
                        desktop.get("desktop_guid"),
                        desktop.get("desktop_number"),
                        desktop.get("desktop_name"),
                        desktop.get("dominant_project_id"),
                        json.dumps(desktop.get("summary", {})),
                    ),
                )
                desktop_map[desktop.get("desktop_guid")] = dcur.lastrowid

            window_map = {}
            for window in payload.get("windows", []):
                wcur = conn.execute(
                    """
                    INSERT INTO snapshot_windows(snapshot_id, desktop_snapshot_id, hwnd_at_capture, pid_at_capture, process_name, title, clean_name,
                    semantic_type, semantic_subtype, importance, tab_count, project_id, workspace_id, restore_hint_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        snapshot_id,
                        desktop_map.get(window.get("desktop_guid")),
                        window.get("hwnd_at_capture"),
                        window.get("pid_at_capture"),
                        window.get("process_name"),
                        window.get("title"),
                        window.get("clean_name"),
                        window.get("semantic_type"),
                        window.get("semantic_subtype"),
                        window.get("importance"),
                        window.get("tab_count"),
                        window.get("project_id"),
                        window.get("workspace_id"),
                        json.dumps(window.get("restore_hint", {})),
                    ),
                )
                if window.get("hwnd_at_capture") is not None:
                    window_map[window["hwnd_at_capture"]] = wcur.lastrowid

            for terminal in payload.get("terminals", []):
                worker = terminal.get("active_worker") or {}
                conn.execute(
                    """
                    INSERT INTO snapshot_terminals(snapshot_id, window_snapshot_id, terminal_pid, terminal_name, terminal_cwd, worker_name, worker_cwd, worker_cmdline_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        snapshot_id,
                        window_map.get(terminal.get("window_hwnd")),
                        terminal.get("terminal_pid"),
                        terminal.get("terminal_name"),
                        terminal.get("terminal_cwd"),
                        worker.get("name"),
                        worker.get("cwd"),
                        json.dumps(worker.get("cmdline")),
                    ),
                )
            return snapshot_id

    def recent_snapshots(self, limit: int = 10) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, capture_mode, captured_at, status, desktop_count, window_count, terminal_count
                FROM snapshots ORDER BY captured_at DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def latest_snapshot(self) -> dict[str, Any] | None:
        rows = self.recent_snapshots(limit=1)
        return rows[0] if rows else None

    def snapshot_detail(self, snapshot_id: int) -> dict[str, Any] | None:
        with self.connect() as conn:
            snapshot = conn.execute("SELECT * FROM snapshots WHERE id = ?", (snapshot_id,)).fetchone()
            if not snapshot:
                return None
            desktops = conn.execute("SELECT * FROM snapshot_desktops WHERE snapshot_id = ?", (snapshot_id,)).fetchall()
            windows = conn.execute("SELECT * FROM snapshot_windows WHERE snapshot_id = ?", (snapshot_id,)).fetchall()
            terminals = conn.execute("SELECT * FROM snapshot_terminals WHERE snapshot_id = ?", (snapshot_id,)).fetchall()
            return {
                "snapshot": dict(snapshot),
                "desktops": [dict(row) for row in desktops],
                "windows": [dict(row) for row in windows],
                "terminals": [dict(row) for row in terminals],
            }
