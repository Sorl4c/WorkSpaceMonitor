import json
from pathlib import Path
from typing import Any

try:
    import psutil
except Exception:  # pragma: no cover
    psutil = None


DEFAULT_SINGLETON_TOOLS = {
    "tools": [
        {
            "id": "vmware",
            "label": "VMware",
            "match": {"process_names": ["vmware.exe"], "title_contains": ["vmware", "workstation"]},
        },
        {
            "id": "xampp",
            "label": "XAMPP",
            "match": {"process_names": ["xampp-control.exe"], "title_contains": ["xampp control panel", "xampp"]},
        },
        {
            "id": "discord",
            "label": "Discord",
            "match": {"process_names": ["discord.exe"], "title_contains": ["discord"], "detect_process_only": True},
        },
        {
            "id": "whatsapp",
            "label": "WhatsApp",
            "match": {
                "process_names": ["whatsapp.exe", "whatsapp.root.exe"],
                "title_contains": ["whatsapp"],
                "detect_process_only": True,
            },
        },
        {
            "id": "dbeaver",
            "label": "DBeaver",
            "match": {"process_names": ["dbeaver.exe", "dbeaver-ce.exe"], "title_contains": ["dbeaver"]},
        },
    ]
}


class SingletonToolsService:
    def __init__(self, config_path: str | None = None):
        self.config_path = Path(config_path or (Path(__file__).resolve().parent.parent / "data" / "singleton_tools.json"))

    def _fallback(self) -> list[dict[str, Any]]:
        return DEFAULT_SINGLETON_TOOLS["tools"]

    def _load_config(self) -> list[dict[str, Any]]:
        if not self.config_path.exists():
            return self._fallback()
        try:
            payload = json.loads(self.config_path.read_text(encoding="utf-8"))
        except Exception:
            return self._fallback()

        tools = payload.get("tools")
        if not isinstance(tools, list):
            return self._fallback()

        cleaned: list[dict[str, Any]] = []
        for tool in tools:
            if not isinstance(tool, dict):
                continue
            tool_id = (tool.get("id") or "").strip()
            label = (tool.get("label") or tool_id).strip()
            match = tool.get("match") or {}
            process_names = [str(name).strip().lower() for name in match.get("process_names", []) if str(name).strip()]
            title_contains = [str(text).strip().lower() for text in match.get("title_contains", []) if str(text).strip()]
            detect_process_only = bool(match.get("detect_process_only"))
            if not tool_id or (not process_names and not title_contains):
                continue
            cleaned.append(
                {
                    "id": tool_id,
                    "label": label or tool_id,
                    "match": {
                        "process_names": process_names,
                        "title_contains": title_contains,
                        "detect_process_only": detect_process_only,
                    },
                }
            )
        return cleaned or self._fallback()

    def _window_matches(self, window: dict[str, Any], tool: dict[str, Any]) -> bool:
        match = tool.get("match") or {}
        process_name = (window.get("process_name") or "").strip().lower()
        title = (window.get("title") or "").strip().lower()
        process_names = match.get("process_names") or []
        title_contains = match.get("title_contains") or []
        if process_names:
            if process_name in process_names:
                return True
            if process_name:
                return False
        return any(token in title for token in title_contains)

    def _process_matches(self, process_name: str, tool: dict[str, Any]) -> bool:
        match = tool.get("match") or {}
        process_names = match.get("process_names") or []
        lowered = (process_name or "").strip().lower()
        return lowered in process_names

    def _detect_process_only(self, tool: dict[str, Any]) -> list[dict[str, Any]]:
        match = tool.get("match") or {}
        if not match.get("detect_process_only") or psutil is None:
            return []
        matches: list[dict[str, Any]] = []
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                name = proc.info.get("name") or ""
                if self._process_matches(name, tool):
                    matches.append({"pid": proc.info["pid"], "process_name": name})
            except Exception:
                continue
        return matches

    def detect(self, state: dict[str, Any]) -> dict[str, Any]:
        desktops = state.get("desktops", [])
        windows = state.get("windows", [])
        desktop_number_by_id = {desktop.get("id"): desktop.get("number") for desktop in desktops}
        items: list[dict[str, Any]] = []

        for tool in sorted(self._load_config(), key=lambda item: item["label"].lower()):
            matches = [window for window in windows if self._window_matches(window, tool)]
            process_matches = self._detect_process_only(tool) if not matches else []
            desktop_numbers = sorted(
                {
                    desktop_number_by_id[window.get("desktop_id")]
                    for window in matches
                    if window.get("desktop_id") in desktop_number_by_id and desktop_number_by_id[window.get("desktop_id")] is not None
                }
            )
            desktop_unknown = any(window.get("desktop_id") not in desktop_number_by_id for window in matches) or bool(process_matches)
            items.append(
                {
                    "id": tool["id"],
                    "label": tool["label"],
                    "status": "on" if matches or process_matches else "off",
                    "desktop_numbers": desktop_numbers,
                    "desktop_unknown": desktop_unknown,
                    "window_count": len(matches),
                    "process_count": len(process_matches),
                    "matches": [
                        {
                            "hwnd": match.get("hwnd"),
                            "title": match.get("title"),
                            "process_name": match.get("process_name"),
                            "desktop_number": desktop_number_by_id.get(match.get("desktop_id")),
                        }
                        for match in matches
                    ],
                }
            )

        return {"items": items}
