# Workspace Monitor – Documento de Conocimiento

## Key Takeaways

* Se ha completado un MVP funcional de **Workspace Monitor**: daemon en segundo plano, descubrimiento de escritorios virtuales en Windows 11, enumeración de ventanas, detección y etiquetado manual de terminales, y dashboard local en tiempo real mediante SSE.
* El backend expone endpoints FastAPI (`/desktops`, `/windows`, `/terminals`, `/events`) que devuelven un mapa consistente de `desktops`, `windows` y `terminals`, permitiendo correlacionar PID de procesos con ventanas y escritorios virtuales.
* La interfaz actual en Alpine.js cumple el MVP (grid por escritorio, ventanas actualizándose cada 2 segundos), pero es demasiado plana; el siguiente foco ya no es más backend, sino **ontología + diseño de producto** para convertirla en un mapa cognitivo del workspace.
* Se ha definido una **ontología mínima** para el producto: escritorio virtual, contexto, app, ventana, terminal, categoría, importancia y ruido, con sus roles y relaciones.
* Se ha esbozado un **esquema JSON v2** y reglas de clasificación automática (por `process_name`, título, terminales etiquetados, ruido) que permitirán pasar de “lista de ventanas” a “mapa de trabajo”.
* La estrategia de diseño recomendada: usar Gemini Web Canvas (React + mock data) para iterar visualmente el dashboard, y más tarde portar el diseño consolidado al stack real (FastAPI + Alpine.js).
* Para mantener el hiperfoco y evitar context switching, la mejor inversión de tiempo es profundizar en: ontología, taxonomía de apps, señales de relevancia, arquitectura de información y críticas UX, no en más detalles de implementación.

***

## Conceptos del Proyecto

### Objetivo del MVP

* Construir un **mapa visual del workspace** en Windows 11:
  * Descubrir todos los **escritorios virtuales** activos.
  * Enumerar **ventanas** abiertas y mapearlas a su escritorio.
  * Detectar **terminales** y permitir etiquetado manual (p. ej. “API Server”).
  * Servir un **dashboard local** que se actualiza en tiempo real (SSE) mostrando el estado actual del workspace.

### Alcance y no-alcance (según spec)

* En alcance:
  * Daemon en segundo plano y servidor local.
  * Integración con APIs de Windows 11 para:
    * Escritorios virtuales.
    * Ventanas y PIDs.
  * Tracking de terminales y persistencia de etiquetas en SQLite.
  * Dashboard Alpine.js + FastAPI con SSE.

* Fuera de alcance (para tracks futuras):
  * Gestión interactiva de ventanas desde el dashboard (mover, cerrar, enfocar).
  * Extracción profunda de pestañas de navegador.

### Fases del MVP (ya completadas)

* **Phase 1 – Foundation and System Daemon**
  * Project setup, esqueleto FastAPI.
  * Icono de bandeja + servidor local.
  * Integración con Windows 11 para listar escritorios virtuales.

* **Phase 2 – Window Enumeration and Terminal Tracking**
  * Enumeración de ventanas y mapeo a escritorios (hwnd, título, desktop_id, pid).
  * Detección de procesos de terminal con `psutil` (cmd.exe, powershell.exe, WindowsTerminal.exe).
  * API `/terminals` para listar terminales por PID y asignar `custom_name`.
  * Correlación PID terminal ↔ ventana.

* **Phase 3 – Dashboard and Real-time Updates**
  * Endpoint `/events` SSE:
    * Genera un estado periódico `{desktops, windows, terminals}`.
    * Envía eventos SSE continuos.
  * Implementación con `EventSource` en el frontend y Alpine.js para:
    * Recibir el JSON.
    * Poblar `desktops`, `windows`, `terminals`.
    * Refrescar la UI sin recarga.
  * Dashboard dark-mode en grid: una card por escritorio mostrando sus ventanas; al abrir/cerrar apps, el dashboard se actualiza.

***

## Ontología de Workspace Monitor

### Escritorio virtual

* **Definición**: Contenedor físico-lógico de mayor nivel (virtual desktop de Windows).
* **Propósito**: Macro-contexto de trabajo (“Backend & API”, “Investigación / IA”, “Comunicaciones”, etc.).
* **Relaciones**:
  * Contiene Contextos, Apps y Ventanas.
  * Toda ventana pertenece a un único escritorio.
* **UI**:
  * Selector/pestañas de escritorios.
  * Cards o columnas con nombre significativo (no solo “Desktop 1”).
* **Errores a evitar**:
  * Tratarlo como simple índice numérico sin nombre ni identidad visual.

### Contexto

* **Definición**: Agrupación semántica de actividades ligadas a un objetivo (p. ej. “Refactor Auth Service”).
* **Propósito**: Convertir una lista de ventanas en un **mapa de trabajo**; une recursos heterogéneos bajo una intención.
* **Relaciones**:
  * Vive dentro de un Escritorio.
  * Se suele anclar a un **terminal con etiqueta manual**.
  * Varias apps pueden pertenecer al mismo contexto.
* **UI**:
  * “Cajas” o bloques con título dominante.
  * Ventanas y apps “atraídas” visualmente a ese bloque.
* **Errores a evitar**:
  * Pretender automatizarlo todo; el nombre manual del usuario debe tener peso fuerte.

### App

* **Definición**: Entidad lógica de software (VS Code, Edge, DBeaver, Telegram).
* **Propósito**: Agrupar instancias (ventanas) y dar identidad reconocible (nombre + icono).
* **Relaciones**:
  * Padre de Ventanas.
  * Tiene una Categoría asignada (dev, chat, navegador, etc.).
* **UI**:
  * Icono + nombre amigable (no el .exe).
  * Posibilidad de colapsar múltiples ventanas bajo una app.
* **Errores a evitar**:
  * Confundir App con Proceso; una App puede corresponder a múltiples procesos.

### Ventana

* **Definición**: Instancia concreta de una App; unidad visual mínima.
* **Propósito**: Representar el documento/vista sobre el que se trabaja (archivo, pestaña, diálogo).
* **Relaciones**:
  * Pertenece a un Escritorio y a una App.
  * Puede estar o no asociada a un Contexto.
* **UI**:
  * Título principal, tal vez subtítulo/contexto.
  * Diferenciar ventana principal vs diálogos auxiliares.
* **Errores a evitar**:
  * Dar mismo peso visual a un “Save As…” que a la ventana principal de un IDE.

### Terminal

* **Definición**: Tipo especial de ventana de línea de comandos (cmd, PowerShell, Windows Terminal, etc.).
* **Propósito**:
  * Portal de comandos.
  * **Fuente principal de etiquetas manuales de contexto**.
* **Relaciones**:
  * Subtipo de Ventana.
  * Sus `custom_label` pueden crear/nombrar Contextos; otras ventanas relacionadas se vinculan a ese contexto.
* **UI**:
  * Aspecto diferenciado (mono-space, icono de prompt).
  * Se muestra como “ancla” de su grupo.
* **Errores a evitar**:
  * Tratarlo como app genérica; es un sensor de intención del usuario.

### Categoría

* **Definición**: Rol funcional de una App (development, terminal, browser, webapp, chat, db, multimedia, system, ambiguous).
* **Propósito**:
  * Filtrado rápido.
  * Color, iconografía y chips consistentes por tipo.
* **Relaciones**:
  * Atributo de App.
* **UI**:
  * Badges/chips discretos de color.
  * Opciones de filtro por categoría.
* **Errores a evitar**:
  * Taxonomía demasiado amplia; ideal ≤ 7–8 categorías.

### Importancia

* **Definición**: Peso semántico de una Ventana en el flujo actual (active, relevant, background, noise).
* **Propósito**:
  * Jerarquizar; reducir carga visual.
* **Relaciones**:
  * Estado dinámico de la Ventana (relacionado con foco, uso reciente, contexto).
* **UI**:
  * Tamaño, brillo, opacidad y grosor de borde distintos según importancia.
* **Errores a evitar**:
  * Modelo binario activo/inactivo; se prefiere un gradiente.

### Ruido

* **Definición**: Ventanas que aportan poco al mapa mental (overlays, utility windows, processes de sistema, diálogos temporales).
* **Propósito**:
  * Mantener el dashboard limpio.
* **Relaciones**:
  * Es una etiqueta/filtro sobre Ventanas.
* **UI**:
  * Ocultas por defecto o agrupadas en un “Ruido / Sistema” colapsable.
* **Errores a evitar**:
  * Eliminarlas del todo; debe existir un modo debug donde se ve “todo”.

***

## Datos Técnicos y Modelo de Estado

### Entidades actuales (estado MVP)

* **Desktop**
  * Campos confirmados:
    * `id` (GUID).
    * `number` (1..N).
    * `name` (puede ser vacío si el usuario no ha renombrado).
* **Window**
  * `hwnd` (handle).
  * `title`.
  * `desktop_id`.
  * `pid`.
* **Terminal**
  * Detectada con `psutil` (cmd.exe, powershell.exe, WindowsTerminal.exe, etc.).
  * Campos:
    * `pid`.
    * `name` (ejecutable).
    * `custom_name` (etiqueta manual persistida en SQLite).
* **Proceso**
  * `pid`.
  * `name` (ejecutable).

### Esquema JSON v2 propuesto (abstracto)

* Campo raíz:
  * `timestamp`.
  * `active_hwnd`.
* `desktops`:
  * `id`, `number`, `name`.
  * `apps`: agrupación por app/contexto.
  * Cada `app`:
    * `app_id`, `name`, `category`, `context_id`.
    * `windows`: lista con `hwnd`, `title`, `is_active`, `geometry`.
  * `noise`: lista de elementos clasificados como ruido.

### Campos adicionales deseables

* Prioridad alta:
  * `is_active` (bool, ventana con foco).
  * `normalized_name` (“Google Chrome” en vez de chrome.exe).
  * `geometry` (x, y, w, h) para mapear posición y tamaño.
* Prioridad media:
  * `is_system_window` (bool).
  * `browser_domain` (dominio principal para distinguir web-apps).
* Prioridad baja:
  * `process_path` (extraer iconos).
  * `shell_type` para terminales (cmd, pwsh, bash).
  * `icon_key` o `icon_path`.

***

## Clasificación y Heurísticas

### Taxonomía propuesta de tipos de app

* development (VS Code, IDEs)
* terminal
* browser (navegación general)
* webapp (Gmail, Perplexity, Jira, etc. dentro del navegador)
* chat / communication
* db / tools (DBeaver, XAMPP)
* files / system explorer
* multimedia (Spotify, YouTube, reproductores)
* system (Task Manager, Settings, overlays)
* ambiguous / unknown

### Reglas de clasificación automática (ejemplos)

* **Por `process_name`**:
  * `Code.exe`, `idea64.exe`, `pycharm.exe` → `development`.
  * `WindowsTerminal.exe`, `cmd.exe`, `powershell.exe` → `terminal`.
  * `msedge.exe`, `chrome.exe`, `firefox.exe` → `browser` (si no se detecta web-app).
  * `Discord.exe`, `Telegram.exe`, etc. → `chat`.
  * `DBeaver.exe` → `db`.
  * `explorer.exe` → `files/system`.
* **Por título + proceso (web-app)**:
  * Proceso navegador + título contiene “Gmail”, “Perplexity”, “Jira”, etc.:
    * Re-clasificar como `webapp` con identificador de servicio.
* **Relación terminal–ventana**:
  * Ventanas cuyo `pid` coincide con un terminal etiquetado o que se lanzan desde él → asociadas al mismo contexto.
* **Ruido / sistema**:
  * Títulos vacíos o procesos conocidos de sistema (Taskmgr, ApplicationFrameHost, overlays) → `noise` o `system`.

***

## Experiencia de Usuario y Dashboard

### Estado actual del dashboard

* Frontend:
  * Una página dark-mode simple.
  * Grid de cards, una por escritorio virtual.
  * Dentro de cada card:
    * Título de escritorio (name o “Desktop N”).
    * Lista de ventanas (`title`), con posible badge de terminal (`[custom_name]`) si hay correlación por PID.
* Comportamiento:
  * Al abrir/cerrar ventanas o terminales, el dashboard se actualiza automáticamente vía `/events` SSE.
  * No hay filtros, distinción visual entre tipos de app ni jerarquía de importancia.

### Problemas UX detectados

* Visualización plana:
  * Todo se muestra como lista homogénea, sin jerarquía clara de foco/contexto/ruido.
* Falta de semántica:
  * Browser vs web-app vs app nativa se ven igual.
* Terminales:
  * Aun siendo clave para el contexto, se visualizan casi como cualquier ventana más.
* Ruido:
  * Ventanas de sistema y utilidades compiten visualmente con ventanas reales de trabajo.
* Sin contexto:
  * Faltan agrupaciones por “proyecto” o contexto lógico.

### Direcciones de diseño exploradas (a alto nivel)

* **Bento Clarity**:
  * Grid modular, cards por contexto o categoría.
  * Apto para ver densidad de tipos de apps.
* **Focus Hub**:
  * Vista centrada en la ventana/contexto activo, con herramientas de soporte alrededor.
* **Workspace Map**:
  * Mapa espacial de ventanas según geometría real; útil para usuarios con fuerte memoria espacial.

La reacción del usuario ha sido que las propuestas renderizadas como UI React parecían más un **dashboard genérico** de SaaS que el “mapa mental de trabajo” que tiene en mente, por lo que se decide abrir un nuevo hilo y redefinir con más fuerza la metáfora de diseño.

***

## Estrategia de Diseño y Próximos Pasos

### Línea estratégica

* Backend MVP ya está en buen estado:
  * No se quiere seguir iterando en la CLI por ahora.
* Siguiente prioridad:
  * Usar Gemini Web Canvas (React + mock data) para encontrar **una dirección visual fuerte**:
    * Menos “panel corporativo”.
    * Más “mapa cognitivo de trabajo personal”.
* Después:
  * Traducir ese diseño a la implementación real (FastAPI + Alpine.js), reutilizando el modelo conceptual y el esquema JSON.

### Qué debe enfatizar el nuevo diseño

* Metáfora:
  * Orientación cognitiva, no monitorización.
* Jerarquía:
  * Escritorio → Contexto → Grupo de apps → Ventanas.
* Terminal etiquetado:
  * Debe ser el centro de su contexto, no una ventana más.
* Ruido:
  * Fuera de la vista principal por defecto; visible solo en modos secundarios.
* Navegador vs web-app:
  * Se deben diferenciar visualmente para transmitir intención (lectura, investigación, app productiva, ocio).

### Prompts clave acordados para el nuevo hilo de diseño

* Explicar claramente que:
  * El diseño anterior parecía un panel genérico.
  * Se desea una sola dirección visual principal, no varias.
  * Primero se debe describir la intención y metáfora de la UI, luego el prototipo.
* Exigir:
  * Foco en contextos, no en widgets.
  * Un dashboard que responda a:
    * ¿En qué escritorio estoy?
    * ¿Qué contextos hay?
    * ¿Cuál es mi foco?
    * ¿Qué ventanas son relevantes o ruido?

***

## Referencias

* Especificación del MVP (virtual desktops, window enumeration, terminal tracking, local dashboard con SSE).
* Plan de fases (Foundation, Window Enumeration & Terminal Tracking, Dashboard & Real-time Updates).
* Notas internas sobre:
  * Ontología de Workspace Monitor (escritorio, contexto, app, ventana, terminal, categoría, importancia, ruido).
  * Esquema JSON v2 propuesto.
  * Reglas heurísticas de clasificación.
  * Campos adicionales de backend deseables (is_active, geometry, browser_domain, etc.).
* Ejemplos de UI generadas en React (tres variantes: claridad, foco, espacial) que se usarán como material de contraste, no como diseño final.