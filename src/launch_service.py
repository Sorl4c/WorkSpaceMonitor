import subprocess
import sys
from typing import Any

from src.persistence import ALLOWED_ZONES, SQLitePersistence

ZONE_TO_RATIO = {
    "maximized": (0.0, 0.0, 1.0, 1.0),
    "left": (0.0, 0.0, 0.5, 1.0),
    "right": (0.5, 0.0, 0.5, 1.0),
    "top-left": (0.0, 0.0, 0.5, 0.5),
    "top-right": (0.5, 0.0, 0.5, 0.5),
    "bottom-left": (0.0, 0.5, 0.5, 0.5),
    "bottom-right": (0.5, 0.5, 0.5, 0.5),
    "center": (0.2, 0.15, 0.6, 0.7),
}


class LaunchService:
    def __init__(self, persistence: SQLitePersistence):
        self.persistence = persistence

    def _desktop_attempt(self, desktop_number: int | None) -> dict[str, Any]:
        if desktop_number is None:
            return {"status": "success", "message": "No desktop preference"}
        if sys.platform != "win32":
            return {"status": "partial", "message": "Desktop targeting only available on Windows"}
        try:
            from pyvda import VirtualDesktop

            VirtualDesktop(desktop_number).go()
            return {"status": "success", "message": f"Desktop {desktop_number} targeted"}
        except Exception as exc:
            return {"status": "partial", "message": f"Desktop targeting failed: {exc}"}

    def zone_rect(self, zone: str, screen_rect: tuple[int, int, int, int] = (0, 0, 1920, 1080)) -> dict[str, int]:
        if zone not in ALLOWED_ZONES:
            zone = "center"
        x, y, w, h = screen_rect
        rx, ry, rw, rh = ZONE_TO_RATIO[zone]
        return {"x": int(x + w * rx), "y": int(y + h * ry), "width": int(w * rw), "height": int(h * rh)}

    def _launch_terminal(self, profile: dict[str, Any]) -> dict[str, Any]:
        cmd = profile.get("launch_command")
        shell = profile.get("shell") or ("cmd" if sys.platform == "win32" else "bash")
        cwd = profile.get("cwd") or "."
        try:
            if cmd:
                process = subprocess.Popen([shell, "/c", cmd] if sys.platform == "win32" else [shell, "-lc", cmd], cwd=cwd)
            else:
                process = subprocess.Popen([shell], cwd=cwd)
            return {"status": "success", "pid": process.pid}
        except Exception as exc:
            return {"status": "failed", "message": str(exc)}

    def _launch_app(self, profile: dict[str, Any], project: dict[str, Any]) -> dict[str, Any]:
        app_type = profile.get("app_type")
        launch_target = profile.get("launch_target") or project.get("root_path")
        args = profile.get("launch_args") or []
        try:
            if app_type == "vscode":
                process = subprocess.Popen(["code", launch_target, *args])
            elif app_type == "explorer":
                process = subprocess.Popen(["explorer", launch_target])
            elif app_type == "browser":
                process = subprocess.Popen(["start", launch_target], shell=True)
            else:
                command = [launch_target, *args] if launch_target else args
                process = subprocess.Popen(command)
            return {"status": "success", "pid": getattr(process, "pid", None)}
        except Exception as exc:
            return {"status": "failed", "message": str(exc)}

    def launch_project(self, project_id: int) -> dict[str, Any]:
        project = self.persistence.get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        items = []
        desktop_result = self._desktop_attempt(project.get("preferred_desktop_number"))

        for app in [a for a in project["app_profiles"] if a.get("auto_launch", 1)]:
            launch = self._launch_app(app, project)
            placement = {
                "status": "partial" if app.get("preferred_zone") else "success",
                "zone": app.get("preferred_zone"),
                "target_rect": self.zone_rect(app.get("preferred_zone", "center")),
            }
            if launch["status"] == "failed":
                item_status = "failed"
            elif placement["status"] == "partial" or desktop_result["status"] == "partial":
                item_status = "partial"
            else:
                item_status = "success"
            items.append({"kind": "app", "profile_id": app["id"], "launch": launch, "placement": placement, "status": item_status})

        for terminal in [t for t in project["terminal_profiles"] if t.get("auto_launch", 1)]:
            launch = self._launch_terminal(terminal)
            placement = {
                "status": "partial" if terminal.get("preferred_zone") else "success",
                "zone": terminal.get("preferred_zone"),
                "target_rect": self.zone_rect(terminal.get("preferred_zone", "center")),
            }
            if launch["status"] == "failed":
                item_status = "failed"
            elif placement["status"] == "partial" or desktop_result["status"] == "partial":
                item_status = "partial"
            else:
                item_status = "success"
            items.append(
                {"kind": "terminal", "profile_id": terminal["id"], "launch": launch, "placement": placement, "status": item_status}
            )

        return {"project_id": project_id, "desktop": desktop_result, "items": items}
