<div x-data="comandaCard(order)"
     x-show="show"
     x-transition:enter="transition ease-out duration-300"
     x-transition:enter-start="opacity-0 translate-y-4 scale-95"
     x-transition:enter-end="opacity-100 translate-y-0 scale-100"
     x-transition:leave="transition ease-in duration-200"
     x-transition:leave-start="opacity-100 scale-100"
     x-transition:leave-end="opacity-0 scale-95"
     class="relative p-3 mb-4 rounded-xl border flex flex-col gap-3 transition-transform duration-200 overflow-hidden select-none hover:-translate-y-0.5 shadow-md border-slate-600"
     :class="statusClasses">

    <div class="flex justify-between items-start">
        <div class="flex flex-col gap-1">
            <span class="font-bold text-lg bg-orange-600/90 px-2.5 py-1 rounded text-white shadow-sm w-fit" x-text="order.mesa"></span>
            <span class="text-xs text-slate-400 font-mono" x-text="'#' + order.orderId"></span>
        </div>
        <div class="text-lg font-mono flex items-center gap-1 px-2 py-0.5 rounded bg-slate-900/40" :class="timeTextClass">
            <i data-lucide="clock" class="w-4 h-4"></i>
            <span x-text="timeString"></span>
        </div>
    </div>
    
    <!-- Progreso -->
    <div class="w-full bg-slate-700/80 rounded-full h-2 mt-1">
        <div class="bg-orange-500 h-2 rounded-full transition-all duration-500" :style="`width: ${(order.completedItems / (order.totalItems || 1)) * 100}%`"></div>
    </div>
    <div class="text-xs text-slate-400 font-bold flex justify-between">
        <span x-text="`${order.completedItems} de ${order.totalItems} servidos`"></span>
        <span x-text="`${order.activeItemsCount} activos`" class="text-orange-400/80"></span>
    </div>

    <!-- Resumen de Platos -->
    <div class="bg-slate-900/40 rounded-lg p-2 flex flex-col gap-1.5 border border-slate-700/50">
        <div class="text-[10px] text-slate-500 uppercase font-bold tracking-wider mb-0.5">Platos Activos</div>
        <template x-for="line in order.summaryLines" :key="line.key">
            <div class="flex flex-col">
                <div class="flex items-start gap-2">
                    <span class="font-black text-sm text-orange-400" x-text="line.qty + 'x'"></span>
                    <span class="text-sm font-bold text-slate-200 leading-tight" x-text="line.producto"></span>
                </div>
                <template x-if="line.notes && line.notes.length > 0">
                    <div class="pl-6 mt-1 flex flex-wrap gap-1">
                        <template x-for="note in line.notes">
                            <span class="text-[10px] font-bold text-amber-300 bg-amber-950/60 px-1.5 py-0.5 rounded flex items-center gap-1 border border-amber-500/30">
                                <i data-lucide="alert-circle" class="w-3 h-3"></i>
                                <span x-text="note"></span>
                            </span>
                        </template>
                    </div>
                </template>
            </div>
        </template>
    </div>

    <!-- CTA de Avance -->
    <div class="mt-1 pt-2 border-t border-slate-600/50 flex justify-between items-center text-sm font-bold uppercase tracking-wider">
        <span class="text-slate-400 opacity-80" x-text="'Fase: ' + order.phase"></span>
        <button @click="advanceOrder" 
             class="flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-colors focus:outline-none focus:ring-2 focus:ring-orange-500/50"
             :class="order.canAdvance ? 'bg-orange-500/20 text-orange-400 border-orange-500/40 hover:bg-orange-500/30 cursor-pointer' : 'bg-slate-700/50 text-slate-500 border-slate-600 cursor-not-allowed opacity-50'"
             :disabled="!order.canAdvance">
            <span x-text="advanceText"></span>
            <i data-lucide="arrow-right" class="w-4 h-4"></i>
        </button>
    </div>
</div>