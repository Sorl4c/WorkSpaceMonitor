# Implementation Plan: Persistent Workspace Snapshots and Context Resume

## Strategic Intent
This track replaces the product's center of value.

The goal is no longer "monitor current windows in a nice dashboard".
The goal is "persist work context so the user can resume after interruption with minimal mental overhead".

This plan is intentionally detailed enough to be handed off as an implementation brief.

## Product Decisions Locked for This Track
- Runtime dashboard model: `snapshot refresh`, not SSE-first live streaming
- Persistence backend: `SQLite`
- Snapshot scope: full desktop state
- Capture modes in V1: manual + timed automatic
- Core persistent entities:
  - `Workspace`
  - `Project`
  - `Snapshot`
  - `DesktopSnapshot`
  - `WindowInstance`
  - `RestoreTask`
- Resume philosophy: progressive restore, not all-or-nothing
- Failure policy: unresolved items remain visible as pending manual actions

## Open Product Questions Left Intentionally Flexible
- retention policy for snapshot history
- exact semantics for terminal restore
- exact level of VS Code state restoration beyond project root
- whether future "logical workspaces" should be independent of Windows desktop numbering

## Implementation Principle
Do not try to build perfect restore in one pass.

Build in this order:
1. capture
2. persist
3. query and browse history
4. infer projects/workspaces
5. assist resume
6. automate restore gradually

## Phase 0: Stabilization Before New Foundation
- [ ] Task: Audit and align the current codebase with the real product direction
  - [ ] Sub-task: Remove SSE-first assumptions from implementation planning and document the refresh-first model
  - [ ] Sub-task: Inventory endpoints, frontend flows, and tests that still assume the old terminal naming or SSE behavior
  - [ ] Sub-task: Decide which current behaviors are authoritative versus leftover MVP residue
- [ ] Task: Repair baseline test architecture so the project can evolve safely
  - [ ] Sub-task: Fix broken imports and stale tests expecting deleted APIs such as old terminal tracker behavior
  - [ ] Sub-task: Add test seams for Windows-only integrations so core logic can be tested without full OS dependencies
  - [ ] Sub-task: Establish a minimum green test path for snapshot and persistence modules
- [ ] Task: Track known integration instability in navigation/focus behavior
  - [ ] Sub-task: Create an explicit bug note for taskbar flashing / inconsistent focus after cross-desktop jumps
  - [ ] Sub-task: Add instrumentation around desktop switch + focus sequencing to support later debugging

## Phase 1: Persistence Foundation
- [ ] Task: Introduce database module and lifecycle management
  - [ ] Sub-task: Create a dedicated persistence package for SQLite connection handling, migrations, and repositories
  - [ ] Sub-task: Define a local database path strategy suitable for tray app usage and app restarts
  - [ ] Sub-task: Add startup initialization for database creation and migrations
- [ ] Task: Design and implement the initial schema
  - [ ] Sub-task: Create tables for `workspaces`
  - [ ] Sub-task: Create tables for `projects`
  - [ ] Sub-task: Create tables for `snapshots`
  - [ ] Sub-task: Create tables for `snapshot_desktops`
  - [ ] Sub-task: Create tables for `snapshot_windows`
  - [ ] Sub-task: Create tables for `snapshot_terminals`
  - [ ] Sub-task: Create tables for `restore_tasks` and `restore_task_items`
  - [ ] Sub-task: Add indexes for timestamp lookups, workspace lookups, and snapshot traversal
- [ ] Task: Define persistence contracts
  - [ ] Sub-task: Create typed models or DTOs for captured state and persisted state
  - [ ] Sub-task: Separate raw OS observations from persistent entities
  - [ ] Sub-task: Ensure schema allows future repository metadata and AI annotations

## Phase 2: Snapshot Capture Pipeline
- [ ] Task: Formalize the snapshot capture service
  - [ ] Sub-task: Refactor current `gather_state()` into a reusable capture pipeline with explicit capture metadata
  - [ ] Sub-task: Add capture ids, timestamps, mode (`manual` or `auto`), and summary statistics
  - [ ] Sub-task: Preserve the full observed workspace, not only active dashboard-derived views
- [ ] Task: Persist full snapshots
  - [ ] Sub-task: Save one snapshot header plus its desktops/windows/terminal records transactionally
  - [ ] Sub-task: Mark snapshot status as valid, partial, or failed depending on capture outcome
  - [ ] Sub-task: Preserve raw data needed for later restore attempts
- [ ] Task: Add capture policies
  - [ ] Sub-task: Manual snapshot endpoint and UI action
  - [ ] Sub-task: Automatic capture scheduler with configurable interval
  - [ ] Sub-task: Guardrails to avoid overlapping captures
  - [ ] Sub-task: Basic deduplication or cheap no-op protection if snapshots are identical within a short interval

## Phase 3: Project and Workspace Modeling
- [ ] Task: Introduce project inference
  - [ ] Sub-task: Infer project root primarily from terminal cwd and active worker cwd
  - [ ] Sub-task: Infer project hints from VS Code window titles and editor context when available
  - [ ] Sub-task: Normalize root paths into stable project keys
- [ ] Task: Create persistent project records
  - [ ] Sub-task: Upsert projects discovered from snapshot capture
  - [ ] Sub-task: Support manual project name override
  - [ ] Sub-task: Reserve schema fields for future repository URL / GitHub linkage
- [ ] Task: Introduce workspace semantics
  - [ ] Sub-task: Define a first rule for mapping snapshot desktops to a dominant project or workspace
  - [ ] Sub-task: Allow a workspace to store preferred desktop intent and restore preferences
  - [ ] Sub-task: Keep workspace logic simple in V1 to avoid premature complexity

## Phase 4: Snapshot Query and Resume UI
- [ ] Task: Add snapshot browsing APIs
  - [ ] Sub-task: Endpoint for latest snapshot
  - [ ] Sub-task: Endpoint for recent snapshots list
  - [ ] Sub-task: Endpoint for one snapshot detail with desktops, windows, and inferred projects
  - [ ] Sub-task: Endpoint for current-versus-snapshot comparison
- [ ] Task: Add dashboard surfaces for persistence workflows
  - [ ] Sub-task: Add `Save Snapshot` action in the UI
  - [ ] Sub-task: Add recent snapshots panel or resume panel
  - [ ] Sub-task: Add summary chips showing capture mode, age, and restore readiness
- [ ] Task: Build the first resume-oriented view
  - [ ] Sub-task: Show desktops from a stored snapshot
  - [ ] Sub-task: Show anchor windows for each desktop when inferable
  - [ ] Sub-task: Mark items as `matched`, `restorable`, `pending manual`, or `unknown`
  - [ ] Sub-task: Let the user launch a restore attempt from one snapshot

## Phase 5: Progressive Restore Engine
- [ ] Task: Implement restore planning
  - [ ] Sub-task: Build a restore planner that converts snapshot contents into per-item restore actions
  - [ ] Sub-task: Detect which windows/apps already exist in the current session
  - [ ] Sub-task: Prefer reusing current windows before reopening applications
- [ ] Task: Implement first automatic restore actions
  - [ ] Sub-task: Restore VS Code by reopening saved project roots
  - [ ] Sub-task: Restore terminals with best-effort cwd where technically feasible
  - [ ] Sub-task: Restore file explorer windows for saved folders where technically feasible
  - [ ] Sub-task: Record browser/app anchors even if exact tab recreation is not yet possible
- [ ] Task: Implement desktop targeting
  - [ ] Sub-task: Attempt to reopen or move restored items into intended desktops
  - [ ] Sub-task: Record desktop placement success and failure per item
  - [ ] Sub-task: Keep this logic explicitly best-effort and diagnosable due to Windows API constraints
- [ ] Task: Handle partial failure correctly
  - [ ] Sub-task: Persist restore task results
  - [ ] Sub-task: Show unresolved items as pending manual actions
  - [ ] Sub-task: Provide manual action affordances where launch context is known

## Phase 6: Reliability, Diagnostics, and Retention
- [ ] Task: Add structured diagnostics
  - [ ] Sub-task: Log capture failures with item-level detail
  - [ ] Sub-task: Log restore failures with action type and OS error context when available
  - [ ] Sub-task: Record metrics such as matched items, reopened items, failed items, and pending items
- [ ] Task: Define safe retention behavior
  - [ ] Sub-task: Keep multiple snapshots by default
  - [ ] Sub-task: Mark latest successful snapshot explicitly
  - [ ] Sub-task: Add a pruning strategy placeholder without prematurely deleting user history
- [ ] Task: Protect user trust
  - [ ] Sub-task: Make it obvious when a restore is partial
  - [ ] Sub-task: Never claim full restoration when only anchors were recovered
  - [ ] Sub-task: Preserve enough raw detail for manual recovery

## Phase 7: Integration Hardening
- [ ] Task: Investigate the existing cross-desktop focus bug
  - [ ] Sub-task: Reproduce the flashing taskbar issue under controlled timing conditions
  - [ ] Sub-task: Experiment with settle delays and focus ordering
  - [ ] Sub-task: Determine whether restore should use a different focus strategy than normal jump
- [ ] Task: Harden Windows-specific reopen flows
  - [ ] Sub-task: Validate command-line launching for VS Code, terminals, and explorer
  - [ ] Sub-task: Measure what information is actually stable across reboots versus only within one session
  - [ ] Sub-task: Separate "restore intent" from "restore success" in all APIs and UI

## Suggested API Additions

### Capture
- [ ] `POST /api/snapshots`
  - create a manual snapshot
- [ ] `GET /api/snapshots/latest`
  - retrieve latest snapshot summary
- [ ] `GET /api/snapshots`
  - retrieve recent snapshots list
- [ ] `GET /api/snapshots/{snapshot_id}`
  - retrieve full snapshot detail

### Workspaces and Projects
- [ ] `GET /api/workspaces`
- [ ] `POST /api/workspaces`
- [ ] `PATCH /api/workspaces/{workspace_id}`
- [ ] `GET /api/projects`
- [ ] `PATCH /api/projects/{project_id}`

### Restore
- [ ] `POST /api/snapshots/{snapshot_id}/restore-plan`
  - generate restore plan without executing
- [ ] `POST /api/snapshots/{snapshot_id}/restore`
  - execute a restore attempt
- [ ] `GET /api/restore-tasks/{restore_task_id}`
  - fetch results and diagnostics

## Suggested Initial SQLite Schema

### `snapshots`
- [ ] `id`
- [ ] `capture_mode`
- [ ] `captured_at`
- [ ] `app_version`
- [ ] `status`
- [ ] `desktop_count`
- [ ] `window_count`
- [ ] `terminal_count`
- [ ] `notes_json`

### `snapshot_desktops`
- [ ] `id`
- [ ] `snapshot_id`
- [ ] `desktop_guid`
- [ ] `desktop_number`
- [ ] `desktop_name`
- [ ] `dominant_project_id`
- [ ] `summary_json`

### `snapshot_windows`
- [ ] `id`
- [ ] `snapshot_id`
- [ ] `desktop_snapshot_id`
- [ ] `hwnd_at_capture`
- [ ] `pid_at_capture`
- [ ] `process_name`
- [ ] `title`
- [ ] `clean_name`
- [ ] `semantic_type`
- [ ] `semantic_subtype`
- [ ] `importance`
- [ ] `tab_count`
- [ ] `project_id`
- [ ] `workspace_id`
- [ ] `restore_hint_json`

### `snapshot_terminals`
- [ ] `id`
- [ ] `snapshot_id`
- [ ] `window_snapshot_id`
- [ ] `terminal_pid`
- [ ] `terminal_name`
- [ ] `terminal_cwd`
- [ ] `worker_name`
- [ ] `worker_cwd`
- [ ] `worker_cmdline_json`

### `projects`
- [ ] `id`
- [ ] `root_path`
- [ ] `inferred_name`
- [ ] `manual_name`
- [ ] `repository_url`
- [ ] `metadata_json`

### `workspaces`
- [ ] `id`
- [ ] `name`
- [ ] `description`
- [ ] `dominant_project_id`
- [ ] `preferred_restore_strategy`
- [ ] `metadata_json`

### `restore_tasks`
- [ ] `id`
- [ ] `snapshot_id`
- [ ] `created_at`
- [ ] `status`
- [ ] `strategy`
- [ ] `summary_json`

### `restore_task_items`
- [ ] `id`
- [ ] `restore_task_id`
- [ ] `window_snapshot_id`
- [ ] `action_type`
- [ ] `status`
- [ ] `message`
- [ ] `diagnostics_json`

## Testing Strategy
- [ ] Task: Persistence tests
  - [ ] Sub-task: schema creation and migration tests
  - [ ] Sub-task: snapshot insert/readback tests
  - [ ] Sub-task: rollback behavior on partial failure
- [ ] Task: Capture pipeline tests
  - [ ] Sub-task: capture metadata and transactional persistence
  - [ ] Sub-task: handling of missing OS attributes
  - [ ] Sub-task: auto-capture scheduling behavior
- [ ] Task: Project inference tests
  - [ ] Sub-task: cwd to project normalization
  - [ ] Sub-task: VS Code title inference
  - [ ] Sub-task: ambiguous cases
- [ ] Task: Restore planning tests
  - [ ] Sub-task: existing window match logic
  - [ ] Sub-task: reopen action selection logic
  - [ ] Sub-task: pending manual action generation
- [ ] Task: UI and integration tests
  - [ ] Sub-task: save snapshot action
  - [ ] Sub-task: snapshot history rendering
  - [ ] Sub-task: restore plan rendering and result states

## Delivery Sequence Recommendation
If this track is implemented overnight by another agent, the safest order is:

1. fix stale tests and create persistence skeleton
2. implement SQLite schema and repositories
3. persist manual snapshots from current `gather_state()`
4. expose latest/recent snapshot APIs
5. add snapshot history UI and save action
6. add project inference and workspace mapping
7. add restore planner
8. add first best-effort restore actions
9. investigate desktop placement reliability

## Definition of Success for This Track
This track is successful when the app is no longer just a live organizer, but a persistent memory of the user's work context.

Minimum practical success:
- user can save a full workspace snapshot
- user can see it after restart
- user can inspect desktops/projects from that snapshot
- user can start a restore flow
- unresolved items remain visible and actionable instead of disappearing

Target success:
- user can reopen key apps and place them into intended desktops with enough reliability to materially reduce next-day restart friction
