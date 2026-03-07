# Implementation Plan: MVP Workspace Map

## Phase 1: Foundation and System Daemon
- [x] Task: Project setup and FastAPI skeleton [93ab9fb]
    - [ ] Sub-task: Write tests for basic API endpoints
    - [ ] Sub-task: Implement FastAPI server and tray icon boilerplate
- [x] Task: Virtual Desktop Discovery API integration [9002761]
    - [ ] Sub-task: Write tests for OS API wrappers
    - [ ] Sub-task: Implement Windows 11 virtual desktop querying logic
- [~] Task: Conductor - User Manual Verification 'Phase 1: Foundation and System Daemon' (Protocol in workflow.md)

## Phase 2: Window Enumeration and Terminal Tracking
- [ ] Task: Window Enumeration mapping
    - [ ] Sub-task: Write tests for window-to-desktop mapping logic
    - [ ] Sub-task: Implement window enumeration and filtering
- [ ] Task: Terminal process tracking
    - [ ] Sub-task: Write tests for terminal detection and naming prompt logic
    - [ ] Sub-task: Implement tracking and manual naming feature
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Window Enumeration and Terminal Tracking' (Protocol in workflow.md)
    - [ ] Sub-task: Persist manual terminal labels in SQLite and restore them on subsequent detections when possible


## Phase 3: Dashboard and Real-time Updates
- [ ] Task: SSE implementation in FastAPI
    - [ ] Sub-task: Write tests for SSE endpoint and event generation
    - [ ] Sub-task: Implement state diffing and event streaming
- [ ] Task: Alpine.js Web Dashboard
    - [ ] Sub-task: Write tests for frontend data models and SSE connection
    - [ ] Sub-task: Implement minimalist UI matching design guidelines
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Dashboard and Real-time Updates' (Protocol in workflow.md)