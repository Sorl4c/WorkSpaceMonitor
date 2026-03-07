<div class="fixed bottom-6 right-6 flex flex-col-reverse gap-3 z-50 pointer-events-none">
    <template x-for="toast in $store.kds.toasts" :key="toast.id">
        <div class="pointer-events-auto bg-slate-800 border-2 border-slate-600 text-white px-5 py-3 rounded-2xl shadow-2xl flex items-center gap-5 transition-all duration-300 transform translate-y-0 opacity-100">
            <div class="flex flex-col">
                <span class="text-sm font-black text-green-400 flex items-center gap-1">
                    <i data-lucide="check-circle" class="w-3.5 h-3.5"></i> Plato Finalizado
                </span>
                <span class="text-sm font-medium text-slate-200 mt-0.5">
                    <span class="text-slate-400" x-text="toast.mesa"></span> • <span x-text="toast.producto"></span>
                </span>
            </div>
            <div class="w-px h-10 bg-slate-600"></div>
            <button @click="$store.kds.undoToast(toast.id)" 
                class="flex items-center gap-2 bg-slate-700 hover:bg-slate-600 active:scale-95 px-4 py-2 rounded-xl text-sm font-bold text-white transition-all shadow">
                <i data-lucide="rotate-ccw" class="w-4 h-4 text-amber-400"></i> Deshacer
            </button>
            <button @click="$store.kds.removeToast(toast.id)" class="text-slate-500 hover:text-white transition-colors p-1">
                <i data-lucide="x" class="w-5 h-5"></i>
            </button>
        </div>
    </template>
</div>
