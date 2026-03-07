export function createSSEClient({ onOpen, onMessage, onError } = {}) {
    let source = null;

    return {
        connect(url = '/events') {
            if (source) {
                source.close();
            }

            source = new EventSource(url);
            source.onopen = () => onOpen && onOpen();
            source.onmessage = (event) => onMessage && onMessage(event);
            source.onerror = (error) => onError && onError(error);
            return source;
        },
        disconnect() {
            if (source) {
                source.close();
                source = null;
            }
        }
    };
}
