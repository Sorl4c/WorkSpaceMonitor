const RULES = {
    terminalHints: ['ready', 'powershell', 'cmd', 'bash', 'wsl', 'python', 'uvicorn', 'server', 'worker', 'tunnel', 'root@', 'launch', 'npm', 'node'],
    codeEditors: ['visual studio code', 'vs code', 'cursor', 'notepad++', 'sublime', 'vim', 'neovim'],
    codeTools: ['dbeaver', 'xampp', 'docker', 'insomnia', 'postman', 'control panel'],
    filesApps: ['explorador de archivos', 'explorer', 'finder', 'nautilus'],
    commsApps: ['whatsapp', 'telegram', 'discord', 'slack'],
    webContainers: ['edge', 'chrome', 'firefox', 'comet', 'brave', 'opera', 'safari'],
    webApps: ['perplexity', 'gmail', 'gemini', 'notebooklm', 'chatgpt', 'swagger', 'localhost', 'view-source:localhost', 'openclaw', 'github', 'gitlab'],
    systemNoise: ['configuración', 'settings', 'task manager', 'administrador de tareas', 'paint', 'media player', 'microsoft store', 'vmware']
};

function includesAny(text, words) {
    return words.some((word) => text.includes(word));
}

export function classifyWindow(rawWindow, terminalMatch) {
    const title = (rawWindow.title || '').trim();
    const lowerTitle = title.toLowerCase();
    const matchedRules = [];

    let semanticType = 'system';
    let semanticSubType = 'utility';
    let confidence = 0.35;

    if (terminalMatch) {
        semanticType = 'terminal';
        semanticSubType = includesAny(lowerTitle, RULES.terminalHints) ? 'anchor' : 'generic';
        matchedRules.push('pid:terminal-match');
        confidence = 0.95;
    } else if (includesAny(lowerTitle, RULES.terminalHints)) {
        semanticType = 'terminal';
        semanticSubType = 'generic';
        matchedRules.push('title:terminal-hint');
        confidence = 0.78;
    } else if (includesAny(lowerTitle, RULES.codeEditors)) {
        semanticType = 'code';
        semanticSubType = includesAny(lowerTitle, RULES.codeTools) ? 'tool' : 'editor';
        matchedRules.push('title:code-editor');
        confidence = 0.88;
    } else if (includesAny(lowerTitle, RULES.codeTools)) {
        semanticType = 'code';
        semanticSubType = 'tool';
        matchedRules.push('title:code-tool');
        confidence = 0.74;
    } else if (includesAny(lowerTitle, RULES.filesApps)) {
        semanticType = 'files';
        semanticSubType = 'explorer';
        matchedRules.push('title:files-explorer');
        confidence = 0.85;
    } else if (includesAny(lowerTitle, RULES.commsApps)) {
        semanticType = 'comms';
        semanticSubType = 'chat';
        matchedRules.push('title:comms-app');
        confidence = 0.82;
    } else if (includesAny(lowerTitle, RULES.webContainers) || includesAny(lowerTitle, RULES.webApps)) {
        semanticType = 'web';
        semanticSubType = includesAny(lowerTitle, RULES.webApps) ? 'app' : 'navigation';
        matchedRules.push(semanticSubType === 'app' ? 'title:web-app' : 'title:web-browser');
        confidence = semanticSubType === 'app' ? 0.8 : 0.68;
    } else if (title.length === 0) {
        semanticType = 'system';
        semanticSubType = 'noise';
        matchedRules.push('title:empty');
        confidence = 0.3;
    } else if (includesAny(lowerTitle, RULES.systemNoise)) {
        semanticType = 'system';
        semanticSubType = 'noise';
        matchedRules.push('title:system-noise');
        confidence = 0.7;
    }

    const isAnchor = semanticType === 'terminal' && (semanticSubType === 'anchor' || includesAny(lowerTitle, RULES.terminalHints));
    const isNoise = semanticType === 'system' || confidence < 0.55;

    let importance = 'low';
    if (isAnchor || semanticType === 'code') {
        importance = 'high';
    } else if (['files', 'web', 'comms'].includes(semanticType) && !isNoise) {
        importance = 'medium';
    }

    return {
        semanticType,
        semanticSubType,
        isAnchor,
        isNoise,
        confidence,
        matchedRules,
        importance,
        source: terminalMatch ? 'pid+title' : 'title'
    };
}
