import { classifyWindow } from './classify.js';
import { buildSemanticSummary } from './summary.js';

function coerceList(block) {
    if (Array.isArray(block)) return block;
    if (block && Array.isArray(block.value)) return block.value;
    return [];
}

function normalizeRawPayload(payload = {}) {
    return {
        desktops: coerceList(payload.desktops),
        windows: coerceList(payload.windows),
        terminals: coerceList(payload.terminals)
    };
}

function defaultBuckets() {
    return {
        terminal: [],
        code: [],
        files: [],
        webApp: [],
        webNavigation: [],
        comms: [],
        system: []
    };
}

export function normalizeState(payload = {}) {
    const raw = normalizeRawPayload(payload);
    const terminalsByPid = Object.fromEntries(raw.terminals.map((terminal) => [terminal.pid, terminal]));

    const desktops = raw.desktops
        .map((desktop) => ({
            id: `desktop-${desktop.number}`,
            desktopId: desktop.id,
            number: desktop.number,
            name: desktop.name || `Desktop ${desktop.number}`,
            rawWindowCount: 0,
            semanticSummary: 'sin apps productivas',
            counts: { terminal: 0, code: 0, web: 0, files: 0, comms: 0, system: 0 },
            buckets: defaultBuckets()
        }))
        .sort((a, b) => a.number - b.number);

    const desktopMap = Object.fromEntries(desktops.map((desktop) => [desktop.desktopId, desktop]));

    raw.windows.forEach((window) => {
        if (!desktopMap[window.desktop_id]) {
            const fallback = {
                id: `desktop-unknown-${window.desktop_id}`,
                desktopId: window.desktop_id,
                number: 999,
                name: 'Desktop desconocido',
                rawWindowCount: 0,
                semanticSummary: 'sin apps productivas',
                counts: { terminal: 0, code: 0, web: 0, files: 0, comms: 0, system: 0 },
                buckets: defaultBuckets()
            };
            desktopMap[window.desktop_id] = fallback;
            desktops.push(fallback);
        }

        const terminalMatch = terminalsByPid[window.pid] || null;
        const classification = classifyWindow(window, terminalMatch);
        const displayTitle = window.title || '(sin título)';

        const normalizedWindow = {
            hwnd: window.hwnd,
            pid: window.pid,
            desktop_id: window.desktop_id,
            title: window.title,
            processName: null,
            terminalName: terminalMatch ? (terminalMatch.custom_name || terminalMatch.name) : null,
            displayTitle,
            ...classification
        };

        const desktop = desktopMap[window.desktop_id];
        desktop.rawWindowCount += 1;

        if (normalizedWindow.semanticType === 'web') {
            desktop.buckets[normalizedWindow.semanticSubType === 'app' ? 'webApp' : 'webNavigation'].push(normalizedWindow);
        } else {
            const bucketKey = desktop.buckets[normalizedWindow.semanticType] ? normalizedWindow.semanticType : 'system';
            desktop.buckets[bucketKey].push(normalizedWindow);
        }

        if (['terminal', 'code', 'files', 'comms'].includes(normalizedWindow.semanticType)) {
            desktop.counts[normalizedWindow.semanticType] += 1;
        } else if (normalizedWindow.semanticType === 'web') {
            desktop.counts.web += 1;
        } else {
            desktop.counts.system += 1;
        }
    });

    desktops.forEach((desktop) => {
        desktop.semanticSummary = buildSemanticSummary(desktop.counts);
    });

    const windowsByDesktop = Object.fromEntries(
        desktops.map((desktop) => [
            desktop.desktopId,
            Object.values(desktop.buckets).flat()
        ])
    );

    return {
        raw,
        normalized: {
            desktops,
            desktopMap,
            windowsByDesktop,
            terminalsByPid
        }
    };
}
