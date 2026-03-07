# Master Plan UI Migration

## Estado actual

Workspace Monitor ya tiene una base funcional valida:

- Backend FastAPI operativo en `src/main.py`.
- SSE operativo en `GET /events`.
- Endpoints auxiliares en `GET /desktops`, `GET /windows`, `GET /terminals`, `GET /terminals/{pid}`, `POST /terminals/{pid}`.
- Dashboard Alpine MVP operativo en `static/index.html`.
- Mock snapshot real disponible en `docs/plan-ui/mock-data/current_snapshot.json`.
- Referencia visual React disponible en `docs/plan-ui/react-base.md`.
- Referencia de arquitectura Alpine/KDS reutilizable en `docs/plan-ui/frontend-alpine-arquitercture/`.

Conclusión: no falta backend nuevo para arrancar la migración visual. Falta diseñar y ejecutar la capa de normalización, semántica y layout.

## Objetivo

Sustituir el dashboard plano actual por una UI Alpine.js con semántica cognitiva de escritorios, manteniendo FastAPI + SSE como fuente real de estado, usando la referencia React como contrato visual y el patrón KDS Alpine como contrato estructural.

## Lo que ya está resuelto

- El contrato base de datos ya existe: `desktops`, `windows`, `terminals`.
- El refresco tiempo real ya existe mediante SSE.
- El naming manual de terminales ya existe.
- El prototipo React ya define la dirección visual general:
  - sidebar de escritorios
  - panel principal del escritorio activo
  - agrupación por bloques semánticos
  - distinción entre señal y ruido
- El ejemplo KDS Alpine ya demuestra un patrón claro para:
  - `Alpine.store(...)`
  - vistas derivadas
  - componentes desacoplados
  - persistencia con `Alpine.$persist`
  - manejo de SSE
  - estados derivados y helpers

## Lo que falta realmente

Faltan 7 piezas:

1. Definir el contrato normalizado de frontend para no renderizar directamente el payload crudo.
2. Diseñar el store `wm` completo.
3. Traducir React a componentes Alpine concretos.
4. Implementar heurísticas de clasificación semántica.
5. Separar modo `mock` y modo `live`.
6. Añadir persistencia de preferencias UI.
7. Validar todo con snapshot real y con SSE real.

## Inventario fuente

### Referencias de entrada

- Visual reference: `docs/plan-ui/react-base.md`
- Mock real: `docs/plan-ui/mock-data/current_snapshot.json`
- Alpine architecture pattern: `docs/plan-ui/frontend-alpine-arquitercture/`
- Dashboard actual: `static/index.html`
- Backend real: `src/main.py`

### Contrato backend confirmado

`/events` emite este shape:

```json
{
  "desktops": [],
  "windows": [],
  "terminals": []
}
```

Cada bloque tiene esta semántica:

- `desktops`: `{ id, number, name }`
- `windows`: `{ hwnd, title, desktop_id, pid }`
- `terminals`: `{ pid, name, custom_name }`

## Principios no negociables

Estos puntos deben quedar fijados antes de pedir implementación:

- No tocar la fuente de verdad del backend salvo necesidad real.
- No renderizar directamente `windows` sin capa de derivación.
- La referencia React manda en layout, jerarquía y semántica visual.
- La implementación final debe vivir en Alpine.js, no en React.
- El modo mock debe permitir desarrollo sin daemon vivo.
- El modo live debe consumir `/events` sin romper el flujo mock.
- La UI debe diferenciar actividad productiva, soporte y ruido.

## Arquitectura objetivo

## Estructura propuesta

```text
static/
  index.html
  css/
    ui.css
  js/
    app.js
    store/
      wm-store.js
    services/
      sse.js
      mock-loader.js
      persistence.js
    utils/
      normalize.js
      classify.js
      summary.js
    components/
      sidebar.js
      desktop-header.js
      semantic-panel.js
      window-list.js
      empty-state.js
      debug-panel.js
```

## Store objetivo

El store debe ser `Alpine.store('wm', ...)`.

### Estado base

```js
{
  mode: 'mock' | 'live',
  online: false,
  loading: false,
  error: null,
  lastUpdate: null,
  activeDesktopId: null,
  showEmptyDesktops: false,
  showNoise: true,
  debug: false,
  raw: {
    desktops: [],
    windows: [],
    terminals: []
  },
  normalized: {
    desktops: [],
    desktopMap: {},
    windowsByDesktop: {},
    terminalsByPid: {}
  }
}
```

### Acciones mínimas

- `init()`
- `loadMockState()`
- `connectSSE()`
- `disconnectSSE()`
- `setMode(mode)`
- `setActiveDesktop(desktopId)`
- `toggleEmptyDesktops()`
- `toggleNoise()`
- `toggleDebug()`
- `applyIncomingState(payload)`
- `normalizeState(payload)`

### Getters derivados mínimos

- `desktopsWithSummary`
- `activeDesktop`
- `activeDesktopSummary`
- `activeDesktopSemanticBuckets`
- `emptyDesktops`
- `productiveDesktops`
- `desktopCount`
- `windowCount`
- `anchorTerminals`

## Contrato normalizado de frontend

No se debe pintar `windows` tal cual llegan. La UI final debe trabajar con un modelo derivado como este:

```json
{
  "id": "desktop-14",
  "desktopId": "{2041DD79-94FC-48C6-87B7-EAD8BBDBF199}",
  "number": 14,
  "name": "WorkspaceMonitor Dev",
  "rawWindowCount": 9,
  "semanticSummary": "2 term · 1 cod · 4 web · 1 files · 1 comms",
  "buckets": {
    "terminal": [],
    "code": [],
    "files": [],
    "web": [],
    "comms": [],
    "system": []
  }
}
```

Cada ventana derivada debe incluir:

```json
{
  "hwnd": 123,
  "pid": 456,
  "desktop_id": "...",
  "title": "react-base.md - WorkspaceMonitor - Visual Studio Code",
  "processName": "Code.exe",
  "terminalName": "WorkspaceMonitor",
  "displayTitle": "react-base.md - WorkspaceMonitor - Visual Studio Code",
  "semanticType": "code",
  "semanticSubType": "editor",
  "isAnchor": false,
  "isNoise": false,
  "importance": "high"
}
```

Nota: `processName` no está hoy en el payload de `windows`; si no se añade en backend, las heurísticas deberán operar sobre `title`, `pid` y cruce con `terminals`.

## Mapeo React -> Alpine

### React reference

La referencia React ya define estas zonas:

1. Sidebar izquierda con escritorios.
2. Header del escritorio activo.
3. Panel principal con bloques semánticos.
4. Grupo colapsable de escritorios vacíos.
5. Capa de ambigüedad o ruido separada del contenido principal.

### Alpine target

Mapeo recomendado:

- `WorkspaceMonitor` -> `index.html` + `Alpine.store('wm')`
- Sidebar desktops -> `components/sidebar.js`
- Active desktop header -> `components/desktop-header.js`
- Semantic section shell -> `components/semantic-panel.js`
- Lists por bucket -> `components/window-list.js`
- Empty states -> `components/empty-state.js`
- Debug and raw payload inspector -> `components/debug-panel.js`

## Heurísticas mínimas

Estas heurísticas deben existir desde la primera versión usable.

### Clasificación principal

- `terminal`
  - match por PID presente en `terminals`
  - match por título con `ready`, `powershell`, `cmd`, `bash`, `wsl`, `python`, `uvicorn`, `server`, `worker`, `tunnel`
- `code`
  - títulos con `Visual Studio Code`, `VS Code`, `Notepad++`, `Cursor`, `Sublime`, `vim`
- `files`
  - títulos con `Explorador de archivos`, `Explorer`
- `web`
  - títulos con `Edge`, `Chrome`, `Firefox`, `Comet`, `Gmail`, `ChatGPT`, `Perplexity`, `Gemini`, `NotebookLM`
- `comms`
  - títulos con `WhatsApp`, `Telegram`, `Discord`, `Slack`, `Gmail`
- `system`
  - resto no clasificado o utilidades del sistema

### Subclasificación útil

- `web.app` frente a `web.navigation`
- `code.editor` frente a `code.tool`
- `system.utility` frente a `system.noise`
- `terminal.anchor` frente a `terminal.generic`

### Reglas de importancia

- `high`
  - terminales con procesos activos o nombres custom
  - editores de código
  - ventanas con rutas o nombres de proyecto
- `medium`
  - exploradores de archivos relevantes
  - herramientas técnicas
  - web apps de trabajo
- `low`
  - pestañas genéricas
  - reproductores
  - settings
  - ventanas ambiguas

## Fases de implementación

## Fase 0 - Congelación de referencia

Objetivo: fijar el contrato visual y técnico.

Entregables:

- React reference marcada como base final.
- Snapshot mock confirmado como dataset principal.
- Decisión explícita sobre qué es intocable y qué es adaptable.

Criterios de aceptación:

- No se sigue iterando la UI React salvo bugs.
- Existe una lista de invariantes visuales.

## Fase 1 - Base del store y modo mock

Objetivo: crear la nueva base Alpine sin SSE todavía.

Trabajo:

- Crear `Alpine.store('wm')`.
- Cargar `current_snapshot.json`.
- Construir normalización inicial.
- Renderizar sidebar de escritorios.
- Permitir seleccionar escritorio activo.
- Mostrar resumen semántico por escritorio.

Criterios de aceptación:

- La UI funciona sin backend en vivo.
- El usuario puede navegar escritorios.
- Los escritorios vacíos se distinguen.

## Fase 2 - Layout principal y bloques semánticos

Objetivo: replicar el layout React con datos mock.

Trabajo:

- Header del escritorio activo.
- Bloques `terminal`, `code`, `web`, `files`, `comms`, `system`.
- Estado vacío por bloque.
- Colapsado de escritorios sin actividad.
- Estilo visual cercano a la referencia React.

Criterios de aceptación:

- El layout coincide funcionalmente con React.
- Cada bucket muestra solo su contenido.
- La capa de ruido no compite con la señal principal.

## Fase 3 - SSE real

Objetivo: sustituir mock por estado vivo sin romper la UI.

Trabajo:

- Crear servicio SSE.
- Consumir `GET /events`.
- Reaplicar `normalizeState()` en cada evento.
- Gestionar `online`, reconexión y errores.
- Mantener modo mock como fallback.

Criterios de aceptación:

- La UI reacciona cada vez que llega un evento.
- Si cae SSE, la UI no se rompe.
- Se puede alternar `mock/live` para depuración.

## Fase 4 - Heurísticas y semántica fina

Objetivo: convertir la lista de ventanas en lectura cognitiva útil.

Trabajo:

- Mejorar reglas de clasificación.
- Detectar terminales ancla.
- Separar `web-apps` de navegación.
- Separar `code` de herramientas.
- Marcar ruido y ambigüedad.
- Generar `semanticSummary`.

Criterios de aceptación:

- Los escritorios reflejan intención de trabajo, no solo volumen.
- Las terminales importantes destacan visualmente.
- El bucket `system` no se llena con ventanas que deberían ir en otro grupo.

## Fase 5 - Persistencia y debug

Objetivo: hacer la UI útil como herramienta diaria.

Trabajo:

- Persistir escritorio activo.
- Persistir toggles de `showEmptyDesktops`, `showNoise`, `debug`.
- Añadir panel debug con raw payload y normalized state.
- Añadir métricas simples: recuentos, timestamp, modo actual.

Criterios de aceptación:

- La preferencia del usuario sobrevive recargas.
- El debug acelera ajuste de heurísticas.

## Fase 6 - Pulido

Objetivo: cerrar calidad visual y técnica.

Trabajo:

- Microtransiciones.
- Scrollbars y estados vacíos.
- Adaptación desktop/mobile razonable.
- Limpieza de CSS y utilidades.
- Endurecer textos, labels y consistencia visual.

Criterios de aceptación:

- La UI se siente producto y no prototipo.
- No hay regresión de legibilidad con datos densos.

## Plan de ejecución para Codex Web

Codex Web no debe recibir una orden difusa. Debe trabajar por fases cerradas.

### Orden recomendado

1. Crear store `wm` y modo mock.
2. Renderizar sidebar + desktop activo.
3. Renderizar buckets semánticos.
4. Añadir capa de normalización.
5. Integrar SSE real.
6. Añadir persistencia.
7. Añadir debug.
8. Pulir visual y limpiar.

### Restricciones que debes pasarle

- No rehacer backend salvo necesidad muy justificada.
- No mover la app a React.
- No introducir frameworks adicionales.
- Mantener Alpine.js como stack final.
- Reutilizar `static/index.html` como punto de entrada salvo mejor razón.
- Si hace falta modularizar, hacerlo en `static/js/` y `static/css/`.

## Riesgos reales

1. El payload de `windows` no incluye `process_name`, lo que limita clasificación robusta.
2. El snapshot actual puede representar solo un momento concreto y sesgar heurísticas.
3. La clasificación por título tendrá falsos positivos y falsos negativos.
4. Si el layout se implementa antes de la normalización, se acumulará deuda rápida.
5. Si no se separa `mock/live`, el desarrollo quedará acoplado al daemon real.

## Mitigaciones

- Arrancar con heurísticas explícitas y listas de palabras clave versionadas.
- Usar debug panel para ver `raw -> normalized`.
- Mantener snapshot real como fixture de regresión.
- Añadir más snapshots si aparecen escenarios extremos.
- Considerar ampliar backend más adelante con `process_name` en `windows`.

## Qué hace falta preparar todavía

Quedan pendientes estas piezas documentales y operativas:

- `docs/plan-ui/workspace-monitor-brief.md`
- `docs/plan-ui/migration-checklist.md`
- `docs/plan-ui/prompt-codex-web.md`
- Al menos 2 snapshots más:
  - escritorio limpio
  - escritorio caótico
- Decisión formal de invariantes visuales

## Checklist maestro

- [x] Confirmar referencia React.
- [x] Confirmar arquitectura Alpine de referencia.
- [x] Confirmar snapshot real.
- [x] Confirmar endpoints reales.
- [x] Confirmar dashboard actual.
- [ ] Definir invariantes visuales.
- [ ] Definir contrato normalizado final.
- [ ] Crear nuevo store `wm`.
- [ ] Separar modo `mock/live`.
- [ ] Implementar sidebar y selección de escritorio.
- [ ] Implementar panel principal del escritorio activo.
- [ ] Implementar buckets semánticos.
- [ ] Implementar heurísticas mínimas.
- [ ] Integrar SSE real.
- [ ] Añadir persistencia.
- [ ] Añadir debug panel.
- [ ] Pulir visualmente.
- [ ] Validar con snapshot y con daemon real.

## Qué debe pedirseles a Codex CLI y Codex Web

### Primero a Codex CLI

Pedir solo plan, no código.

Debe devolver:

- mapeo React -> Alpine
- estructura de carpetas
- diseño del store `wm`
- contrato `raw -> normalized`
- heurísticas mínimas
- riesgos
- orden de implementación
- criterios de aceptación por fase

### Después a Codex Web

Pedir implementación por fases.

Primera orden recomendada:

> Implementa la Fase 1 y la Fase 2 del `MASTER_PLAN_UI_MIGRATION.md` usando Alpine.js dentro de `static/`, sin tocar backend salvo necesidad estricta, y manteniendo compatibilidad con el snapshot mock y con el contrato SSE actual.

## Definición de terminado

La migración se considerará terminada cuando:

- el dashboard actual haya sido sustituido por la nueva UI Alpine
- funcione con mock y con SSE real
- clasifique ventanas en buckets útiles
- destaque señal frente a ruido
- persista preferencias básicas
- tenga un modo debug para ajustar heurísticas
- conserve simplicidad operativa sobre FastAPI + Alpine
