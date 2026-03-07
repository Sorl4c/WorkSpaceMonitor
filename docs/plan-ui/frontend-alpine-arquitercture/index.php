<!DOCTYPE html>
<html lang="es" class="h-full">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KitchenSync KDS | Alpine Edition</title>
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- Lucide Icons (Para paridad con React) -->
    <script src="https://unpkg.com/lucide@latest"></script>

    <!-- Estilos Globales -->
    <style>
        [x-cloak] { display: none !important; }
        
        /* Scrollbar personalizada para paridad visual */
        .custom-scrollbar::-webkit-scrollbar { width: 6px; height: 6px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background-color: #334155; border-radius: 10px; }
    </style>
</head>
<body class="h-full bg-[#0B1120] text-slate-200 font-sans select-none overflow-hidden" x-data x-cloak>

    <div class="h-screen w-full flex flex-col relative">
        <?php include 'components/header.php'; ?>
        <!-- ... resto del contenido ... -->

        <main class="flex-1 p-6 overflow-hidden flex flex-col relative">
            <!-- Vista Kanban -->
            <template x-if="$store.kds.activeView === 'kanban'">
                <div class="flex gap-6 h-full items-stretch overflow-x-auto pb-4 custom-scrollbar fade-in">
                    <!-- Columna Pendiente -->
                    <div class="flex flex-1" x-data="{ title: 'Pendiente', icon: 'clock', type: 'pendiente' }">
                        <?php include 'components/kanban_column.php'; ?>
                    </div>

                    <!-- Columna Cocina -->
                    <template x-if="$store.kds.activeFilter === 'todo' || $store.kds.activeFilter === 'cocina'">
                        <div class="flex flex-1" x-data="{ title: 'Cocina', icon: 'utensils', type: 'cocina' }">
                            <?php include 'components/kanban_column.php'; ?>
                        </div>
                    </template>

                    <!-- Columna Horno -->
                    <template x-if="$store.kds.activeFilter === 'todo' || $store.kds.activeFilter === 'horno'">
                        <div class="flex flex-1" x-data="{ title: 'Horno', icon: 'flame', type: 'horno' }">
                            <?php include 'components/kanban_column.php'; ?>
                        </div>
                    </template>

                    <!-- Columna Barra -->
                    <template x-if="$store.kds.activeFilter === 'todo' || $store.kds.activeFilter === 'barra'">
                        <div class="flex flex-1" x-data="{ title: 'Barra', icon: 'martini', type: 'barra' }">
                            <?php include 'components/kanban_column.php'; ?>
                        </div>
                    </template>

                    <!-- Columna Emplatado -->
                    <div class="flex flex-1" x-data="{ title: 'Emplatado', icon: 'check-circle', type: 'emplatado' }">
                        <?php include 'components/kanban_column.php'; ?>
                    </div>
                </div>
            </template>

            <!-- Vista Mesas -->
            <template x-if="$store.kds.activeView === 'mesas'">
                <?php include 'components/mesas_view.php'; ?>
            </template>

            <!-- Vista Comanda -->
            <template x-if="$store.kds.activeView === 'comanda'">
                <?php include 'components/comanda_view.php'; ?>
            </template>

            <!-- Vista Servidos -->
            <template x-if="$store.kds.activeView === 'servidos'">
                <?php include 'components/servidos_view.php'; ?>
            </template>

            <?php include 'components/toasts.php'; ?>
        </main>
    </div>

    <!-- Audio para nuevas comandas -->
    <audio id="new-order-sound" src="assets/ding.mp3" preload="auto"></audio>

    <!-- 1. Alpine.js Plugins -->
    <script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/persist@3.x.x/dist/cdn.min.js"></script>

    <!-- 2. Lógica de la Aplicación (con defer para mantener orden secuencial) -->
    <script defer src="js/store.js?v=2"></script>
    <script defer src="js/components/header.js?v=2"></script>
    <script defer src="js/components/kanbanCard.js?v=2"></script>
    <script defer src="js/components/comandaCard.js?v=2"></script>
    <script defer src="js/app.js?v=2"></script>

    <!-- 3. Alpine.js Core (SIEMPRE EL ÚLTIMO) -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>

    <script>
        // Inicializar iconos Lucide tras la carga
        document.addEventListener('DOMContentLoaded', () => {
            lucide.createIcons();
        });
    </script>
</body>
</html>
