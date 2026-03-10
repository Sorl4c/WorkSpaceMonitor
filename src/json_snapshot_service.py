import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from src.project_inference import infer_project_root_for_terminal, infer_project_root_for_window


class JsonSnapshotService:
    def __init__(self, gather_state_fn: Callable[[], dict], snapshot_path: str | None = None):
        self.gather_state_fn = gather_state_fn
        self.snapshot_path = Path(snapshot_path or (Path(__file__).resolve().parent.parent / "data" / "current_desktop_snapshot.json"))
        self.snapshot_path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> dict[str, Any] | None:
        if not self.snapshot_path.exists():
            return None
        return json.loads(self.snapshot_path.read_text(encoding="utf-8"))

    def _write(self, payload: dict[str, Any]) -> None:
        self.snapshot_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")

    def capture_desktop(self, desktop_id: str, title: str | None = None, note: str | None = None) -> dict[str, Any]:
        state = self.gather_state_fn()
        desktops = state.get("desktops", [])
        windows = state.get("windows", [])
        terminals = state.get("terminals", [])

        desktop = next((d for d in desktops if d.get("id") == desktop_id), None)
        if not desktop:
            raise ValueError(f"Desktop not found: {desktop_id}")

        desktop_windows = [w for w in windows if w.get("desktop_id") == desktop_id]
        terminal_by_pid = {t.get("pid"): t for t in terminals if t.get("pid") is not None}
        desktop_terminals = [terminal_by_pid[w.get("pid")] for w in desktop_windows if w.get("pid") in terminal_by_pid]
        unique_terminals = {t["pid"]: t for t in desktop_terminals if t.get("pid") is not None}

        snapshot_windows = []
        inferred_project_roots: dict[str, int] = {}
        for window in desktop_windows:
            terminal = terminal_by_pid.get(window.get("pid"))
            project_root = infer_project_root_for_window(window, list(unique_terminals.values()))
            if project_root:
                inferred_project_roots[project_root] = inferred_project_roots.get(project_root, 0) + 1
            snapshot_windows.append(
                {
                    "hwnd": window.get("hwnd"),
                    "pid": window.get("pid"),
                    "title": window.get("title"),
                    "clean_name": window.get("clean_name"),
                    "process_name": window.get("process_name"),
                    "desktop_id": window.get("desktop_id"),
                    "rect": window.get("rect") or {},
                    "explorer_path": window.get("explorer_path"),
                    "explorer_name": window.get("explorer_name"),
                    "project_root": project_root,
                    "terminal_cwd": ((terminal or {}).get("cli_context") or {}).get("terminal_cwd"),
                }
            )

        snapshot_terminals = []
        for terminal in unique_terminals.values():
            cli_context = terminal.get("cli_context") or {}
            active_worker = cli_context.get("active_worker") or {}
            snapshot_terminals.append(
                {
                    "pid": terminal.get("pid"),
                    "name": terminal.get("name"),
                    "terminal_cwd": cli_context.get("terminal_cwd"),
                    "project_root": infer_project_root_for_terminal(terminal),
                    "active_worker": {
                        "name": active_worker.get("name"),
                        "cwd": active_worker.get("cwd"),
                        "cmdline": active_worker.get("cmdline"),
                    }
                    if active_worker
                    else None,
                }
            )

        dominant_project_root = None
        if inferred_project_roots:
            dominant_project_root = max(inferred_project_roots.items(), key=lambda item: item[1])[0]

        payload = {
            "version": 1,
            "scope": "desktop",
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "title": title or f"Desktop {desktop.get('number')}",
            "note": note or "",
            "desktop": {
                "id": desktop.get("id"),
                "number": desktop.get("number"),
                "name": desktop.get("name"),
            },
            "dominant_project_root": dominant_project_root,
            "window_count": len(snapshot_windows),
            "terminal_count": len(snapshot_terminals),
            "windows": snapshot_windows,
            "terminals": snapshot_terminals,
        }
        self._write(payload)
        return payload

    def get_current_snapshot(self) -> dict[str, Any] | None:
        return self._read()

    def build_restore_plan(self) -> dict[str, Any]:
        snapshot = self._read()
        if not snapshot:
            raise ValueError("No current desktop snapshot found")

        state = self.gather_state_fn()
        snapshot_desktop_id = (snapshot.get("desktop") or {}).get("id")
        current_windows = [w for w in state.get("windows", []) if w.get("desktop_id") == snapshot_desktop_id]
        current_titles = {(w.get("title") or "").strip().lower() for w in current_windows}
        current_explorer_paths = {
            (w.get("explorer_path") or "").strip().lower()
            for w in current_windows
            if (w.get("process_name") or "").lower() == "explorer.exe"
        }
        current_terminal_cwds = {
            ((t.get("cli_context") or {}).get("terminal_cwd") or "").strip().lower()
            for t in state.get("terminals", [])
            if any(w.get("pid") == t.get("pid") for w in current_windows)
        }

        items: list[dict[str, Any]] = []
        planned_actions: set[tuple[str, str]] = set()
        for window in snapshot.get("windows", []):
            title = (window.get("title") or "").strip().lower()
            process_name = (window.get("process_name") or "").lower()
            project_root = window.get("project_root")
            terminal_cwd = (window.get("terminal_cwd") or "").strip().lower()
            explorer_path = (window.get("explorer_path") or "").strip().lower()
            action = None

            if process_name == "explorer.exe" and explorer_path and explorer_path in current_explorer_paths:
                status = "matched"
            elif process_name == "explorer.exe" and explorer_path:
                status = "restorable"
                action = {"type": "explorer", "target": explorer_path}
            elif title and title in current_titles:
                status = "matched"
            elif process_name in {"code.exe", "cursor.exe"} and project_root:
                status = "restorable"
                action = {"type": "vscode", "target": project_root}
            elif process_name in {"windowsterminal.exe", "powershell.exe", "pwsh.exe", "cmd.exe"} and terminal_cwd:
                action_key = ("terminal", terminal_cwd)
                if action_key in planned_actions:
                    status = "pending_manual"
                else:
                    status = "restorable"
                    action = {"type": "terminal", "target": terminal_cwd}
                    planned_actions.add(action_key)
            elif terminal_cwd and terminal_cwd not in current_terminal_cwds:
                action_key = ("terminal", terminal_cwd)
                if action_key in planned_actions:
                    status = "pending_manual"
                else:
                    status = "restorable"
                    action = {"type": "terminal", "target": terminal_cwd}
                    planned_actions.add(action_key)
            elif title:
                status = "pending_manual"
            else:
                status = "unknown"

            items.append(
                {
                    "kind": "window",
                    "title": window.get("title"),
                    "process_name": window.get("process_name"),
                    "status": status,
                    "action": action,
                }
            )

        for terminal in snapshot.get("terminals", []):
            cwd = (terminal.get("terminal_cwd") or "").strip().lower()
            if not cwd:
                items.append({"kind": "terminal", "title": terminal.get("name"), "process_name": terminal.get("name"), "status": "pending_manual", "action": None})
                continue
            if cwd in current_terminal_cwds:
                status = "matched"
                action = None
            elif ("terminal", cwd) in planned_actions:
                status = "pending_manual"
                action = None
            else:
                status = "restorable"
                action = {"type": "terminal", "target": terminal.get("terminal_cwd")}
                planned_actions.add(("terminal", cwd))
            items.append({"kind": "terminal", "title": terminal.get("name"), "process_name": terminal.get("name"), "status": status, "action": action})

        summary = {k: 0 for k in ["matched", "restorable", "pending_manual", "unknown"]}
        for item in items:
            summary[item["status"]] += 1

        return {"snapshot": snapshot, "summary": summary, "items": items}

    def _go_to_desktop(self, desktop_number: int | None) -> dict[str, Any]:
        if desktop_number is None:
            return {"status": "partial", "message": "No desktop number stored"}
        if sys.platform != "win32":
            return {"status": "partial", "message": "Desktop switching only supported on Windows"}
        try:
            from pyvda import VirtualDesktop

            VirtualDesktop(desktop_number).go()
            return {"status": "success", "message": f"Desktop {desktop_number} focused"}
        except Exception as exc:
            return {"status": "partial", "message": str(exc)}

    def _launch_vscode(self, target: str) -> dict[str, Any]:
        try:
            process = subprocess.Popen(["code", target])
            return {"status": "success", "pid": process.pid}
        except Exception as exc:
            return {"status": "failed", "message": str(exc)}

    def _launch_terminal(self, cwd: str) -> dict[str, Any]:
        try:
            if sys.platform == "win32":
                process = subprocess.Popen(["cmd.exe", "/c", "start", "", "cmd.exe", "/k", f"cd /d {cwd}"], cwd=cwd, shell=False)
            else:
                process = subprocess.Popen(["bash"], cwd=cwd)
            return {"status": "success", "pid": process.pid}
        except Exception as exc:
            return {"status": "failed", "message": str(exc)}

    def _launch_explorer(self, target: str) -> dict[str, Any]:
        try:
            if sys.platform == "win32":
                process = subprocess.Popen(["explorer.exe", target])
            else:
                process = subprocess.Popen(["xdg-open", target])
            return {"status": "success", "pid": getattr(process, "pid", None)}
        except Exception as exc:
            return {"status": "failed", "message": str(exc)}

    def restore_current_snapshot(self) -> dict[str, Any]:
        plan = self.build_restore_plan()
        snapshot = plan["snapshot"]
        desktop_result = self._go_to_desktop((snapshot.get("desktop") or {}).get("number"))

        results = []
        executed_actions: set[tuple[str, str]] = set()
        for item in plan["items"]:
            if item["status"] == "matched":
                results.append({**item, "result": "success", "message": "Already present"})
                continue
            action = item.get("action")
            if item["status"] != "restorable" or not action:
                results.append({**item, "result": "manual", "message": "Manual recovery required"})
                continue
            action_key = (action["type"], str(action["target"]).lower())
            if action_key in executed_actions:
                results.append({**item, "result": "manual", "message": "Duplicate restore action skipped"})
                continue

            if action["type"] == "vscode":
                launch = self._launch_vscode(action["target"])
            elif action["type"] == "explorer":
                launch = self._launch_explorer(action["target"])
            elif action["type"] == "terminal":
                launch = self._launch_terminal(action["target"])
            else:
                launch = {"status": "failed", "message": "Unknown action"}
            executed_actions.add(action_key)

            result = "success" if launch["status"] == "success" and desktop_result["status"] == "success" else "partial"
            if launch["status"] == "failed":
                result = "manual"
            results.append({**item, "result": result, "launch": launch})

        return {"snapshot": snapshot, "desktop": desktop_result, "items": results}
