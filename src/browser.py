import os
import time

import psutil
import win32gui
import win32process


BROWSER_PROCESS_NAMES = {"chrome.exe", "msedge.exe", "comet.exe"}
DEBUG_TABS_ENV_VAR = "WORKSPACE_MONITOR_DEBUG_TABS"
DIRECT_TAB_DEPTH = 8
FOREGROUND_FALLBACK_DEPTH = 10
CONTAINER_SEARCH_DEPTH = 7
CONTAINER_TAB_DEPTH = 3
CACHE_TTL_SECONDS = 300
CHROMIUM_CONTAINER_TYPES = ("TabControl", "PaneControl", "GroupControl", "CustomControl")
GENERIC_CONTAINER_TYPES = ("TabControl", "PaneControl", "GroupControl")
_TAB_COUNT_CACHE: dict[tuple[int, str | None, str], tuple[float, int | None]] = {}


def is_supported_browser_process(process_name: str | None) -> bool:
    return (process_name or "").lower() in BROWSER_PROCESS_NAMES


def _is_tab_debug_enabled() -> bool:
    return os.getenv(DEBUG_TABS_ENV_VAR, "").strip().lower() in {"1", "true", "yes", "on"}


def _debug_browser_tab_probe(
    *,
    hwnd: int,
    process_name: str | None,
    title: str,
    direct_count: int | None,
    fallback_count: int | None,
    strategy: str,
    elapsed_ms: float,
    error: Exception | None = None,
) -> None:
    if not _is_tab_debug_enabled():
        return

    message = (
        f"[DEBUG][tabs] hwnd={hwnd} process_name={process_name!r} "
        f"title={title!r} direct_tab_items={direct_count} "
        f"fallback_tab_items={fallback_count} strategy={strategy} "
        f"elapsed_ms={elapsed_ms:.2f}"
    )
    if error is not None:
        message = f"{message} error={type(error).__name__}: {error}"
    print(message)


def _get_uiautomation_module():
    try:
        import uiautomation as auto
    except Exception:
        return None
    return auto


def _get_window_title(hwnd: int) -> str:
    try:
        return win32gui.GetWindowText(hwnd) or ""
    except Exception:
        return ""


def _get_process_name(hwnd: int) -> str | None:
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return psutil.Process(pid).name().lower()
    except Exception:
        return None


def _iter_descendants(ctrl, max_depth: int):
    queue = [(ctrl, 0)]

    while queue:
        current, depth = queue.pop(0)
        yield current, depth

        if depth >= max_depth:
            continue

        try:
            children = current.GetChildren()
        except Exception:
            continue

        for child in children:
            queue.append((child, depth + 1))


def _matches_control_type(node, control_type, control_type_name: str) -> bool:
    try:
        if getattr(node, "ControlType", None) == control_type:
            return True
    except Exception:
        pass
    return getattr(node, "ControlTypeName", None) == control_type_name


def _count_tab_items(ctrl, auto, depth: int) -> int | None:
    count = 0
    for node, _ in _iter_descendants(ctrl, depth):
        if _matches_control_type(node, auto.ControlType.TabItemControl, "TabItemControl"):
            count += 1
    return count or None


def _iter_candidate_controls(ctrl, auto, process_name: str | None):
    container_types = CHROMIUM_CONTAINER_TYPES if process_name in BROWSER_PROCESS_NAMES else GENERIC_CONTAINER_TYPES
    control_type_map = {
        control_type_name: getattr(auto.ControlType, control_type_name, None)
        for control_type_name in container_types
    }

    for candidate, depth in _iter_descendants(ctrl, CONTAINER_SEARCH_DEPTH):
        if depth == 0:
            continue
        for control_type_name, control_type in control_type_map.items():
            if control_type is None:
                continue
            if _matches_control_type(candidate, control_type, control_type_name):
                yield candidate, control_type_name
                break


def _score_candidate(candidate, control_type_name: str) -> tuple[int, str]:
    try:
        name = (getattr(candidate, "Name", "") or "").lower()
    except Exception:
        name = ""
    try:
        class_name = (getattr(candidate, "ClassName", "") or "").lower()
    except Exception:
        class_name = ""
    try:
        automation_id = (getattr(candidate, "AutomationId", "") or "").lower()
    except Exception:
        automation_id = ""

    score = 0
    if "tab" in name:
        score += 3
    if "tab" in class_name or "strip" in class_name:
        score += 3
    if "tab" in automation_id or "strip" in automation_id:
        score += 2
    if "strip" in name or "row" in name:
        score += 1
    if control_type_name == "TabControl":
        score += 2
    elif control_type_name == "CustomControl":
        score += 1
    return score, f"{name}|{class_name}|{automation_id}"


def _find_candidate_tab_containers(ctrl, auto, process_name: str | None) -> list:
    candidates: list = []
    for candidate, control_type_name in _iter_candidate_controls(ctrl, auto, process_name):
        score, name = _score_candidate(candidate, control_type_name)
        if score <= 0 and control_type_name not in {"TabControl", "CustomControl"}:
            continue
        candidates.append((score, name, candidate))

    candidates.sort(key=lambda item: item[0], reverse=True)
    return [candidate for _, _, candidate in candidates[:6]]


def _count_tabs_in_candidates(candidates: list, auto) -> int | None:
    best_count = None
    for candidate in candidates:
        count = _count_tab_items(candidate, auto, CONTAINER_TAB_DEPTH)
        if count is None or count <= 0:
            continue
        if best_count is None or count > best_count:
            best_count = count
    return best_count


def _get_cached_tab_count(hwnd: int, process_name: str | None, title: str) -> int | None | object:
    cache_key = (hwnd, process_name, title)
    cached_entry = _TAB_COUNT_CACHE.get(cache_key)
    if cached_entry is None:
        return _CACHE_MISS

    cached_at, cached_value = cached_entry
    if (time.perf_counter() - cached_at) > CACHE_TTL_SECONDS:
        _TAB_COUNT_CACHE.pop(cache_key, None)
        return _CACHE_MISS

    return cached_value


def _store_cached_tab_count(hwnd: int, process_name: str | None, title: str, value: int | None) -> None:
    _TAB_COUNT_CACHE[(hwnd, process_name, title)] = (time.perf_counter(), value)


_CACHE_MISS = object()


def get_browser_tab_count(hwnd: int) -> int | None:
    """Count browser tabs exposed through UI Automation for a window handle."""
    started_at = time.perf_counter()
    process_name = None
    title = ""
    direct_count = None
    fallback_count = None
    strategy = "none"

    if not win32gui.IsWindow(hwnd):
        _debug_browser_tab_probe(
            hwnd=hwnd,
            process_name=process_name,
            title=title,
            direct_count=direct_count,
            fallback_count=fallback_count,
            strategy="invalid_window",
            elapsed_ms=(time.perf_counter() - started_at) * 1000,
        )
        return None

    try:
        if not win32gui.IsWindowVisible(hwnd):
            strategy = "hidden_window"
            return None

        process_name = _get_process_name(hwnd)
        title = _get_window_title(hwnd)
        if not is_supported_browser_process(process_name):
            strategy = "unsupported_process"
            return None

        cached_count = _get_cached_tab_count(hwnd, process_name, title)
        if cached_count is not _CACHE_MISS:
            strategy = "cached"
            return cached_count

        auto = _get_uiautomation_module()
        if auto is None:
            strategy = "uia_missing"
            return None

        ctrl = auto.ControlFromHandle(hwnd)

        direct_count = _count_tab_items(ctrl, auto, DIRECT_TAB_DEPTH)
        if direct_count is not None and direct_count > 0:
            strategy = "direct"
            _store_cached_tab_count(hwnd, process_name, title, direct_count)
            return direct_count

        fallback_count = _count_tab_items(ctrl, auto, FOREGROUND_FALLBACK_DEPTH)
        if fallback_count is not None and fallback_count > 0:
            strategy = "direct_deep"
            _store_cached_tab_count(hwnd, process_name, title, fallback_count)
            return fallback_count

        candidates = _find_candidate_tab_containers(ctrl, auto, process_name)
        fallback_count = _count_tabs_in_candidates(candidates, auto)
        if fallback_count is not None and fallback_count > 0:
            strategy = "container_fallback"
            _store_cached_tab_count(hwnd, process_name, title, fallback_count)
            return fallback_count

        strategy = "not_found"
        _store_cached_tab_count(hwnd, process_name, title, None)
        return None
    except Exception as exc:
        _debug_browser_tab_probe(
            hwnd=hwnd,
            process_name=process_name,
            title=title,
            direct_count=direct_count,
            fallback_count=fallback_count,
            strategy="exception",
            elapsed_ms=(time.perf_counter() - started_at) * 1000,
            error=exc,
        )
        return None
    finally:
        if strategy != "exception":
            _debug_browser_tab_probe(
                hwnd=hwnd,
                process_name=process_name,
                title=title,
                direct_count=direct_count,
                fallback_count=fallback_count,
                strategy=strategy,
                elapsed_ms=(time.perf_counter() - started_at) * 1000,
            )
