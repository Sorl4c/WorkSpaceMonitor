import { createWMStore } from './store/wm-store.js';

document.addEventListener('alpine:init', () => {
    Alpine.store('wm', createWMStore());
});
