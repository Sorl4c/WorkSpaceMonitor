document.addEventListener('alpine:init', () => {
     Alpine.store('wm', {
        mode: 'live',
        viewMode: 'detail',
        online: false,
        lastUpdate: Date.now(),
        activeDesktopId: null,
        favorites: JSON.parse(localStorage.getItem('wm_favorites') || '[]'),
        recentSnapshots: [],
        latestSnapshot: null,
        savingSnapshot: false,
        
        // Datos brutos
        raw: { desktops: [], windows: [], terminals: [] },
        
        // Datos procesados (Cache para velocidad instantánea)
        processed: {
            desktops: [],
            normalizedWindows: [],
            byCategory: []
        },

        init() {
            this.refresh();
            this.loadRecentSnapshots(); 
            setInterval(() => { this.lastUpdate = Date.now(); }, 5000);
        },

        async refresh() {
            this.online = 'loading';
            try {
                const response = await fetch('/api/snapshot', { cache: 'no-store' });
                if (!response.ok) {
                    throw new Error(`Snapshot request failed with ${response.status}`);
                }

                const data = await response.json();
                this.applyIncomingState(data);
                this.online = true;
            } catch (e) {
                const isOffline = e instanceof TypeError;
                if (isOffline) {
                    console.warn('WM Store: backend offline or unreachable during refresh');
                } else {
                    console.error('WM Store: Refresh Error', e);
                }
                this.online = false;
            }
        },

        applyIncomingState(payload) {
            this.raw.desktops = payload.desktops || [];
            this.raw.windows = payload.windows || [];
            this.raw.terminals = payload.terminals || [];
            
            // --- PROCESAMIENTO ÚNICO (Aquí ahorramos CPU) ---
            
            // 1. Normalizar ventanas
            this.processed.normalizedWindows = this.raw.windows.map(win => {
                const terminal = this.raw.terminals.find(t => t.pid === win.pid);
                const type = this.classify(win, terminal);
                const extMatch = (win.title || "").match(/\.([a-z0-9]{1,10})\b/i);
                return {
                    ...win,
                    terminalName: terminal ? (terminal.custom_name || win.clean_name || win.title) : (win.clean_name || win.title),
                    cli_context: terminal ? terminal.cli_context : null,
                    semanticType: type.main,
                    semanticSubType: type.sub,
                    importance: type.importance,
                    extension: extMatch ? extMatch[0].toLowerCase() : null
                };
            });

            // 2. Procesar Escritorios con sus Buckets
            this.processed.desktops = this.raw.desktops.map(d => {
                const wins = this.processed.normalizedWindows.filter(w => w.desktop_id === d.id);
                
                const summary = [];
                const counts = {
                    term: wins.filter(w => w.semanticType === 'terminal').length,
                    cod: wins.filter(w => w.semanticType === 'code').length,
                    web: wins.filter(w => w.semanticType === 'web').length
                };
                if (counts.term) summary.push(`${counts.term} term`);
                if (counts.cod) summary.push(`${counts.cod} cód`);
                if (counts.web) summary.push(`${counts.web} web`);

                const fileStats = {};
                wins.filter(w => w.extension).forEach(w => {
                    fileStats[w.extension] = (fileStats[w.extension] || 0) + 1;
                });

                const catCounts = {};
                wins.forEach(w => catCounts[w.semanticType] = (catCounts[w.semanticType] || 0) + 1);
                const dominantCategory = Object.entries(catCounts).sort((a,b) => b[1]-a[1])[0]?.[0] || 'noise';

                return {
                    ...d,
                    windowCount: wins.length,
                    hasActivity: wins.length > 0,
                    semanticSummary: summary.length > 0 ? summary.join(' · ') : 'vacío',
                    fileStats: fileStats,
                    dominantCategory: dominantCategory,
                    buckets: {
                        terminal: wins.filter(w => w.semanticType === 'terminal'),
                        code: {
                            files: wins.filter(w => w.semanticType === 'code' && w.semanticSubType === 'editor'),
                            tools: wins.filter(w => w.semanticType === 'code' && w.semanticSubType === 'tool')
                        },
                        web: {
                            apps: wins.filter(w => w.semanticType === 'web' && w.semanticSubType === 'app'),
                            browsing: wins.filter(w => w.semanticType === 'web' && w.semanticSubType === 'browsing')
                        },
                        files: wins.filter(w => w.semanticType === 'files'),
                        comms: wins.filter(w => w.semanticType === 'comms'),
                        system: wins.filter(w => w.semanticType === 'system'),
                        noise: wins.filter(w => w.semanticType === 'noise')
                    }
                };
            }).sort((a, b) => a.number - b.number);

            // 3. Procesar Categorías (Matrix View)
            const categories = [
                { id: 'terminal', label: 'Terminals', icon: 'terminal', color: 'var(--c-terminal)' },
                { id: 'code', label: 'Development', icon: 'code', color: 'var(--c-code)' },
                { id: 'web', label: 'Web & Research', icon: 'globe', color: 'var(--c-web)' },
                { id: 'files', label: 'Files', icon: 'folder', color: 'var(--c-files)' },
                { id: 'comms', label: 'Communication', icon: 'message-square', color: 'var(--c-comms)' },
                { id: 'system', label: 'System', icon: 'settings', color: 'var(--c-system)' },
                { id: 'noise', label: 'Noise', icon: 'minus', color: 'rgba(107, 114, 128, 0.5)' }
            ];

            this.processed.byCategory = categories.map(cat => {
                const wins = this.processed.normalizedWindows.filter(w => w.semanticType === cat.id);
                const byDesktop = [];
                this.processed.desktops.forEach(d => {
                    const dWins = wins.filter(w => w.desktop_id === d.id);
                    if (dWins.length > 0) {
                        byDesktop.push({ desktopName: d.name || `Desktop ${d.number}`, windows: dWins });
                    }
                });
                return { ...cat, groups: byDesktop, totalCount: wins.length };
            });

            // Seleccionar primer escritorio si no hay uno activo
            if (!this.activeDesktopId && this.processed.desktops.length > 0) {
                this.activeDesktopId = this.processed.desktops[0].id;
            }
        },

        classify(win, terminal) {
            const title = (win.title || "").toLowerCase();
            const hasAny = (keywords) => keywords.some((kw) => title.includes(kw));
            const codeEditorKeywords = ['visual studio code', 'vscode', 'cursor', 'sublime', 'notepad++'];
            const codeToolKeywords = ['dbeaver', 'xampp', 'postman', 'docker', 'vmware', 'heidisql', 'mysql workbench', 'mongodb compass', 'insomnia', 'tableplus', 'redis insight', 'pgadmin'];
            const browserKeywords = ['chrome', 'edge', 'firefox', 'comet'];
            const webAppKeywords = ['perplexity', 'gemini', 'notebooklm', 'chatgpt', 'claude', 'localhost', '127.0.0.1', 'figma', 'excalidraw'];
            const webBrowsingKeywords = ['youtube', 'github', 'stackoverflow', 'docs', 'documentation', 'tutorial', 'guide', 'blog', 'view-source:'];
            const commsKeywords = ['whatsapp', 'slack', 'discord', 'telegram', 'gmail', 'outlook', 'inbox', 'mail'];
            const filesKeywords = ['explorador', 'explorer'];
            const systemKeywords = ['task manager', 
                'administrador de tareas', 'settings', 
                'configuraciÃ³n', 'control panel', 'panel de control',
                 'registry editor', 'services', 'device manager', 'windows security', 
                 'seguridad de windows', 'herramienta recortes', 'snipping tool', 'reloj', 'clock',
                  'opciones de energÃ­a', 'power options'];
            if (terminal) {
                const isAnchor = ['ready', 'python', 'npm', 'node', 'ssh', 'uvicorn', 'server', 'worker'].some(kw => title.includes(kw));
                return { main: 'terminal', sub: isAnchor ? 'anchor' : 'generic', importance: isAnchor ? 'high' : 'medium' };
            }
            if (hasAny(codeEditorKeywords)) {
                return { main: 'code', sub: 'editor', importance: 'high' };
            }
            if (hasAny(codeToolKeywords)) {
                return { main: 'code', sub: 'tool', importance: 'high' };
            }
            if (hasAny(commsKeywords) && !hasAny(browserKeywords)) {
                return { main: 'comms', sub: 'chat', importance: 'medium' };
            }
            if (hasAny(filesKeywords)) {
                return { main: 'files', sub: 'folder', importance: 'medium' };
            }
            if (hasAny(systemKeywords)) {
                return { main: 'system', sub: 'utility', importance: 'medium' };
            }
            if (hasAny(commsKeywords)) {
                return { main: 'comms', sub: 'web-chat', importance: 'medium' };
            }
            if (hasAny(webAppKeywords)) {
                return { main: 'web', sub: 'app', importance: 'medium' };
            }
            if (hasAny(browserKeywords)) {
                if (hasAny(webBrowsingKeywords)) {
                    return { main: 'web', sub: 'browsing', importance: 'low' };
                }
                return { main: 'web', sub: 'browsing', importance: 'low' };
            }
            if (['task manager', 'administrador de tareas', 'settings', 'configuración', 'control panel', 'panel de control', 'registry editor', 'services', 'device manager', 'windows security', 'seguridad de windows'].some(kw => title.includes(kw))) {
                return { main: 'system', sub: 'utility', importance: 'medium' };
            }
            return { main: 'noise', sub: 'ambiguous', importance: 'low' };
        },

        // Getters ahora ultra-rápidos (solo devuelven la caché procesada)
        get desktopsWithSummary() { return this.processed.desktops; },
        get activeDesktop() { return this.processed.desktops.find(d => d.id === this.activeDesktopId); },
        get activeBuckets() { return this.activeDesktop?.buckets || { terminal: [], code: { files: [], tools: [] }, web: { apps: [], browsing: [] }, files: [], comms: [], system: [], noise: [] }; },
        get allWindowsByCategory() { return this.processed.byCategory; },

        setActiveDesktop(id) {
            this.activeDesktopId = id;
            this.viewMode = 'detail';
        },

        setViewMode(mode) {
            this.viewMode = mode;
        },
        toggleFavorite(win) {
            if (!win) return;
            const index = this.favorites.findIndex(f => f.hwnd === win.hwnd);
            if (index > -1) {
                this.favorites.splice(index, 1);
            } else {
                this.favorites.push({
                    hwnd: win.hwnd,
                    title: win.terminalName || win.title,
                    type: win.semanticType || 'unknown'
                });
            }
            localStorage.setItem('wm_favorites', JSON.stringify(this.favorites));
        },

        isFavorite(hwnd) {
            return this.favorites.some(f => f.hwnd === hwnd);
        },

        async saveSnapshot() {
            this.savingSnapshot = true;
            try {
                const response = await fetch('/api/snapshots', { method: 'POST' });
                if (!response.ok) throw new Error('Failed to save snapshot');
                await this.loadRecentSnapshots();
            } catch (e) {
                console.error('Save Snapshot Error:', e);
            } finally {
                this.savingSnapshot = false;
            }
        },

        async loadRecentSnapshots() {
            try {
                const response = await fetch('/api/snapshots?limit=8');
                if (!response.ok) throw new Error('Failed to list snapshots');
                const data = await response.json();
                this.recentSnapshots = data.items || [];
                this.latestSnapshot = this.recentSnapshots[0] || null;
            } catch (e) {
                console.error('Snapshot List Error:', e);
            }
        },
        async jumpToWindow(hwnd) {
            try {
                const response = await fetch(`/api/windows/${hwnd}/jump`, { method: 'POST' });
                if (!response.ok) throw new Error('Failed to jump to window');
            } catch (e) {
                console.error('Jump Error:', e);
            }
        },

        async jumpToDesktop(desktopNum) {
            try {
                const response = await fetch(`/api/desktops/${desktopNum}/go`, { method: 'POST' });
                if (!response.ok) throw new Error('Failed to jump to desktop');
            } catch (e) {
                console.error('Desktop Jump Error:', e);
            }
        }
    });
});
