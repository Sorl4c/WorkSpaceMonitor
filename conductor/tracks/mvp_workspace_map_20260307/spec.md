# Specification: MVP Workspace Map

## Overview
Build the initial MVP for Workspace Monitor. This track covers the core Python daemon, Windows 11 API integration for virtual desktop and window discovery, terminal tracking, and the Alpine.js local web dashboard for visualizing the workspace state.

## Functional Requirements
- **Virtual Desktop Discovery:** Query the OS to list all active virtual desktops.
- **Window Enumeration:** Enumerate all open windows and map them to their respective virtual desktops.
- **Terminal Tracking:** Detect new terminal sessions and allow the user to manually assign names to them.
- **Local Dashboard:** Serve a local web interface via FastAPI that summarizes the current state using Server-Sent Events (SSE) to push updates.
- **Terminal Metadata Persistence:** Store manual terminal labels in SQLite so they survive snapshots and app restarts when possible.


## Non-Functional Requirements
- **Performance:** Low CPU/RAM usage; sub-500ms latency for SSE updates.
- **Resilience:** Graceful degradation on API failures or permission issues.
- **Security:** Dashboard strictly bound to localhost.

## Acceptance Criteria
- Manual terminal labels are persisted locally in SQLite and restored in subsequent snapshots and application restarts when possible.
- Running the daemon starts a system tray icon and a localhost server.
- The web dashboard accurately displays the number of virtual desktops and their associated windows.
- New windows reflect on the dashboard in real time without refreshing.
- Opening a new terminal triggers a prompt for a manual label, which is then tracked.

## Out of Scope
- Interactive window management (moving, closing, focusing) from the dashboard.
- Browser tab extraction (will be a separate track).