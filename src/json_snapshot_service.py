import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from shutil import which
from typing import Any, Callable

from src.desktop import create_virtual_desktop
from src.json_snapshot_inference import (
    desktop_local_roots,
    dominant_project_root,
    editor_open_elsewhere,
    infer_snapshot_terminal,
    infer_snapshot_window,
)


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
        local_roots = desktop_local_roots(desktop_windows, list(unique_terminals.values()))
        fallback_root = local_roots[0] if len(local_roots) == 1 else None

        snapshot_windows = []
        inferred_project_roots: dict[str, int] = {}
        for window in desktop_windows:
            terminal = terminal_by_pid.get(window.get("pid"))
            inferred = infer_snapshot_window(window, terminal, list(unique_terminals.values()), fallback_root)
            project_root = inferred["project_root"]
            terminal_cwd = inferred["terminal_cwd"]
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
                    "terminal_cwd": terminal_cwd,
                }
            )

        snapshot_terminals = []
        for terminal in unique_terminals.values():
            cli_context = terminal.get("cli_context") or {}
            active_worker = cli_context.get("active_worker") or {}
            inferred = infer_snapshot_terminal(terminal, fallback_root)
            snapshot_terminals.append(
                {
                    "pid": terminal.get("pid"),
                    "name": terminal.get("name"),
                    "terminal_cwd": inferred["terminal_cwd"],
                    "project_root": inferred["project_root"],
                    "active_worker": {
                        "name": active_worker.get("name"),
                        "cwd": active_worker.get("cwd"),
                        "cmdline": active_worker.get("cmdline"),
                    }
                    if active_worker
                    else None,
                }
            )

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
            "dominant_project_root": dominant_project_root(inferred_project_roots, fallback_root),
            "window_count": len(snapshot_windows),
            "terminal_count": len(snapshot_terminals),
            "windows": snapshot_windows,
            "terminals": snapshot_terminals,
        }
        self._write(payload)
        return payload

    def get_current_snapshot(self) -> dict[str, Any] | None:
        return self._read()

    def _desktop_lookup(self, state: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[int, dict[str, Any]]]:
        desktops = state.get("desktops", [])
        return (
            {desktop.get("id"): desktop for desktop in desktops if desktop.get("id") is not None},
            {desktop.get("number"): desktop for desktop in desktops if desktop.get("number") is not None},
        )

    def _resolve_target_for_plan(self, snapshot: dict[str, Any], state: dict[str, Any], target: dict[str, Any] | None = None) -> dict[str, Any]:
        target = target or {"mode": "same"}
        if target.get("resolved_desktop_number") is not None and target.get("resolved_desktop_id") is not None:
            return {
                "mode": target.get("mode") or "desktop",
                "requested_desktop_number": target.get("requested_desktop_number"),
                "resolved_desktop_number": target.get("resolved_desktop_number"),
                "resolved_desktop_id": target.get("resolved_desktop_id"),
                "created_new_desktop": bool(target.get("created_new_desktop")),
                "will_create_new": False,
            }
        mode = target.get("mode") or "same"
        _, by_number = self._desktop_lookup(state)
        snapshot_desktop = snapshot.get("desktop") or {}
        snapshot_number = snapshot_desktop.get("number")
        snapshot_id = snapshot_desktop.get("id")

        if mode == "same":
            desktop = by_number.get(snapshot_number)
            if desktop:
                return {
                    "mode": "same",
                    "requested_desktop_number": snapshot_number,
                    "resolved_desktop_number": desktop.get("number"),
                    "resolved_desktop_id": desktop.get("id"),
                    "created_new_desktop": False,
                    "will_create_new": False,
                }
            return {
                "mode": "same",
                "requested_desktop_number": snapshot_number,
                "resolved_desktop_number": snapshot_number,
                "resolved_desktop_id": snapshot_id,
                "created_new_desktop": False,
                "will_create_new": False,
            }

        if mode == "desktop":
            requested = target.get("desktop_number")
            desktop = by_number.get(requested)
            if not desktop:
                raise ValueError(f"Target desktop not found: {requested}")
            return {
                "mode": "desktop",
                "requested_desktop_number": requested,
                "resolved_desktop_number": desktop.get("number"),
                "resolved_desktop_id": desktop.get("id"),
                "created_new_desktop": False,
                "will_create_new": False,
            }

        if mode == "new":
            return {
                "mode": "new",
                "requested_desktop_number": None,
                "resolved_desktop_number": None,
                "resolved_desktop_id": None,
                "created_new_desktop": False,
                "will_create_new": True,
            }

        raise ValueError(f"Unsupported target mode: {mode}")

    def _create_target_desktop(self) -> dict[str, Any]:
        desktop = create_virtual_desktop()
        return {
            "mode": "new",
            "requested_desktop_number": None,
            "resolved_desktop_number": desktop.get("number"),
            "resolved_desktop_id": desktop.get("id"),
            "created_new_desktop": True,
            "will_create_new": False,
        }

    def build_restore_plan(self, target: dict[str, Any] | None = None) -> dict[str, Any]:
        snapshot = self._read()
        if not snapshot:
            raise ValueError("No current desktop snapshot found")

        state = self.gather_state_fn()
        resolved_target = self._resolve_target_for_plan(snapshot, state, target)
        target_desktop_id = resolved_target.get("resolved_desktop_id")
        if resolved_target.get("mode") == "new":
            current_windows = []
            current_windows_elsewhere = list(state.get("windows", []))
        else:
            current_windows = [w for w in state.get("windows", []) if w.get("desktop_id") == target_desktop_id]
            current_windows_elsewhere = [w for w in state.get("windows", []) if w.get("desktop_id") != target_desktop_id]

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
        current_terminal_cwds_elsewhere = {
            ((t.get("cli_context") or {}).get("terminal_cwd") or "").strip().lower()
            for t in state.get("terminals", [])
            if any(w.get("pid") == t.get("pid") for w in current_windows_elsewhere)
        }
        desktop_number_by_id, _ = self._desktop_lookup(state)

        def desktop_numbers_for(predicate):
            return sorted(
                {
                    desktop_number_by_id.get(window.get("desktop_id"), {}).get("number")
                    for window in current_windows_elsewhere
                    if predicate(window) and desktop_number_by_id.get(window.get("desktop_id"), {}).get("number") is not None
                }
            )

        items: list[dict[str, Any]] = []
        window_terminal_action_keys: set[tuple[str, str]] = set()
        for window in snapshot.get("windows", []):
            title = (window.get("title") or "").strip().lower()
            process_name = (window.get("process_name") or "").lower()
            project_root = window.get("project_root")
            terminal_cwd = (window.get("terminal_cwd") or "").strip().lower()
            explorer_path = (window.get("explorer_path") or "").strip().lower()
            action = None

            if process_name == "explorer.exe" and explorer_path and explorer_path in current_explorer_paths:
                status = "matched"
                existing_desktop_numbers = [resolved_target.get("resolved_desktop_number")] if resolved_target.get("resolved_desktop_number") else []
            elif process_name == "explorer.exe" and explorer_path and desktop_numbers_for(
                lambda other: (other.get("process_name") or "").lower() == "explorer.exe"
                and (other.get("explorer_path") or "").strip().lower() == explorer_path
            ):
                status = "already_open_elsewhere"
                existing_desktop_numbers = desktop_numbers_for(
                    lambda other: (other.get("process_name") or "").lower() == "explorer.exe"
                    and (other.get("explorer_path") or "").strip().lower() == explorer_path
                )
                action = {"type": "focus_existing_explorer", "target": explorer_path}
            elif process_name == "explorer.exe" and explorer_path:
                status = "restorable"
                action = {"type": "explorer", "target": explorer_path}
                existing_desktop_numbers = []
            elif title and title in current_titles:
                status = "matched"
                existing_desktop_numbers = [resolved_target.get("resolved_desktop_number")] if resolved_target.get("resolved_desktop_number") else []
            elif process_name in {"code.exe", "cursor.exe"} and editor_open_elsewhere(project_root, current_windows_elsewhere, state.get("terminals", [])):
                status = "already_open_elsewhere"
                action = {"type": "focus_existing_editor", "target": project_root}
                existing_desktop_numbers = desktop_numbers_for(
                    lambda other: (other.get("process_name") or "").lower() in {"code.exe", "cursor.exe"}
                )
            elif process_name in {"code.exe", "cursor.exe"} and project_root:
                status = "restorable"
                action = {"type": "vscode", "target": project_root}
                existing_desktop_numbers = []
            elif process_name in {"windowsterminal.exe", "powershell.exe", "pwsh.exe", "cmd.exe"} and terminal_cwd:
                if terminal_cwd in current_terminal_cwds:
                    status = "matched"
                    existing_desktop_numbers = [resolved_target.get("resolved_desktop_number")] if resolved_target.get("resolved_desktop_number") else []
                elif terminal_cwd in current_terminal_cwds_elsewhere:
                    status = "already_open_elsewhere"
                    action = {"type": "focus_existing_terminal", "target": terminal_cwd}
                    existing_desktop_numbers = desktop_numbers_for(
                        lambda other: ((other.get("process_name") or "").lower() in {"windowsterminal.exe", "powershell.exe", "pwsh.exe", "cmd.exe"})
                    )
                else:
                    status = "restorable"
                    action = {"type": "terminal", "target": terminal_cwd}
                    existing_desktop_numbers = []
                    window_terminal_action_keys.add(("terminal", terminal_cwd))
            elif terminal_cwd and terminal_cwd not in current_terminal_cwds:
                status = "restorable"
                action = {"type": "terminal", "target": terminal_cwd}
                window_terminal_action_keys.add(("terminal", terminal_cwd))
                existing_desktop_numbers = []
            elif title:
                status = "pending_manual"
                existing_desktop_numbers = []
            else:
                status = "unknown"
                existing_desktop_numbers = []

            items.append(
                {
                    "kind": "window",
                    "title": window.get("title"),
                    "process_name": window.get("process_name"),
                    "status": status,
                    "action": action,
                    "existing_desktop_numbers": existing_desktop_numbers,
                }
            )

        for terminal in snapshot.get("terminals", []):
            cwd = (terminal.get("terminal_cwd") or "").strip().lower()
            if not cwd:
                items.append(
                    {
                        "kind": "terminal",
                        "title": terminal.get("name"),
                        "process_name": terminal.get("name"),
                        "status": "pending_manual",
                        "action": None,
                        "existing_desktop_numbers": [],
                    }
                )
                continue
            if cwd in current_terminal_cwds:
                status = "matched"
                action = None
                existing_desktop_numbers = [resolved_target.get("resolved_desktop_number")] if resolved_target.get("resolved_desktop_number") else []
            elif ("terminal", cwd) in window_terminal_action_keys:
                continue
            elif cwd in current_terminal_cwds_elsewhere:
                status = "already_open_elsewhere"
                action = {"type": "focus_existing_terminal", "target": terminal.get("terminal_cwd")}
                existing_desktop_numbers = desktop_numbers_for(
                    lambda other: ((other.get("process_name") or "").lower() in {"windowsterminal.exe", "powershell.exe", "pwsh.exe", "cmd.exe"})
                )
            else:
                status = "restorable"
                action = {"type": "terminal", "target": terminal.get("terminal_cwd")}
                existing_desktop_numbers = []
            items.append(
                {
                    "kind": "terminal",
                    "title": terminal.get("name"),
                    "process_name": terminal.get("name"),
                    "status": status,
                    "action": action,
                    "existing_desktop_numbers": existing_desktop_numbers,
                }
            )

        summary = {k: 0 for k in ["matched", "restorable", "pending_manual", "unknown", "already_open_elsewhere"]}
        for item in items:
            summary[item["status"]] += 1

        return {"snapshot": snapshot, "target": resolved_target, "summary": summary, "items": items}

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
            candidates = [
                which("code"),
                which("code.cmd"),
                str(Path.home() / "AppData" / "Local" / "Programs" / "Microsoft VS Code" / "Code.exe"),
                str(Path.home() / "AppData" / "Local" / "Programs" / "Cursor" / "Cursor.exe"),
            ]
            command = next((candidate for candidate in candidates if candidate and Path(candidate).exists()), None)
            if not command:
                raise FileNotFoundError("No VS Code/Cursor executable found")
            process = subprocess.Popen([command, target])
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

    def restore_current_snapshot(self, target: dict[str, Any] | None = None) -> dict[str, Any]:
        snapshot = self._read()
        if not snapshot:
            raise ValueError("No current desktop snapshot found")

        if (target or {}).get("mode") == "new":
            resolved_target = self._create_target_desktop()
            plan = self.build_restore_plan(resolved_target)
        else:
            plan = self.build_restore_plan(target)
            resolved_target = plan["target"]

        snapshot = plan["snapshot"]
        desktop_result = self._go_to_desktop(resolved_target.get("resolved_desktop_number"))

        results = []
        executed_actions: set[tuple[str, str]] = set()
        for item in plan["items"]:
            if item["status"] == "matched":
                results.append({**item, "result": "success", "message": "Already present"})
                continue
            if item["status"] == "already_open_elsewhere":
                results.append({**item, "result": "partial", "message": "Already open on another desktop"})
                continue
            action = item.get("action")
            if item["status"] != "restorable" or not action:
                results.append({**item, "result": "manual", "message": "Manual recovery required"})
                continue
            action_key = (action["type"], str(action["target"]).lower())
            should_dedupe = action["type"] != "terminal" or item.get("kind") == "terminal"
            if should_dedupe and action_key in executed_actions:
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
            if should_dedupe:
                executed_actions.add(action_key)

            result = "success" if launch["status"] == "success" and desktop_result["status"] == "success" else "partial"
            if launch["status"] == "failed":
                result = "manual"
            results.append({**item, "result": result, "launch": launch})

        return {"snapshot": snapshot, "target": resolved_target, "desktop": desktop_result, "items": results}
