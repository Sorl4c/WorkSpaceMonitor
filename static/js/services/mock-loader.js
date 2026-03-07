const MOCK_PATH = '/mock/current_snapshot.json';

export async function loadMockSnapshot() {
    const response = await fetch(MOCK_PATH, { cache: 'no-store' });
    if (!response.ok) {
        throw new Error(`No se pudo cargar el snapshot mock (${response.status})`);
    }
    return response.json();
}
