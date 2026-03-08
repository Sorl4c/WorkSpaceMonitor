import psutil
import time

TERMINAL_PROCESS_NAMES = {"windowsterminal.exe", "cmd.exe", "pwsh.exe", "powershell.exe", "alacritty.exe"}
IGNORED_CHILDREN = {"conhost.exe", "openconsole.exe", "wslhost.exe", "svchost.exe"}

_context_cache = {}
CACHE_TTL = 5.0  

def build_process_tree():
    """Construye un mapa de padre a hijos en 1 sola pasada. Reduce el coste de O(N^2) a O(N)."""
    tree = {}
    all_procs = {}
    
    for p in psutil.process_iter(['pid', 'ppid', 'name']):
        try:
            pid = p.info['pid']
            ppid = p.info['ppid']
            all_procs[pid] = p
            
            if ppid not in tree:
                tree[ppid] = []
            tree[ppid].append(p)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
    return tree, all_procs

def get_descendants(pid, tree):
    """Obtiene los descendientes de forma recursiva desde el mapa en memoria (0ms de coste)."""
    descendants = []
    children = tree.get(pid, [])
    for child in children:
        descendants.append(child)
        descendants.extend(get_descendants(child.info['pid'], tree))
    return descendants

def get_deep_cli_context(proc, tree) -> dict | None:
    pid = proc.info['pid']
    global _context_cache
    now = time.time()
    
    # Retorno rápido desde la caché
    if pid in _context_cache:
        if now - _context_cache[pid]["timestamp"] < CACHE_TTL:
            return _context_cache[pid]["data"]

    try:
        # Usamos el árbol en memoria, que es casi instantáneo
        descendants = get_descendants(pid, tree)
        worker = None
        
        # Invertimos para buscar el "worker" más profundo
        for child_proc in reversed(descendants):
            try:
                name = child_proc.info['name'].lower() if child_proc.info['name'] else ""
                if name not in IGNORED_CHILDREN:
                    worker = {
                        "pid": child_proc.info['pid'],
                        "name": child_proc.info['name'],
                        "cwd": child_proc.cwd(),
                        "cmdline": child_proc.cmdline()
                    }
                    break
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue
                
        context = {
            "terminal_cwd": proc.cwd() if hasattr(proc, 'cwd') else None,
            "active_worker": worker
        }
        
        _context_cache[pid] = {"timestamp": now, "data": context}
        return context
        
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None

def detect_terminals() -> list[dict]:
    terminals = []
    
    # 1. Construimos el árbol completo del sistema una sola vez (<30ms)
    tree, all_procs = build_process_tree()
    
    # 2. Filtramos iterando sobre lo que ya tenemos en memoria
    for pid, proc in all_procs.items():
        try:
            name = proc.info['name']
            if name and name.lower() in TERMINAL_PROCESS_NAMES:
                base_info = {
                    "pid": pid, 
                    "name": name,
                    "custom_name": None # Mantenemos el campo null por compatibilidad con el frontend
                }
                # Solo extraemos los datos profundos para los terminales
                base_info["cli_context"] = get_deep_cli_context(proc, tree)
                terminals.append(base_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    # Limpiamos la caché de terminales que ya se han cerrado
    current_pids = {t["pid"] for t in terminals}
    for pid in list(_context_cache.keys()):
        if pid not in current_pids:
            del _context_cache[pid]
            
    return terminals