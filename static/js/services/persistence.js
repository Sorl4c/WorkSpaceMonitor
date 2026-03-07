const STORAGE_KEY = 'wm.preferences.v1';

const DEFAULTS = {
    mode: 'mock',
    activeDesktopId: null,
    showEmptyDesktops: false,
    showNoise: false,
    debug: false
};

export function loadPreferences() {
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (!stored) return { ...DEFAULTS };
        const parsed = JSON.parse(stored);
        return { ...DEFAULTS, ...parsed };
    } catch (_error) {
        return { ...DEFAULTS };
    }
}

export function savePreferences(preferences) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
}

export function getPreferenceDefaults() {
    return { ...DEFAULTS };
}
