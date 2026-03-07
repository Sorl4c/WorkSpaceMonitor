document.addEventListener("alpine:init", () => {
  Alpine.data("mesasView", () => ({
    get tablesData() {
      const items = this.$store.kds.items;
      const tablesMap = new Map();

      items.forEach((item) => {
        if (!tablesMap.has(item.mesa)) {
          tablesMap.set(item.mesa, {
            nombre: item.mesa,
            items: [],
            oldestPendingTime: null,
            totalItems: 0,
            completedItems: 0,
          });
        }
        const table = tablesMap.get(item.mesa);
        table.items.push(item);
        table.totalItems++;
        if (item.estado === "listo") table.completedItems++;

        if (item.estado !== "listo") {
          if (
            !table.oldestPendingTime ||
            item.estado_timestamp < table.oldestPendingTime
          ) {
            table.oldestPendingTime = item.estado_timestamp;
          }
        }
      });

      // Ordenar mesas numéricamente
      const sortedTables = Array.from(tablesMap.values()).sort((a, b) => {
        const numA = parseInt(a.nombre.replace(/\D/g, "")) || 0;
        const numB = parseInt(b.nombre.replace(/\D/g, "")) || 0;
        return numA - numB;
      });

      return sortedTables.map((table) => {
        // Agrupar items dentro de la mesa
        const groupedItemsMap = new Map();
        table.items.forEach((i) => {
          const notesArray = Array.isArray(i.notes) ? i.notes : [];
          const key = `${i.producto}-${i.estado}-${notesArray.join(",")}`;
          if (groupedItemsMap.has(key)) groupedItemsMap.get(key).qty++;
          else groupedItemsMap.set(key, { ...i, qty: 1, notes: notesArray });
        });

        const statusOrder = {
          pendiente: 1,
          cocina: 2,
          horno: 2,
          barra: 2,
          emplatado: 3,
          listo: 4,
        };
        table.groupedItems = Array.from(groupedItemsMap.values())
          .sort((a, b) => statusOrder[a.estado] - statusOrder[b.estado])
          .map((item) => ({
            ...item,
            status: this.getStatusDisplay(item.estado),
          }));

        // Lógica de tiempo para la mesa
        if (table.oldestPendingTime) {
          const elapsedMs =
            this.$store.kds.lastUpdate - table.oldestPendingTime;
          const minutes = Math.floor(elapsedMs / 60000);
          const seconds = Math.floor((elapsedMs % 60000) / 1000);
          table.timeString = `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;

          if (minutes >= 15) table.timeColor = "text-red-400 animate-pulse";
          else if (minutes >= 10) table.timeColor = "text-amber-400";
          else table.timeColor = "text-emerald-400";
        }

        table.isFullyDelivered =
          table.totalItems > 0 && table.completedItems === table.totalItems;
        // Add canBump flag (true if there is at least one item in 'emplatado' state)
        table.canBump = table.items.some((i) => i.estado === "emplatado");
        return table;
      });
    },

    getStatusDisplay(estado) {
      switch (estado) {
        case "pendiente":
          return {
            label: "Pendiente",
            color: "bg-slate-600 text-slate-200",
            dot: "bg-slate-400",
          };
        case "cocina":
        case "horno":
        case "barra":
          return {
            label: "En Preparación",
            color:
              "bg-orange-900/40 text-orange-400 border border-orange-500/30",
            dot: "bg-orange-500 animate-pulse",
          };
        case "emplatado":
          return {
            label: "Pase",
            color: "bg-cyan-900/40 text-cyan-400 border border-cyan-500/30",
            dot: "bg-cyan-400",
          };
        case "listo":
          return {
            label: "Entregado",
            color: "bg-green-900/20 text-green-500/50",
            dot: "bg-green-500/50",
          };
        default:
          return {
            label: estado,
            color: "bg-slate-700 text-white",
            dot: "bg-white",
          };
      }
    },

    bumpTable(table) {
      const idsToBump = table.items
        .filter((i) => i.estado === "emplatado")
        .map((i) => i.id);

      if (idsToBump.length > 0) {
        this.$store.kds.advanceState(idsToBump, "listo");
      }
    },
  }));
});
