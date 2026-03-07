<div x-data="kanbanCard(item)"
     x-show="show"
     x-transition:enter="transition ease-out duration-300"
     x-transition:enter-start="opacity-0 translate-y-4 scale-95"
     x-transition:enter-end="opacity-100 translate-y-0 scale-100"
     x-transition:leave="transition ease-in duration-200"
     x-transition:leave-start="opacity-100 scale-100"
     x-transition:leave-end="opacity-0 scale-95"
     class="relative p-3 mb-3 rounded-xl border flex flex-col gap-2 transition-transform duration-200 cursor-pointer overflow-hidden touch-none select-none hover:-translate-y-0.5 shadow-md"
     :class="statusClasses"
     :style="{ borderLeftWidth: '6px', borderLeftColor: stationColor, transform: isHolding ? 'scale(0.96)' : 'scale(1)' }"
     @pointerdown="handlePointerDown"
     @pointerup="handlePointerUpOrLeave"
     @pointerleave="handlePointerUpOrLeave"
     @contextmenu.prevent="handleRightClick">

    <!-- Barra de progreso del Long Press -->
    <div class="absolute bottom-0 left-0 h-1 bg-red-500 ease-linear"
         :style="{ 
            width: isHolding ? '100%' : '0%', 
            transition: isHolding ? 'width 600ms linear' : 'width 100ms ease-out',
            opacity: isHolding ? 1 : 0
         }"></div>

    <div class="flex justify-between items-start">
        <div class="flex items-center gap-2">
            <span class="font-bold text-sm bg-slate-900/80 px-2 py-1 rounded text-white shadow-sm" x-text="item.mesa"></span>
            <template x-if="item.qty > 1">
                <div class="flex items-center gap-1 group/qty">
                    <span class="font-black text-sm bg-orange-500 px-2 py-1 rounded text-white shadow-md animate-pulse" x-text="'x' + item.qty"></span>
                    <span class="hidden group-hover/qty:inline-block text-[10px] text-orange-300 font-bold bg-orange-950/40 px-1.5 py-0.5 rounded border border-orange-500/20">Split: Click Der.</span>
                </div>
            </template>
        </div>
        <div class="text-lg font-mono flex items-center gap-1 bg-slate-900/40 px-2 py-0.5 rounded" :class="timeTextClass">
            <i data-lucide="clock" class="w-3.5 h-3.5"></i>
            <span x-text="timeString"></span>
        </div>
    </div>
    
    <div>
        <h3 class="text-xl font-black text-white leading-tight tracking-tight" x-text="item.producto"></h3>
        <template x-if="item.notes && item.notes.length > 0">
            <div class="mt-1.5 flex flex-col gap-1">
                <template x-for="note in item.notes">
                    <span class="text-xs font-bold text-amber-300 bg-amber-950/60 px-2 py-1 rounded w-fit flex items-center gap-1.5 border border-amber-500/30">
                        <i data-lucide="alert-circle" class="w-3 h-3"></i>
                        <span x-text="note"></span>
                    </span>
                </template>
            </div>
        </template>
    </div>

    <div class="mt-2 pt-2 border-t border-slate-600/50 flex justify-between items-center text-xs text-slate-400 font-bold uppercase tracking-wider">
        <span class="opacity-70" x-text="'Est. ' + item.estimated_time + 'm'"></span>
        <div class="flex items-center gap-3">
            <template x-if="hasPrevState">
                <span class="text-amber-500/70">Mantener ➔ Atrás</span>
            </template>
            <span class="text-orange-400" x-text="'Tap ➔ ' + (nextStateName || 'Terminar')"></span>
        </div>
    </div>
</div>
