<header class="bg-slate-900 border-b border-slate-800 px-6 py-4 shrink-0 flex items-center justify-between shadow-xl z-10">
    <div class="flex items-center gap-6">
        <div class="flex items-center gap-3">
            <div class="bg-orange-500 text-white p-2.5 rounded-xl shadow-[0_0_20px_rgba(249,115,22,0.3)]">
                <i data-lucide="chef-hat" class="w-7 h-7"></i>
            </div>
            <div>
                <h1 class="text-2xl font-black text-white tracking-tight leading-none mb-1">KITCHEN<span class="text-orange-500">SYNC</span></h1>
                <p class="text-[10px] uppercase font-bold flex items-center gap-1.5 tracking-wider"
                   :class="$store.kds.online ? 'text-green-400' : 'text-red-400'">
                    <span class="relative flex h-2 w-2">
                        <span class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75" :class="$store.kds.online ? 'bg-green-400' : 'bg-red-400'"></span>
                        <span class="relative inline-flex rounded-full h-2 w-2" :class="$store.kds.online ? 'bg-green-500' : 'bg-red-500'"></span>
                    </span>
                    <span x-text="$store.kds.online ? 'En Línea' : 'Desconectado'"></span>
                </p>
            </div>
        </div>

        <!-- Toggles de Vista -->
        <div class="hidden md:flex bg-slate-800 p-1 rounded-xl border border-slate-700 ml-4">
            <button @click="$store.kds.activeView = 'kanban'"
                class="px-4 py-2 rounded-lg font-bold text-sm transition-all duration-200 flex items-center gap-2"
                :class="$store.kds.activeView === 'kanban' ? 'bg-slate-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'">
                <i data-lucide="kanban-square" class="w-4 h-4"></i> Kanban
            </button>
            <button @click="$store.kds.activeView = 'comanda'"
                class="px-4 py-2 rounded-lg font-bold text-sm transition-all duration-200 flex items-center gap-2"
                :class="$store.kds.activeView === 'comanda' ? 'bg-slate-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'">
                <i data-lucide="receipt" class="w-4 h-4"></i> Comanda
            </button>
            <button @click="$store.kds.activeView = 'mesas'"
                class="px-4 py-2 rounded-lg font-bold text-sm transition-all duration-200 flex items-center gap-2"
                :class="$store.kds.activeView === 'mesas' ? 'bg-slate-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'">
                <i data-lucide="layout-grid" class="w-4 h-4"></i> Mesas
            </button>
            <button @click="$store.kds.activeView = 'servidos'"
                class="px-4 py-2 rounded-lg font-bold text-sm transition-all duration-200 flex items-center gap-2"
                :class="$store.kds.activeView === 'servidos' ? 'bg-slate-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'">
                <i data-lucide="history" class="w-4 h-4"></i> Servidos
            </button>
        </div>
    </div>

    <div class="flex items-center gap-4">
        <!-- Filtros Kanban -->
        <template x-if="$store.kds.activeView === 'kanban'">
            <div class="hidden lg:flex bg-slate-800/80 p-1 rounded-xl border border-slate-700/50">
                <template x-for="f in [{id:'todo', l:'Todo'}, {id:'barra', l:'Barra'}, {id:'cocina', l:'Cocina'}, {id:'horno', l:'Horno'}]">
                    <button @click="$store.kds.activeFilter = f.id"
                        class="px-6 py-2 rounded-lg font-bold text-sm transition-all duration-200"
                        :class="$store.kds.activeFilter === f.id ? 'bg-orange-500 text-white shadow-md' : 'text-slate-400 hover:text-slate-100 hover:bg-slate-700/50'"
                        x-text="f.l">
                    </button>
                </template>
            </div>
        </template>
    </div>
</header>
