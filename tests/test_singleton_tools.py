import json

from src.singleton_tools import SingletonToolsService


def test_detect_singleton_tools_on_and_off(tmp_path):
    config_path = tmp_path / "singleton_tools.json"
    config_path.write_text(
        json.dumps(
            {
                "tools": [
                    {
                        "id": "vmware",
                        "label": "VMware",
                        "match": {"process_names": ["vmware.exe"], "title_contains": ["workstation"]},
                    },
                    {
                        "id": "xampp",
                        "label": "XAMPP",
                        "match": {"process_names": ["xampp-control.exe"], "title_contains": ["xampp"]},
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    service = SingletonToolsService(str(config_path))
    result = service.detect(
        {
            "desktops": [{"id": "desk-7", "number": 7}],
            "windows": [
                {
                    "hwnd": 10,
                    "title": "Ubuntu 64-bit - VMware Workstation",
                    "process_name": "vmware.exe",
                    "desktop_id": "desk-7",
                }
            ],
        }
    )

    vmware = next(item for item in result["items"] if item["id"] == "vmware")
    xampp = next(item for item in result["items"] if item["id"] == "xampp")

    assert vmware["status"] == "on"
    assert vmware["desktop_numbers"] == [7]
    assert xampp["status"] == "off"


def test_detect_singleton_tool_unknown_desktop(tmp_path):
    config_path = tmp_path / "singleton_tools.json"
    config_path.write_text(
        json.dumps(
            {
                "tools": [
                    {
                        "id": "discord",
                        "label": "Discord",
                        "match": {"process_names": ["discord.exe"], "title_contains": ["discord"]},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    service = SingletonToolsService(str(config_path))
    result = service.detect(
        {
            "desktops": [{"id": "desk-2", "number": 2}],
            "windows": [{"hwnd": 22, "title": "Discord", "process_name": "discord.exe", "desktop_id": None}],
        }
    )

    discord = result["items"][0]
    assert discord["status"] == "on"
    assert discord["desktop_numbers"] == []
    assert discord["desktop_unknown"] is True


def test_detect_singleton_tool_with_process_only(tmp_path, monkeypatch):
    config_path = tmp_path / "singleton_tools.json"
    config_path.write_text(
        json.dumps(
            {
                "tools": [
                    {
                        "id": "whatsapp",
                        "label": "WhatsApp",
                        "match": {
                            "process_names": ["whatsapp.root.exe"],
                            "title_contains": ["whatsapp"],
                            "detect_process_only": True,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    class FakeProc:
        def __init__(self, pid, name):
            self.info = {"pid": pid, "name": name}

    from src import singleton_tools as singleton_module

    monkeypatch.setattr(singleton_module, "psutil", type("FakePsutil", (), {"process_iter": staticmethod(lambda _: [FakeProc(77, "WhatsApp.Root.exe")])}))
    service = SingletonToolsService(str(config_path))
    result = service.detect({"desktops": [], "windows": []})

    whatsapp = result["items"][0]
    assert whatsapp["status"] == "on"
    assert whatsapp["window_count"] == 0
    assert whatsapp["process_count"] == 1
    assert whatsapp["desktop_unknown"] is True
