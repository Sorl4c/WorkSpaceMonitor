# Tech Stack

## Architecture Overview
The application follows a lightweight daemon/local-server architecture. A Python backend runs as a Windows system tray application, providing an API and serving a lightweight local web dashboard.
The local dashboard updates in real time using **Server-Sent Events (SSE)**. FastAPI emits workspace state changes, and Alpine.js reflects them in the interface, avoiding aggressive polling while keeping the architecture simple and reactive. This is an intentional part of the MVP architecture.

## Core Technologies

### Languages
- **Python:** Used for the system daemon, OS API interactions, and local backend server.
- **JavaScript:** Used on the frontend for dashboard interactivity.

### Backend Daemon & API
- **FastAPI (Python):** Chosen for its high performance, ease of use, and built-in asynchronous support, making it ideal for a responsive local API, serving the dashboard, and streaming SSE.

### Frontend Web Dashboard
- **Alpine.js:** A rugged, minimal framework for composing JavaScript behavior in the UI. It provides reactivity with minimal overhead and no complex build steps, handling lightweight UI reactivity to SSE events seamlessly.

### Local Data Storage
- **SQLite:** A self-contained, serverless relational database used to store application state, workspace configurations, and persistent window metadata reliably.