import { loadMockSnapshot } from '../services/mock-loader.js';
import { createSSEClient } from '../services/sse.js';
import { getPreferenceDefaults, loadPreferences, savePreferences } from '../services/persistence.js';
import { normalizeState } from '../utils/normalize.js';

export function createWMStore() {
    const defaults = getPreferenceDefaults();
    const persisted = loadPreferences();

    return {
        mode: persisted.mode || defaults.mode,
        online: false,
        loading: false,
        error: null,
        sseError: null,
        lastUpdate: null,
        activeDesktopId: persisted.activeDesktopId || defaults.activeDesktopId,
        showEmptyDesktops: persisted.showEmptyDesktops ?? defaults.showEmptyDesktops,
        showNoise: persisted.showNoise ?? defaults.showNoise,
        debug: persisted.debug ?? defaults.debug,
        raw: {
            desktops: [],
            windows: [],
            terminals: []
        },
        normalized: {
            desktops: [],
            desktopMap: {},
            windowsByDesktop: {},
            terminalsByPid: {}
        },
        _sseClient: null,

        async init() {
            this.loading = true;
            this.error = null;

            if (this.mode === 'live') {
                await this.connectSSE();
            } else {
                await this.loadMockState();
            }

            this.loading = false;
        },

        async setMode(mode) {
            if (!['mock', 'live'].includes(mode) || mode === this.mode) return;
            this.mode = mode;
            this.persistPreferences();
            this.error = null;

            if (mode === 'mock') {
                this.disconnectSSE();
                await this.loadMockState();
            } else {
                await this.connectSSE();
            }
        },

        async loadMockState() {
            this.loading = true;
            this.online = false;
            try {
                const payload = await loadMockSnapshot();
                this.applyIncomingState(payload);
                this.error = null;
            } catch (error) {
                this.error = error.message || 'No se pudo cargar mock';
            } finally {
                this.loading = false;
            }
        },

        async connectSSE() {
            this.disconnectSSE();
            this.loading = true;

            this._sseClient = createSSEClient({
                onOpen: () => {
                    this.online = true;
                    this.sseError = null;
                    this.loading = false;
                },
                onMessage: (event) => {
                    try {
                        const payload = JSON.parse(event.data);
                        this.applyIncomingState(payload);
                        this.error = null;
                        this.online = true;
                    } catch (_error) {
                        this.sseError = 'Payload SSE inválido';
                    }
                },
                onError: () => {
                    this.online = false;
                    this.sseError = 'SSE con errores o reconectando';
                }
            });

            this._sseClient.connect('/events');
        },

        disconnectSSE() {
            if (this._sseClient) {
                this._sseClient.disconnect();
            }
            this._sseClient = null;
            this.online = false;
        },

        applyIncomingState(payload) {
            const next = normalizeState(payload);
            this.raw = next.raw;
            this.normalized = next.normalized;
            this.lastUpdate = new Date().toISOString();

            const activeExists = this.normalized.desktopMap[this.activeDesktopId];
            if (!activeExists) {
                this.activeDesktopId = this.pickDefaultDesktopId();
                this.persistPreferences();
            }
        },

        pickDefaultDesktopId() {
            const productive = this.productiveDesktops;
            if (productive.length) return productive[0].desktopId;
            return this.normalized.desktops[0]?.desktopId || null;
        },

        setActiveDesktop(desktopId) {
            this.activeDesktopId = desktopId;
            this.persistPreferences();
        },

        toggleEmptyDesktops() {
            this.showEmptyDesktops = !this.showEmptyDesktops;
            this.persistPreferences();
        },

        toggleNoise() {
            this.showNoise = !this.showNoise;
            this.persistPreferences();
        },

        toggleDebug() {
            this.debug = !this.debug;
            this.persistPreferences();
        },

        persistPreferences() {
            savePreferences({
                mode: this.mode,
                activeDesktopId: this.activeDesktopId,
                showEmptyDesktops: this.showEmptyDesktops,
                showNoise: this.showNoise,
                debug: this.debug
            });
        },

        get desktopsWithSummary() {
            const all = this.normalized.desktops;
            if (this.showEmptyDesktops) return all;
            return all.filter((desktop) => desktop.rawWindowCount > 0);
        },

        get emptyDesktops() {
            return this.normalized.desktops.filter((desktop) => desktop.rawWindowCount === 0);
        },

        get productiveDesktops() {
            return this.normalized.desktops.filter((desktop) => desktop.counts.terminal + desktop.counts.code + desktop.counts.web + desktop.counts.files + desktop.counts.comms > 0);
        },

        get activeDesktop() {
            return this.normalized.desktopMap[this.activeDesktopId] || null;
        },

        get activeDesktopSummary() {
            return this.activeDesktop?.semanticSummary || 'sin datos';
        },

        get activeDesktopSemanticBuckets() {
            if (!this.activeDesktop) return null;
            return this.activeDesktop.buckets;
        },

        get desktopCount() {
            return this.normalized.desktops.length;
        },

        get windowCount() {
            return this.raw.windows.length;
        },

        get anchorTerminals() {
            return this.raw.windows
                .map((win) => this.normalized.windowsByDesktop[win.desktop_id] || [])
                .flat()
                .filter((win) => win.semanticType === 'terminal' && win.isAnchor);
        }
    };
}
