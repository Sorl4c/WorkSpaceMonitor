import time

try:
    import psutil
except Exception:  # pragma: no cover
    psutil = None

TERMINAL_PROCESS_NAMES = {"windowsterminal.exe", "cmd.exe", "pwsh.exe", "powershell.exe", "alacritty.exe"}
IGNORED_CHILDREN = {"conhost.exe", "openconsole.exe", "wslhost.exe", "svchost.exe"}

_context_cache = {}
CACHE_TTL = 5.0


def build_process_tree():
    if psutil is None:
        return {}, {}
    tree = {}
    all_procs = {}
    for p in psutil.process_iter(["pid", "ppid", "name"]):
        try:
            pid = p.info["pid"]
            ppid = p.info["ppid"]
            all_procs[pid] = p
            tree.setdefault(ppid, []).append(p)
        except Exception:
            pass
    return tree, all_procs


def get_descendants(pid, tree):
    descendants = []
    for child in tree.get(pid, []):
        descendants.append(child)
        descendants.extend(get_descendants(child.info["pid"], tree))
    return descendants


def get_deep_cli_context(proc, tree):
    pid = proc.info["pid"]
    now = time.time()
    if pid in _context_cache and now - _context_cache[pid]["timestamp"] < CACHE_TTL:
        return _context_cache[pid]["data"]

    descendants = get_descendants(pid, tree)
    worker = None
    for child_proc in reversed(descendants):
        try:
            name = (child_proc.info.get("name") or "").lower()
            if name not in IGNORED_CHILDREN:
                worker = {
                    "pid": child_proc.info["pid"],
                    "name": child_proc.info.get("name"),
                    "cwd": child_proc.cwd(),
                    "cmdline": child_proc.cmdline(),
                }
                break
        except Exception:
            continue

    context = {"terminal_cwd": proc.cwd() if hasattr(proc, "cwd") else None, "active_worker": worker}
    _context_cache[pid] = {"timestamp": now, "data": context}
    return context


def detect_terminals() -> list[dict]:
    if psutil is None:
        return []
    terminals = []
    tree, all_procs = build_process_tree()
    for pid, proc in all_procs.items():
        try:
            name = proc.info.get("name")
            if name and name.lower() in TERMINAL_PROCESS_NAMES:
                terminals.append({"pid": pid, "name": name, "custom_name": None, "cli_context": get_deep_cli_context(proc, tree)})
        except Exception:
            pass
    current = {t["pid"] for t in terminals}
    for cached in list(_context_cache.keys()):
        if cached not in current:
            del _context_cache[cached]
    return terminals
