document.addEventListener('alpine:init', () => {
    Alpine.data('comandaCard', (order) => {
        return {
            show: false,
            init() {
                setTimeout(() => {
                    this.show = true;
                }, 10);
            },
            
            get elapsedMs() {
                if (order.oldestActiveTimestamp === Infinity || !order.oldestActiveTimestamp) return 0;
                return this.$store.kds.lastUpdate - order.oldestActiveTimestamp;
            },

            get timeString() {
                if (this.elapsedMs === 0) return "00:00";
                const minutes = Math.floor(this.elapsedMs / 60000);
                const seconds = Math.floor((this.elapsedMs % 60000) / 1000);
                return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            },

            get minutesElapsed() {
                return Math.floor(this.elapsedMs / 60000);
            },

            get statusClasses() {
                const estTime = order.estimatedMaxTime || 15; // default 15 min if none
                if (this.minutesElapsed >= estTime) {
                    return "bg-red-900/30 border-red-500/40 shadow-[0_0_15px_rgba(220,38,38,0.15)]";
                } else if (this.minutesElapsed >= estTime * 0.75) {
                    return "bg-amber-900/20 border-amber-500/40";
                }
                return "bg-slate-800 border-slate-700";
            },

            get timeTextClass() {
                const estTime = order.estimatedMaxTime || 15;
                if (this.minutesElapsed >= estTime) {
                    return "text-red-400 font-bold animate-pulse";
                } else if (this.minutesElapsed >= estTime * 0.75) {
                    return "text-amber-400 font-bold";
                }
                return "text-slate-300";
            },

            get advanceText() {
                if (order.phase === 'pendiente') return `Avanzar (${order.pendingItems})`;
                if (order.phase === 'preparacion') return `Avanzar (${order.preparingItems})`;
                if (order.phase === 'emplatado') return `Servir (${order.platedItems})`;
                return 'Hecho';
            },

            advanceOrder() {
                if (!order.canAdvance) return;
                this.$store.kds.advanceFullOrder(order.orderId);
                if (navigator.vibrate) navigator.vibrate(50);
            }
        };
    });
});
