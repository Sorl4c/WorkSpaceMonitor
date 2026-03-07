document.addEventListener('alpine:init', () => {
    Alpine.store('kds', {
        // --- ESTADO ---
        items: [],
        toasts: [],
        online: false,
        activeView: Alpine.$persist('kanban').as('activeView'),
        activeFilter: Alpine.$persist('todo').as('activeFilter'),
        lastUpdate: Date.now(),
        
        // Historial de servidos
        showFullHistory: false,
        historyItems: [],
        loadingHistory: false,
        selectedTableFilter: '',

        // --- CONFIGURACIÓN SSE ---
        sseSource: null,
        reconnectTimeout: null,

        // --- INICIALIZACIÓN ---
        init() {
            this.connectSSE();
            
            // Timer global para forzar re-renders de tiempos si fuera necesario
            setInterval(() => {
                this.lastUpdate = Date.now();
            }, 1000);
        },

        connectSSE() {
            if (this.sseSource) {
                this.sseSource.close();
            }

            console.log('Intentando conectar a SSE...');
            this.sseSource = new EventSource('../backend/kds_api.php');

            this.sseSource.onopen = () => {
                console.log('Conexión SSE establecida');
                this.online = true;
                if (this.reconnectTimeout) {
                    clearTimeout(this.reconnectTimeout);
                    this.reconnectTimeout = null;
                }
            };

            this.sseSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    
                    // Comprobar si hay IDs nuevos para hacer sonar la alerta
                    if (this.items.length > 0) {
                        const currentIds = new Set(this.items.map(i => i.id));
                        const hasNewOrders = data.some(item => !currentIds.has(item.id) && item.estado === 'pendiente');
                        
                        if (hasNewOrders) {
                            const audio = document.getElementById('new-order-sound');
                            if (audio) {
                                audio.play().catch(e => console.log('Autoplay prevent prevented sound', e));
                            }
                        }
                    }

                    // Actualización reactiva de items
                    this.items = data;
                } catch (e) {
                    console.error('Error parseando datos SSE:', e);
                }
            };

            this.sseSource.onerror = (err) => {
                console.error('Error en conexión SSE:', err);
                this.online = false;
                this.sseSource.close();
                
                // Reconexión automática tras 3 segundos
                if (!this.reconnectTimeout) {
                    this.reconnectTimeout = setTimeout(() => {
                        this.connectSSE();
                    }, 3000);
                }
            };
        },

        // --- ACCIONES ---
        async toggleHistory() {
            this.showFullHistory = !this.showFullHistory;
            if (this.showFullHistory && this.historyItems.length === 0) {
                this.loadingHistory = true;
                try {
                    const response = await fetch('../backend/get_historial.php');
                    if (response.ok) {
                        this.historyItems = await response.json();
                    } else {
                        console.error('Error cargando historial completo');
                    }
                } catch (e) {
                    console.error('Fallo en fetch historial:', e);
                } finally {
                    this.loadingHistory = false;
                }
            }
        },

        async updateStatus(ids, newState) {
            // Aseguramos que ids sea un array si viene un solo ID
            if (!Array.isArray(ids)) ids = [ids];
            
            // Lógica Optimista
            const originalItems = JSON.parse(JSON.stringify(this.items));
            const timestamp = Date.now();
            
            this.items = this.items.map(item => {
                if (ids.includes(item.id)) {
                    return { ...item, estado: newState, estado_timestamp: timestamp };
                }
                return item;
            });

            try {
                const response = await fetch('../backend/update_comanda.php', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ids, estado: newState })
                });
                
                if (!response.ok) throw new Error('Error en el servidor');
            } catch (error) {
                console.error('Fallo al actualizar estado:', error);
                this.items = originalItems; // Rollback
            }
        },

        async advanceState(ids, newState) {
            if (!ids) return;
            if (!Array.isArray(ids)) ids = [ids];

            // Lógica Optimista: Actualizar localmente antes del fetch
            const originalItems = JSON.parse(JSON.stringify(this.items));
            const timestamp = Date.now();
            
            this.items = this.items.map(item => {
                if (ids.includes(item.id)) {
                    return { ...item, estado: newState, estado_timestamp: timestamp };
                }
                return item;
            });

            // Si pasa a 'listo', crear un Toast
            if (newState === 'listo') {
                const item = originalItems.find(i => ids.includes(i.id));
                if (item) {
                    this.addToast(item, ids, timestamp);
                }
            }

            try {
                const response = await fetch('../backend/update_comanda.php', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ids, estado: newState })
                });
                
                if (!response.ok) throw new Error('Error en el servidor');
            } catch (error) {
                console.error('Fallo al actualizar estado:', error);
                this.items = originalItems; // Rollback
            }
        },

        async goBackState(ids) {
            if (!ids) return;
            if (!Array.isArray(ids)) ids = [ids];

            const item = this.items.find(i => ids.includes(i.id));
            if (!item) return;

            let prevState = 'pendiente';
            if (item.estado === 'emplatado') {
                prevState = item.station;
            } else if (item.estado === item.station) {
                prevState = 'pendiente';
            } else if (item.estado === 'listo') {
                prevState = 'emplatado';
            }

            if (prevState !== item.estado) {
                await this.advanceState(ids, prevState);
                if (navigator.vibrate) navigator.vibrate(50);
            }
        },

        // --- HELPERS COMANDAS ---
        mapItemStateToOrderPhase(item) {
            if (item.estado === 'pendiente') return 'pendiente';
            if (['cocina', 'horno', 'barra'].includes(item.estado)) return 'preparacion';
            if (item.estado === 'emplatado') return 'emplatado';
            return 'listo';
        },

        resolveOrderPhase(items) {
            if (!items || items.length === 0) return 'listo';
            const phases = items.map(i => this.mapItemStateToOrderPhase(i));
            if (phases.includes('pendiente')) return 'pendiente';
            if (phases.includes('preparacion')) return 'preparacion';
            if (phases.includes('emplatado')) return 'emplatado';
            return 'listo';
        },

        buildOrderSummary(items) {
            const summary = [];
            items.forEach(item => {
                const notesKey = Array.isArray(item.notes) ? item.notes.join('|') : '';
                const key = `${item.producto}-${notesKey}`;
                const existing = summary.find(s => s.key === key);
                
                if (existing) {
                    existing.qty += 1;
                    if (!existing.estados.includes(item.estado)) {
                        existing.estados.push(item.estado);
                    }
                } else {
                    summary.push({
                        key,
                        producto: item.producto,
                        qty: 1,
                        notes: Array.isArray(item.notes) ? item.notes : [],
                        estados: [item.estado]
                    });
                }
            });
            return summary;
        },

        async advanceFullOrder(orderId) {
            if (!orderId) {
                console.warn('[KDS] advanceFullOrder llamado sin orderId válido');
                return;
            }

            // Find all items belonging to this order
            const orderItems = this.items.filter(i => i.orderId === orderId);
            
            const activeItems = orderItems.filter(i => i.estado !== 'listo');
            if (activeItems.length === 0) return;

            const phase = this.resolveOrderPhase(activeItems);
            
            let idsToUpdate = [];
            let newState = '';

            if (phase === 'pendiente') {
                const pendingItems = activeItems.filter(i => i.estado === 'pendiente');
                const byStation = {};
                pendingItems.forEach(i => {
                    if (!byStation[i.station]) byStation[i.station] = [];
                    byStation[i.station].push(i.id);
                });
                
                for (const station in byStation) {
                    await this.advanceState(byStation[station], station);
                }
                return;
            } else if (phase === 'preparacion') {
                idsToUpdate = activeItems.filter(i => ['cocina', 'horno', 'barra'].includes(i.estado)).map(i => i.id);
                newState = 'emplatado';
            } else if (phase === 'emplatado') {
                idsToUpdate = activeItems.filter(i => i.estado === 'emplatado').map(i => i.id);
                newState = 'listo';
            }

            if (idsToUpdate.length > 0 && newState) {
                await this.advanceState(idsToUpdate, newState);
            }
        },

        // --- GETTERS (Derivados) ---
        get fullOrderColumns() {
            const map = new Map();

            this.items.forEach(item => {
                if (!item.orderId) {
                    // console.warn('[KDS] Item sin orderId excluido de vista comanda', item);
                    return;
                }

                if (!map.has(item.orderId)) {
                    map.set(item.orderId, {
                        orderId: item.orderId,
                        mesa: item.mesa || '?',
                        items: []
                    });
                }
                map.get(item.orderId).items.push(item);
            });

            const grouped = Array.from(map.values()).filter(group => {
                return group.items.some(i => i.estado !== 'listo');
            }).map(group => {
                const activeItems = group.items.filter(i => i.estado !== 'listo');
                const phase = this.resolveOrderPhase(activeItems);
                
                const oldestActiveTimestamp = activeItems.reduce((min, i) => Math.min(min, i.estado_timestamp), Infinity);
                const estimatedMaxTime = activeItems.reduce((max, i) => Math.max(max, i.estimated_time || 0), 0);
                
                const activeItemsCount = activeItems.length;

                return {
                    orderId: group.orderId,
                    mesa: group.mesa,
                    ids: activeItems.map(i => i.id),
                    items: activeItems,
                    phase: phase,
                    totalItems: group.items.length,
                    completedItems: group.items.filter(i => i.estado === 'listo').length,
                    activeItemsCount: activeItemsCount,
                    pendingItems: activeItems.filter(i => i.estado === 'pendiente').length,
                    preparingItems: activeItems.filter(i => ['cocina', 'horno', 'barra'].includes(i.estado)).length,
                    platedItems: activeItems.filter(i => i.estado === 'emplatado').length,
                    oldestActiveTimestamp: oldestActiveTimestamp,
                    estimatedMaxTime: estimatedMaxTime,
                    summaryLines: this.buildOrderSummary(activeItems),
                    notes: Array.from(new Set(activeItems.flatMap(i => Array.isArray(i.notes) ? i.notes : []))),
                    canAdvance: phase !== 'listo' && activeItemsCount > 0
                };
            });

            // Sort logically: oldest first
            grouped.sort((a, b) => a.oldestActiveTimestamp - b.oldestActiveTimestamp);

            return {
                pendiente: grouped.filter(g => g.phase === 'pendiente'),
                preparacion: grouped.filter(g => g.phase === 'preparacion'),
                emplatado: grouped.filter(g => g.phase === 'emplatado')
            };
        },

        get groupedColumns() {
            let filtered = this.items.filter(i => i.estado !== 'listo');
            if (this.activeFilter !== 'todo') {
                filtered = filtered.filter(i => i.station === this.activeFilter);
            }

            const map = new Map();
            const grouped = [];
            
            filtered.forEach(item => {
                const notesArray = Array.isArray(item.notes) ? item.notes : [];
                // La clave incluye orderId para no mezclar mesas, pero agrupa productos idénticos
                const key = `${item.orderId}-${item.producto}-${item.estado}-${notesArray.join(',')}`;
                
                if (map.has(key)) {
                    const existing = map.get(key);
                    existing.ids.push(item.id);
                    existing.qty += 1;
                    if (item.estado_timestamp < existing.estado_timestamp) {
                        existing.estado_timestamp = item.estado_timestamp;
                    }
                } else {
                    const newItemGroup = { 
                        ...item, 
                        ids: [item.id], 
                        qty: 1,
                        notes: notesArray // Asegurar que es array
                    };
                    map.set(key, newItemGroup);
                    grouped.push(newItemGroup);
                }
            });

            return {
                pendiente: grouped.filter(i => i.estado === 'pendiente'),
                cocina: grouped.filter(i => i.estado === 'cocina'),
                horno: grouped.filter(i => i.estado === 'horno'),
                barra: grouped.filter(i => i.estado === 'barra'),
                emplatado: grouped.filter(i => i.estado === 'emplatado'),
            };
        },

        get servedItems() {
            // Decidir qué array base usar
            let baseItems = this.showFullHistory ? this.historyItems : this.items.filter(i => i.estado === 'listo');
            
            // Ordenar por tiempo (más reciente primero) sin mutar el array original
            let sorted = [...baseItems].sort((a, b) => b.estado_timestamp - a.estado_timestamp);
            
            // Filtrar por mesa si hay alguna seleccionada
            if (this.selectedTableFilter && this.selectedTableFilter !== '') {
                sorted = sorted.filter(i => i.mesa === this.selectedTableFilter);
            }
            
            // Limitar a los 50 si no es el historial completo, o devolver todos si es el completo
            return this.showFullHistory ? sorted : sorted.slice(0, 50);
        },

        get availableTables() {
            // Extraer las mesas únicas del dataset actual (sin filtrar por mesa)
            let baseItems = this.showFullHistory ? this.historyItems : this.items.filter(i => i.estado === 'listo');
            const tables = new Set(baseItems.map(i => i.mesa).filter(Boolean));
            return Array.from(tables).sort();
        },

        // --- GESTIÓN DE TOASTS ---
        addToast(item, ids, prevTimestamp) {
            const toastId = Date.now() + Math.random();
            this.toasts.push({
                id: toastId,
                itemId: item.id,
                ids: ids, // Guardamos todos los IDs si era un grupo
                mesa: item.mesa,
                producto: item.producto,
                prevState: item.estado,
                prevTimestamp: prevTimestamp
            });

            // Auto-eliminar tras 5 segundos
            setTimeout(() => {
                this.removeToast(toastId);
            }, 5000);
        },

        removeToast(toastId) {
            this.toasts = this.toasts.filter(t => t.id !== toastId);
        },

        async undoToast(toastId) {
            const toast = this.toasts.find(t => t.id === toastId);
            if (toast) {
                await this.advanceState(toast.ids, toast.prevState);
                this.removeToast(toastId);
            }
        }
    });
});
