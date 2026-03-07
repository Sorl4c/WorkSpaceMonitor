<div class="flex gap-6 h-full items-stretch overflow-x-auto pb-4 custom-scrollbar fade-in">
    <!-- Columna Pendiente -->
    <div class="flex flex-1" x-data="{ title: 'Pendiente', icon: 'clock', type: 'pendiente' }">
        <?php include 'components/comanda_column.php'; ?>
    </div>

    <!-- Columna Preparación -->
    <div class="flex flex-1" x-data="{ title: 'Preparación', icon: 'utensils', type: 'preparacion' }">
        <?php include 'components/comanda_column.php'; ?>
    </div>

    <!-- Columna Emplatado -->
    <div class="flex flex-1" x-data="{ title: 'Emplatado', icon: 'check-circle', type: 'emplatado' }">
        <?php include 'components/comanda_column.php'; ?>
    </div>
</div>