const SUMMARY_MAP = {
    terminal: 'term',
    code: 'cod',
    web: 'web',
    files: 'arch',
    comms: 'comms'
};

export function buildSemanticSummary(counts) {
    const parts = Object.entries(SUMMARY_MAP)
        .filter(([key]) => (counts[key] || 0) > 0)
        .map(([key, label]) => `${counts[key]} ${label}`);

    return parts.length ? parts.join(' · ') : 'sin apps productivas';
}
