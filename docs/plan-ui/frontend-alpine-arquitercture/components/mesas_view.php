<div class="h-full overflow-y-auto custom-scrollbar p-2" x-data="mesasView()">
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 pb-20">
        <template x-for="table in tablesData" :key="table.nombre">
            <div class="flex flex-col bg-slate-800/60 rounded-2xl border overflow-hidden shadow-xl"
                 :class="table.isFullyDelivered ? 'border-green-900/50 opacity-60' : 'border-slate-700/80'">
                
                <div class="bg-slate-800 px-5 py-4 border-b border-slate-700 flex justify-between items-center">
                    <h2 class="font-black text-xl text-white tracking-tight" x-text="table.nombre"></h2>
                    <div class="flex items-center gap-4">
                        <span class="text-xs font-bold text-slate-400" x-text="table.completedItems + '/' + table.totalItems"></span>
                        
                        <template x-if="!table.isFullyDelivered && table.oldestPendingTime">
                            <div class="font-mono font-bold flex items-center gap-1" :class="table.timeColor">
                                <i data-lucide="clock" class="w-4 h-4"></i>
                                <span x-text="table.timeString"></span>
                            </div>
                        </template>

                        <template x-if="table.isFullyDelivered">
                            <div class="text-green-500 flex items-center gap-1 font-bold text-sm">
                                <i data-lucide="check-circle" class="w-4.5 h-4.5"></i> Listo
                            </div>
                        </template>

                        <template x-if="!table.isFullyDelivered && table.canBump">
                            <button @click="bumpTable(table)" class="bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-colors shadow-md">
                                <i data-lucide="send" class="w-3.5 h-3.5"></i> Marchar Pase
                            </button>
                        </template>
                    </div>
                </div>

                <div class="p-4 flex flex-col gap-3 max-h-[350px] overflow-y-auto custom-scrollbar">
                    <template x-for="(item, idx) in table.groupedItems" :key="idx">
                        <div class="flex flex-col gap-1 p-3 rounded-lg" 
                             :class="item.status.color + (item.estado === 'listo' ? ' opacity-70 line-through decoration-green-500/50' : '')">
                            
                            <div class="flex justify-between items-start">
                                <div class="flex items-center gap-2">
                                    <template x-if="item.qty > 1">
                                        <span class="font-black text-xs bg-slate-900/50 px-1.5 py-0.5 rounded shadow-sm text-white" x-text="'x' + item.qty"></span>
                                    </template>
                                    <span class="font-bold" :class="item.estado === 'listo' ? 'text-slate-400' : 'text-slate-100'" x-text="item.producto"></span>
                                </div>
                                <div class="flex items-center gap-2 mt-0.5 shrink-0">
                                    <span class="h-2 w-2 rounded-full" :class="item.status.dot"></span>
                                    <span class="text-[10px] uppercase font-black tracking-wider opacity-80" x-text="item.status.label"></span>
                                </div>
                            </div>
                            
                            <template x-if="item.notes && item.notes.length > 0 && item.estado !== 'listo'">
                                <div class="flex gap-1 mt-1">
                                    <template x-for="note in item.notes">
                                        <span class="text-[10px] font-bold text-amber-200/80 bg-black/20 px-1.5 py-0.5 rounded flex items-center gap-1">
                                            <i data-lucide="alert-circle" class="w-2.5 h-2.5"></i>
                                            <span x-text="note"></span>
                                        </span>
                                    </template>
                                </div>
                            </template>
                        </div>
                    </template>
                </div>
            </div>
        </template>
    </div>
</div>
