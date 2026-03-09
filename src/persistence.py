import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALLOWED_ZONES = {
    "maximized",
    "left",
    "right",
    "top-left",
    "top-right",
    "bottom-left",
    "bottom-right",
    "center",
}


class SQLitePersistence:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or self._default_path()
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _default_path(self) -> str:
        base = os.getenv("WORKSPACE_MONITOR_DATA_DIR")
        if base:
            return str(Path(base) / "workspace_monitor.db")
        repo_root = Path(__file__).resolve().parent.parent
        return str(repo_root / "workspace_monitor.db")

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

    def _ensure_column(self, conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        cols = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def _init_db(self):
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    root_path TEXT UNIQUE NOT NULL,
                    inferred_name TEXT,
                    manual_name TEXT,
                    repository_url TEXT,
                    github_provider TEXT,
                    github_owner TEXT,
                    github_repo TEXT,
                    default_branch TEXT,
                    repo_local_path_confirmed INTEGER NOT NULL DEFAULT 0,
                    notes TEXT,
                    preferred_desktop_number INTEGER,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    metadata_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS project_terminal_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    cwd TEXT NOT NULL,
                    launch_command TEXT,
                    shell TEXT,
                    preferred_desktop_number INTEGER,
                    preferred_zone TEXT,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    auto_launch INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS project_app_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    app_type TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    launch_target TEXT,
                    launch_args_json TEXT,
                    preferred_desktop_number INTEGER,
                    preferred_zone TEXT,
                    auto_launch INTEGER NOT NULL DEFAULT 1,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
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
                    scope TEXT NOT NULL DEFAULT 'full',
                    title TEXT,
                    note TEXT,
                    capture_mode TEXT NOT NULL,
                    captured_at TEXT NOT NULL,
                    app_version TEXT,
                    status TEXT NOT NULL,
                    desktop_count INTEGER NOT NULL,
                    window_count INTEGER NOT NULL,
                    terminal_count INTEGER NOT NULL,
                    captured_desktop_guid TEXT,
                    captured_desktop_number INTEGER,
                    inferred_project_id INTEGER,
                    is_pinned INTEGER NOT NULL DEFAULT 0,
                    notes_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(inferred_project_id) REFERENCES projects(id)
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
                    window_rect_json TEXT,
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
                CREATE INDEX IF NOT EXISTS idx_project_terminal_profiles_project_id ON project_terminal_profiles(project_id);
                CREATE INDEX IF NOT EXISTS idx_project_app_profiles_project_id ON project_app_profiles(project_id);
                """
            )
            self._migrate_existing_schema(conn)

    def _migrate_existing_schema(self, conn: sqlite3.Connection) -> None:
        self._ensure_column(conn, "projects", "notes", "TEXT")
        self._ensure_column(conn, "projects", "preferred_desktop_number", "INTEGER")

        self._ensure_column(conn, "project_terminal_profiles", "cwd", "TEXT")
        self._ensure_column(conn, "project_terminal_profiles", "preferred_desktop_number", "INTEGER")
        self._ensure_column(conn, "project_terminal_profiles", "preferred_zone", "TEXT")
        self._ensure_column(conn, "project_terminal_profiles", "auto_launch", "INTEGER NOT NULL DEFAULT 1")

        self._ensure_column(conn, "snapshots", "scope", "TEXT NOT NULL DEFAULT 'full'")
        self._ensure_column(conn, "snapshots", "title", "TEXT")
        self._ensure_column(conn, "snapshots", "note", "TEXT")
        self._ensure_column(conn, "snapshots", "captured_desktop_guid", "TEXT")
        self._ensure_column(conn, "snapshots", "captured_desktop_number", "INTEGER")
        self._ensure_column(conn, "snapshots", "inferred_project_id", "INTEGER")
        self._ensure_column(conn, "snapshots", "is_pinned", "INTEGER NOT NULL DEFAULT 0")
        self._ensure_column(conn, "snapshots", "created_at", "TEXT")
        self._ensure_column(conn, "snapshots", "updated_at", "TEXT")

        self._ensure_column(conn, "snapshot_windows", "window_rect_json", "TEXT")
        conn.execute(
            "UPDATE snapshots SET created_at = COALESCE(created_at, captured_at), updated_at = COALESCE(updated_at, captured_at)"
        )
        conn.execute("UPDATE project_terminal_profiles SET cwd = COALESCE(cwd, '.') WHERE cwd IS NULL")

    def now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def upsert_project(self, root_path: str, inferred_name: str) -> int:
        now = self.now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO projects(root_path, inferred_name, manual_name, created_at, updated_at)
                VALUES(?, ?, COALESCE(NULL, ?), ?, ?)
                ON CONFLICT(root_path) DO UPDATE SET
                  inferred_name=excluded.inferred_name,
                  updated_at=excluded.updated_at
                """,
                (root_path, inferred_name, inferred_name, now, now),
            )
            row = conn.execute("SELECT id FROM projects WHERE root_path = ?", (root_path,)).fetchone()
            return row["id"]

    def create_project(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = self.now_iso()
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO projects(root_path, inferred_name, manual_name, repository_url, github_provider, github_owner, github_repo,
                default_branch, repo_local_path_confirmed, notes, preferred_desktop_number, is_active, created_at, updated_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["root_path"],
                    payload.get("inferred_name") or payload.get("manual_name") or Path(payload["root_path"]).name,
                    payload.get("manual_name"),
                    payload.get("repository_url"),
                    payload.get("github_provider"),
                    payload.get("github_owner"),
                    payload.get("github_repo"),
                    payload.get("default_branch"),
                    1 if payload.get("repo_local_path_confirmed") else 0,
                    payload.get("notes"),
                    payload.get("preferred_desktop_number"),
                    1 if payload.get("is_active", True) else 0,
                    now,
                    now,
                ),
            )
            row = conn.execute("SELECT * FROM projects WHERE id = ?", (cur.lastrowid,)).fetchone()
            return dict(row)

    def list_projects(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM projects WHERE is_active = 1 ORDER BY updated_at DESC").fetchall()
            return [dict(row) for row in rows]

    def get_project(self, project_id: int) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
            if not row:
                return None
            data = dict(row)
            data["terminal_profiles"] = self.list_project_terminals(project_id)
            data["app_profiles"] = self.list_project_apps(project_id)
            return data

    def update_project(self, project_id: int, payload: dict[str, Any]) -> dict[str, Any] | None:
        allowed = {
            "manual_name",
            "root_path",
            "repository_url",
            "github_provider",
            "github_owner",
            "github_repo",
            "default_branch",
            "repo_local_path_confirmed",
            "notes",
            "preferred_desktop_number",
            "is_active",
        }
        updates = {k: v for k, v in payload.items() if k in allowed}
        if not updates:
            return self.get_project(project_id)
        sets = []
        values = []
        for key, value in updates.items():
            if key in {"repo_local_path_confirmed", "is_active"}:
                value = 1 if value else 0
            sets.append(f"{key} = ?")
            values.append(value)
        values.extend([self.now_iso(), project_id])
        with self.connect() as conn:
            conn.execute(f"UPDATE projects SET {', '.join(sets)}, updated_at = ? WHERE id = ?", values)
        return self.get_project(project_id)

    def delete_project(self, project_id: int) -> None:
        with self.connect() as conn:
            conn.execute("UPDATE projects SET is_active = 0, updated_at = ? WHERE id = ?", (self.now_iso(), project_id))

    def add_project_terminal(self, project_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        now = self.now_iso()
        zone = payload.get("preferred_zone")
        if zone and zone not in ALLOWED_ZONES:
            raise ValueError("invalid preferred_zone")
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO project_terminal_profiles(project_id, name, cwd, launch_command, shell, preferred_desktop_number,
                preferred_zone, sort_order, auto_launch, created_at, updated_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    payload["name"],
                    payload["cwd"],
                    payload.get("launch_command"),
                    payload.get("shell"),
                    payload.get("preferred_desktop_number"),
                    zone,
                    payload.get("sort_order", 0),
                    1 if payload.get("auto_launch", True) else 0,
                    now,
                    now,
                ),
            )
            row = conn.execute("SELECT * FROM project_terminal_profiles WHERE id = ?", (cur.lastrowid,)).fetchone()
            return dict(row)

    def list_project_terminals(self, project_id: int) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM project_terminal_profiles WHERE project_id = ? ORDER BY sort_order, id", (project_id,)
            ).fetchall()
            return [dict(row) for row in rows]

    def get_project_terminal(self, profile_id: int) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM project_terminal_profiles WHERE id = ?", (profile_id,)).fetchone()
            return dict(row) if row else None

    def update_project_terminal(self, profile_id: int, payload: dict[str, Any]) -> dict[str, Any] | None:
        allowed = {
            "name",
            "cwd",
            "launch_command",
            "shell",
            "preferred_desktop_number",
            "preferred_zone",
            "sort_order",
            "auto_launch",
        }
        updates = {k: v for k, v in payload.items() if k in allowed}
        if "preferred_zone" in updates and updates["preferred_zone"] and updates["preferred_zone"] not in ALLOWED_ZONES:
            raise ValueError("invalid preferred_zone")
        sets = []
        values = []
        for key, value in updates.items():
            if key == "auto_launch":
                value = 1 if value else 0
            sets.append(f"{key} = ?")
            values.append(value)
        values.extend([self.now_iso(), profile_id])
        with self.connect() as conn:
            if sets:
                conn.execute(f"UPDATE project_terminal_profiles SET {', '.join(sets)}, updated_at = ? WHERE id = ?", values)
        return self.get_project_terminal(profile_id)

    def delete_project_terminal(self, profile_id: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM project_terminal_profiles WHERE id = ?", (profile_id,))

    def add_project_app(self, project_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        if payload["app_type"] not in {"vscode", "explorer", "browser", "custom"}:
            raise ValueError("invalid app_type")
        zone = payload.get("preferred_zone")
        if zone and zone not in ALLOWED_ZONES:
            raise ValueError("invalid preferred_zone")
        now = self.now_iso()
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO project_app_profiles(project_id, app_type, display_name, launch_target, launch_args_json,
                preferred_desktop_number, preferred_zone, auto_launch, sort_order, created_at, updated_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    payload["app_type"],
                    payload.get("display_name") or payload["app_type"],
                    payload.get("launch_target"),
                    json.dumps(payload.get("launch_args", [])),
                    payload.get("preferred_desktop_number"),
                    zone,
                    1 if payload.get("auto_launch", True) else 0,
                    payload.get("sort_order", 0),
                    now,
                    now,
                ),
            )
            row = conn.execute("SELECT * FROM project_app_profiles WHERE id = ?", (cur.lastrowid,)).fetchone()
            return self._decode_app_row(row)

    def list_project_apps(self, project_id: int) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM project_app_profiles WHERE project_id = ? ORDER BY sort_order, id", (project_id,)
            ).fetchall()
            return [self._decode_app_row(row) for row in rows]

    def _decode_app_row(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        raw_args = data.get("launch_args_json")
        data["launch_args"] = json.loads(raw_args) if raw_args else []
        return data

    def get_project_app(self, profile_id: int) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM project_app_profiles WHERE id = ?", (profile_id,)).fetchone()
            return self._decode_app_row(row) if row else None

    def update_project_app(self, profile_id: int, payload: dict[str, Any]) -> dict[str, Any] | None:
        allowed = {
            "app_type",
            "display_name",
            "launch_target",
            "launch_args",
            "preferred_desktop_number",
            "preferred_zone",
            "auto_launch",
            "sort_order",
        }
        updates = {k: v for k, v in payload.items() if k in allowed}
        if "app_type" in updates and updates["app_type"] not in {"vscode", "explorer", "browser", "custom"}:
            raise ValueError("invalid app_type")
        if "preferred_zone" in updates and updates["preferred_zone"] and updates["preferred_zone"] not in ALLOWED_ZONES:
            raise ValueError("invalid preferred_zone")
        sets = []
        values = []
        for key, value in updates.items():
            if key == "auto_launch":
                value = 1 if value else 0
            if key == "launch_args":
                key = "launch_args_json"
                value = json.dumps(value)
            sets.append(f"{key} = ?")
            values.append(value)
        values.extend([self.now_iso(), profile_id])
        with self.connect() as conn:
            if sets:
                conn.execute(f"UPDATE project_app_profiles SET {', '.join(sets)}, updated_at = ? WHERE id = ?", values)
        return self.get_project_app(profile_id)

    def delete_project_app(self, profile_id: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM project_app_profiles WHERE id = ?", (profile_id,))

    def create_snapshot(self, payload: dict[str, Any]) -> int:
        now = self.now_iso()
        with self.connect() as conn:
            snapshot = payload["snapshot"]
            cur = conn.execute(
                """
                INSERT INTO snapshots(scope, title, note, capture_mode, captured_at, app_version, status, desktop_count, window_count,
                terminal_count, captured_desktop_guid, captured_desktop_number, inferred_project_id, is_pinned, notes_json, created_at, updated_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot.get("scope", "full"),
                    snapshot.get("title"),
                    snapshot.get("note"),
                    snapshot["capture_mode"],
                    snapshot["captured_at"],
                    snapshot.get("app_version"),
                    snapshot.get("status", "valid"),
                    snapshot["desktop_count"],
                    snapshot["window_count"],
                    snapshot["terminal_count"],
                    snapshot.get("captured_desktop_guid"),
                    snapshot.get("captured_desktop_number"),
                    snapshot.get("inferred_project_id"),
                    1 if snapshot.get("is_pinned") else 0,
                    json.dumps(snapshot.get("notes", {})),
                    now,
                    now,
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
                    semantic_type, semantic_subtype, importance, tab_count, project_id, workspace_id, restore_hint_json, window_rect_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        json.dumps(window.get("window_rect", {})),
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

    def recent_snapshots(
        self,
        limit: int = 10,
        scope: str | None = None,
        desktop_number: int | None = None,
        project_id: int | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM snapshots WHERE 1=1"
        params: list[Any] = []
        if scope:
            query += " AND scope = ?"
            params.append(scope)
        if desktop_number is not None:
            query += " AND captured_desktop_number = ?"
            params.append(desktop_number)
        if project_id is not None:
            query += " AND inferred_project_id = ?"
            params.append(project_id)
        query += " ORDER BY captured_at DESC LIMIT ?"
        params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()
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

    def update_snapshot(self, snapshot_id: int, payload: dict[str, Any]) -> dict[str, Any] | None:
        allowed = {"title", "note", "is_pinned"}
        updates = {k: v for k, v in payload.items() if k in allowed}
        if not updates:
            return self.snapshot_detail(snapshot_id)
        sets = []
        values = []
        for key, value in updates.items():
            if key == "is_pinned":
                value = 1 if value else 0
            sets.append(f"{key} = ?")
            values.append(value)
        values.extend([self.now_iso(), snapshot_id])
        with self.connect() as conn:
            conn.execute(f"UPDATE snapshots SET {', '.join(sets)}, updated_at = ? WHERE id = ?", values)
        return self.snapshot_detail(snapshot_id)
