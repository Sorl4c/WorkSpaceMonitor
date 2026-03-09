from datetime import datetime, timezone
from typing import Callable

from src.persistence import SQLitePersistence
from src.project_inference import (
    infer_project_candidates,
    infer_project_root_for_terminal,
    infer_project_root_for_window,
    infer_window_hwnd_for_terminal,
)


class SnapshotService:
    def __init__(self, persistence: SQLitePersistence, gather_state_fn: Callable[[], dict], app_version: str = "dev"):
        self.persistence = persistence
        self.gather_state_fn = gather_state_fn
        self.app_version = app_version

    def _classify(self, title: str, terminal_pid: int | None, terminal_lookup: set[int]) -> tuple[str, str, str]:
        title_l = (title or "").lower()
        if terminal_pid is not None and terminal_pid in terminal_lookup:
            return "terminal", "generic", "medium"
        if any(kw in title_l for kw in ["vscode", "visual studio code", "cursor"]):
            return "code", "editor", "high"
        if any(kw in title_l for kw in ["chrome", "edge", "firefox"]):
            return "web", "browsing", "medium"
        return "system", "noise", "low"

    def capture_and_persist(self, capture_mode: str = "manual") -> dict:
        state = self.gather_state_fn()
        desktops = state.get("desktops", [])
        windows = state.get("windows", [])
        terminals = state.get("terminals", [])

        projects = infer_project_candidates(terminals, windows)
        project_ids = {p["root_path"]: self.persistence.upsert_project(p["root_path"], p["inferred_name"]) for p in projects}

        captured_at = datetime.now(timezone.utc).isoformat()
        terminal_pid_lookup = {t.get("pid") for t in terminals if t.get("pid") is not None}

        payload = {
            "snapshot": {
                "capture_mode": capture_mode,
                "captured_at": captured_at,
                "app_version": self.app_version,
                "status": "valid",
                "desktop_count": len(desktops),
                "window_count": len(windows),
                "terminal_count": len(terminals),
                "notes": {"focus_bug_risk": "Cross-desktop focus/taskbar flashing tracked during jump/focus sequence."},
            },
            "desktops": [
                {
                    "desktop_guid": d.get("id"),
                    "desktop_number": d.get("number"),
                    "desktop_name": d.get("name"),
                    "dominant_project_id": None,
                    "summary": {},
                }
                for d in desktops
            ],
            "windows": [],
            "terminals": [],
        }

        desktop_project_counts: dict[str, dict[int, int]] = {}
        for window in windows:
            semantic_type, semantic_subtype, importance = self._classify(
                window.get("title", ""),
                window.get("pid"),
                terminal_pid_lookup,
            )
            project_root = infer_project_root_for_window(window, terminals)
            project_id = project_ids.get(project_root) if project_root else None
            desktop_guid = window.get("desktop_id")
            if desktop_guid and project_id:
                desktop_project_counts.setdefault(desktop_guid, {})
                desktop_project_counts[desktop_guid][project_id] = desktop_project_counts[desktop_guid].get(project_id, 0) + 1
            payload["windows"].append(
                {
                    "desktop_guid": desktop_guid,
                    "hwnd_at_capture": window.get("hwnd"),
                    "pid_at_capture": window.get("pid"),
                    "process_name": window.get("process_name"),
                    "title": window.get("title"),
                    "clean_name": window.get("clean_name"),
                    "semantic_type": semantic_type,
                    "semantic_subtype": semantic_subtype,
                    "importance": importance,
                    "project_id": project_id,
                    "restore_hint": {
                        "title": window.get("title"),
                        "project_root": project_root,
                        "desktop_guid": desktop_guid,
                    },
                }
            )

        for desktop in payload["desktops"]:
            project_counts = desktop_project_counts.get(desktop["desktop_guid"], {})
            if project_counts:
                desktop["dominant_project_id"] = max(project_counts.items(), key=lambda item: item[1])[0]
            desktop["summary"] = {
                "window_count": len([w for w in payload["windows"] if w.get("desktop_guid") == desktop["desktop_guid"]]),
                "project_count": len(project_counts),
            }

        for terminal in terminals:
            cli_context = terminal.get("cli_context") or {}
            project_root = infer_project_root_for_terminal(terminal)
            payload["terminals"].append(
                {
                    "window_hwnd": infer_window_hwnd_for_terminal(terminal, windows),
                    "terminal_pid": terminal.get("pid"),
                    "terminal_name": terminal.get("name"),
                    "terminal_cwd": cli_context.get("terminal_cwd"),
                    "active_worker": cli_context.get("active_worker"),
                    "project_root": project_root,
                }
            )

        snapshot_id = self.persistence.create_snapshot(payload)
        return {"snapshot_id": snapshot_id, "captured_at": captured_at}

    def build_restore_plan(self, snapshot_id: int, current_state: dict) -> dict:
        detail = self.persistence.snapshot_detail(snapshot_id)
        if not detail:
            raise ValueError(f"Snapshot not found: {snapshot_id}")

        current_titles = {(w.get("title") or "").strip().lower() for w in current_state.get("windows", [])}
        items = []
        for window in detail["windows"]:
            title = (window.get("title") or "").strip().lower()
            process_name = (window.get("process_name") or "").lower()
            if title and title in current_titles:
                status = "matched"
            elif process_name in {"code.exe", "cursor.exe", "explorer.exe", "windowsterminal.exe"}:
                status = "restorable"
            elif title:
                status = "pending_manual"
            else:
                status = "unknown"
            items.append({
                "window_snapshot_id": window.get("id"),
                "title": window.get("title"),
                "process_name": window.get("process_name"),
                "status": status,
            })

        counts = {k: 0 for k in ["matched", "restorable", "pending_manual", "unknown"]}
        for item in items:
            counts[item["status"]] += 1
        return {"snapshot_id": snapshot_id, "summary": counts, "items": items}
