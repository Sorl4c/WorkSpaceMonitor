<div class="flex flex-col flex-1 min-w-[350px] bg-slate-800/40 rounded-2xl border border-slate-700/60 overflow-hidden shadow-lg">
    <div class="bg-slate-800/90 px-4 py-3 border-b border-slate-700 flex justify-between items-center backdrop-blur-sm z-10">
        <h2 class="font-bold text-lg text-white flex items-center gap-2">
            <i :data-lucide="icon" class="w-5 h-5 text-orange-500"></i>
            <span x-text="title"></span>
        </h2>
        <span class="bg-slate-700/50 border border-slate-600 text-slate-200 text-xs font-black px-2.5 py-1 rounded-full"
              x-text="$store.kds.fullOrderColumns[type] ? $store.kds.fullOrderColumns[type].length : 0"></span>
    </div>
    <div class="p-3 overflow-y-auto flex-1 custom-scrollbar">
        <template x-if="!$store.kds.fullOrderColumns[type] || $store.kds.fullOrderColumns[type].length === 0">
            <div class="h-full flex flex-col items-center justify-center text-slate-500 opacity-60">
                <i data-lucide="check-circle" class="w-10 h-10 mb-3 opacity-50"></i>
                <p class="font-semibold text-sm">Sin comandas</p>
            </div>
        </template>
        
        <template x-if="$store.kds.fullOrderColumns[type] && $store.kds.fullOrderColumns[type].length > 0">
            <template x-for="order in $store.kds.fullOrderColumns[type]" :key="order.orderId">
                <?php include 'comanda_card.php'; ?>
            </template>
        </template>
    </div>
</div>