from types import SimpleNamespace
from unittest.mock import patch

from src.browser import (
    DEBUG_TABS_ENV_VAR,
    _TAB_COUNT_CACHE,
    get_browser_tab_count,
    is_supported_browser_process,
)


class FakeControl:
    def __init__(self, control_type="PaneControl", children=None, name="", class_name="", automation_id=""):
        self.ControlType = control_type
        self.ControlTypeName = control_type
        self.children = children or []
        self.Name = name
        self.ClassName = class_name
        self.AutomationId = automation_id
        self.RuntimeId = id(self)

    def GetChildren(self):
        return list(self.children)


def make_auto(control):
    control_type = SimpleNamespace(
        TabItemControl="TabItemControl",
        TabControl="TabControl",
        PaneControl="PaneControl",
        GroupControl="GroupControl",
        CustomControl="CustomControl",
    )
    return SimpleNamespace(ControlType=control_type, ControlFromHandle=lambda hwnd: control)


def wrap_in_chain(node, depth):
    current = node
    for _ in range(depth):
        current = FakeControl(children=[current])
    return current


def patch_browser_runtime(process_name="msedge.exe", foreground_hwnd=123):
    return patch.multiple(
        "src.browser.win32gui",
        IsWindow=lambda hwnd: True,
        IsWindowVisible=lambda hwnd: True,
        GetWindowText=lambda hwnd: "Example title",
        GetForegroundWindow=lambda: foreground_hwnd,
    ), patch("src.browser._get_process_name", return_value=process_name)


def test_is_supported_browser_process():
    assert is_supported_browser_process("chrome.exe") is True
    assert is_supported_browser_process("msedge.exe") is True
    assert is_supported_browser_process("comet.exe") is True
    assert is_supported_browser_process("firefox.exe") is False


@patch("src.browser.win32gui.IsWindow", return_value=False)
def test_get_browser_tab_count_rejects_invalid_window(mock_is_window):
    assert get_browser_tab_count(0) is None


@patch("src.browser.win32gui.IsWindow", return_value=True)
@patch("src.browser.win32gui.IsWindowVisible", return_value=True)
@patch("src.browser._get_process_name", return_value="msedge.exe")
def test_get_browser_tab_count_returns_none_without_uiautomation(
    mock_process_name,
    mock_is_window_visible,
    mock_is_window,
):
    with patch("builtins.__import__", side_effect=ImportError("missing")):
        assert get_browser_tab_count(123) is None


def test_get_browser_tab_count_returns_direct_tab_count():
    _TAB_COUNT_CACHE.clear()
    level_8_tabs = [FakeControl(control_type="TabItemControl") for _ in range(3)]
    root = wrap_in_chain(FakeControl(children=level_8_tabs), 7)
    auto = make_auto(root)
    window_patches, process_patch = patch_browser_runtime()

    with window_patches, process_patch, patch.dict("sys.modules", {"uiautomation": auto}):
        assert get_browser_tab_count(123) == 3


def test_get_browser_tab_count_uses_container_fallback_for_foreground_window():
    _TAB_COUNT_CACHE.clear()
    tab_strip = FakeControl(
        control_type="CustomControl",
        name="Tab strip region",
        class_name="TabStrip",
        children=[wrap_in_chain(FakeControl(control_type="TabItemControl"), 2) for _ in range(4)],
    )
    root = wrap_in_chain(tab_strip, 6)
    auto = make_auto(root)
    window_patches, process_patch = patch_browser_runtime()

    with window_patches, process_patch, patch.dict("sys.modules", {"uiautomation": auto}):
        assert get_browser_tab_count(123) == 4


def test_get_browser_tab_count_skips_expensive_fallback_for_non_foreground_window():
    _TAB_COUNT_CACHE.clear()
    deep_tabs = [wrap_in_chain(FakeControl(control_type="TabItemControl"), 2) for _ in range(2)]
    root = wrap_in_chain(FakeControl(name="Tab strip", class_name="TabStrip", control_type="CustomControl", children=deep_tabs), 6)
    auto = make_auto(root)
    window_patches, process_patch = patch_browser_runtime(foreground_hwnd=999)

    with window_patches, process_patch, patch.dict("sys.modules", {"uiautomation": auto}):
        assert get_browser_tab_count(123) == 2


def test_get_browser_tab_count_returns_none_for_unsupported_process():
    _TAB_COUNT_CACHE.clear()
    root = FakeControl(children=[FakeControl(control_type="TabItemControl")])
    auto = make_auto(root)
    window_patches, process_patch = patch_browser_runtime(process_name="notepad.exe")

    with window_patches, process_patch, patch.dict("sys.modules", {"uiautomation": auto}):
        assert get_browser_tab_count(123) is None


def test_get_browser_tab_count_returns_none_when_uia_raises():
    _TAB_COUNT_CACHE.clear()
    auto = SimpleNamespace(
        ControlType=SimpleNamespace(TabItemControl="TabItemControl"),
        ControlFromHandle=lambda hwnd: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    window_patches, process_patch = patch_browser_runtime()

    with window_patches, process_patch, patch.dict("sys.modules", {"uiautomation": auto}):
        assert get_browser_tab_count(123) is None


def test_get_browser_tab_count_debug_output_includes_key_fields(capsys):
    _TAB_COUNT_CACHE.clear()
    root = wrap_in_chain(FakeControl(children=[FakeControl(control_type="TabItemControl"), FakeControl(control_type="TabItemControl")]), 7)
    auto = make_auto(root)
    window_patches, process_patch = patch_browser_runtime(process_name="chrome.exe")

    with (
        window_patches,
        process_patch,
        patch.dict("sys.modules", {"uiautomation": auto}),
        patch.dict("os.environ", {DEBUG_TABS_ENV_VAR: "1"}, clear=False),
    ):
        assert get_browser_tab_count(123) == 2

    output = capsys.readouterr().out
    assert "hwnd=123" in output
    assert "process_name='chrome.exe'" in output
    assert "direct_tab_items=2" in output


def test_get_browser_tab_count_reuses_cached_value_without_requerying_uia():
    _TAB_COUNT_CACHE.clear()
    root = wrap_in_chain(FakeControl(children=[FakeControl(control_type="TabItemControl") for _ in range(5)]), 7)
    auto = make_auto(root)
    window_patches, process_patch = patch_browser_runtime()

    with window_patches, process_patch, patch.dict("sys.modules", {"uiautomation": auto}):
        assert get_browser_tab_count(123) == 5

    with (
        window_patches,
        process_patch,
        patch("src.browser._get_uiautomation_module", side_effect=RuntimeError("should not hit UIA")),
    ):
        assert get_browser_tab_count(123) == 5
