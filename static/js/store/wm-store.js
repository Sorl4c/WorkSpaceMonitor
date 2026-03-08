document.addEventListener('alpine:init', () => {
     Alpine.store('wm', {
        mode: 'live',
        viewMode: 'detail',
        online: false,
        lastUpdate: Date.now(),
        activeDesktopId: null,
        
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
            setInterval(() => { this.lastUpdate = Date.now(); }, 5000);
        },

        async refresh() {
            this.online = 'loading';
            try {
                const response = await fetch('/api/snapshot');
                if (response.ok) {
                    const data = await response.json();
                    this.applyIncomingState(data);
                    this.online = true;
                }
            } catch (e) {
                console.error('WM Store: Refresh Error', e);
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
                const dominantCategory = Object.entries(catCounts).sort((a,b) => b[1]-a[1])[0]?.[0] || 'system';

                return {
                    ...d,
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
                        system: wins.filter(w => w.semanticType === 'system')
                    }
                };
            }).sort((a, b) => a.number - b.number);

            // 3. Procesar Categorías (Matrix View)
            const categories = [
                { id: 'terminal', label: 'Terminals', icon: 'terminal', color: 'var(--c-terminal)' },
                { id: 'code', label: 'Development', icon: 'code', color: 'var(--c-code)' },
                { id: 'web', label: 'Web & Research', icon: 'globe', color: 'var(--c-web)' },
                { id: 'files', label: 'Files', icon: 'folder', color: 'var(--c-files)' },
                { id: 'comms', label: 'Communication', icon: 'message-square', color: 'var(--c-comms)' }
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
            if (terminal) {
                const isAnchor = ['ready', 'python', 'npm', 'node', 'ssh', 'uvicorn', 'server', 'worker'].some(kw => title.includes(kw));
                return { main: 'terminal', sub: isAnchor ? 'anchor' : 'generic', importance: isAnchor ? 'high' : 'medium' };
            }
            if (['visual studio code', 'vscode', 'cursor', 'sublime', 'notepad++'].some(kw => title.includes(kw))) {
                const isTool = ['dbeaver', 'xampp', 'postman', 'studio', 'docker'].some(kw => title.includes(kw));
                return { main: 'code', sub: isTool ? 'tool' : 'editor', importance: 'high' };
            }
            if (['chrome', 'edge', 'firefox'].some(kw => title.includes(kw))) {
                const isWebApp = ['perplexity', 'gmail', 'gemini', 'notebooklm', 'chatgpt', 'comet', 'localhost'].some(kw => title.includes(kw));
                return { main: 'web', sub: isWebApp ? 'app' : 'browsing', importance: isWebApp ? 'medium' : 'low' };
            }
            if (['whatsapp', 'slack', 'discord', 'telegram'].some(kw => title.includes(kw))) {
                return { main: 'comms', sub: 'chat', importance: 'medium' };
            }
            if (['explorador', 'explorer'].some(kw => title.includes(kw))) {
                return { main: 'files', sub: 'folder', importance: 'medium' };
            }
            return { main: 'system', sub: 'noise', importance: 'low' };
        },

        // Getters ahora ultra-rápidos (solo devuelven la caché procesada)
        get desktopsWithSummary() { return this.processed.desktops; },
        get activeDesktop() { return this.processed.desktops.find(d => d.id === this.activeDesktopId); },
        get activeBuckets() { return this.activeDesktop?.buckets || { terminal: [], code: { files: [], tools: [] }, web: { apps: [], browsing: [] }, files: [], comms: [], system: [] }; },
        get allWindowsByCategory() { return this.processed.byCategory; },

        setActiveDesktop(id) {
            this.activeDesktopId = id;
            this.viewMode = 'detail';
        },

        setViewMode(mode) {
            this.viewMode = mode;
        }
    });
});
