# Specification: Projects and Snapshot Memory

## 1. Scope
This track defines the first implementation-ready version of the product around three user-facing surfaces:

- `Live`
- `Projects`
- `Snapshots`

The goal is to stop expanding the product as a generic live monitor and instead make it useful for:

- launching known work setups
- capturing cognitive checkpoints
- resuming interrupted work with low mental overhead

## 2. Product Model

### 2.1 Live
`Live` is the current-state operational surface.

It shows what is open now and supports:

- inspecting desktops and windows
- jumping to windows and desktops
- saving a full snapshot
- saving a desktop snapshot

`Live` is observational. It is not the source of truth for reusable setup definitions.

### 2.2 Project
`Project` is the main long-lived manual configuration entity.

A project is a reusable launch profile. It defines what should be opened when the user wants to start work intentionally.

`Project` supports:

- identity
- root path
- optional GitHub linkage
- VS Code launch target
- terminal profiles
- optional auxiliary app profiles
- preferred desktop
- preferred layout zones

### 2.3 Snapshot
`Snapshot` is a historical memory artifact.

A snapshot is not a template and must not be treated as one in the UX.

It exists to help the user:

- pause exploratory work
- add a note
- revisit context later
- restore what is practical
- understand what was going on even if restore is partial

## 3. Locked Product Decisions

- `Workspace` is not a first-class visible product concept in this track.
- `Project` is the manual reusable setup concept.
- `Snapshot` is the memory/checkpoint concept.
- `Launch Project` and `Restore Snapshot` are separate flows in both UX and implementation.
- Window positioning is approximate by zone, not pixel-perfect.
- Snapshot scope must support both `full` and `desktop`.
- Snapshot restore is best-effort and must expose partial results honestly.

## 4. V1 Boundaries

### 4.1 In scope
- `Live` surface remains usable
- save full snapshot
- save desktop snapshot
- title and note on snapshots
- browse snapshots
- inspect snapshot detail
- basic restore-plan generation
- `Projects` CRUD
- project terminal profiles
- project app profiles for a minimal set of apps
- project launch
- approximate desktop and layout targeting

### 4.2 Out of scope
- pixel-perfect window restoration
- exact browser tab restore
- full multi-monitor fidelity across hardware changes
- AI summary generation
- GitHub automation actions such as push, pull request, issue creation
- converting snapshots into projects automatically

## 5. User Flows

### 5.1 Launch Project
User goes to `Projects`, selects a project, and clicks `Launch`.

Expected behavior:

- open VS Code on the configured root path
- open configured terminal profiles
- open optional configured apps
- attempt to move each opened window to the preferred desktop
- attempt to place each window into the configured zone
- continue if one launch item fails

### 5.2 Save Full Snapshot
User is in `Live` and clicks `Save Snapshot`.

Expected behavior:

- capture all visible desktops
- persist windows and terminals for all captured desktops
- allow optional title and note
- persist `scope = full`

### 5.3 Save Desktop Snapshot
User is in `Live` and saves the current desktop only.

Expected behavior:

- capture only the active desktop
- persist only windows and terminals for that desktop
- allow optional title and note
- persist `scope = desktop`
- persist captured desktop identity

### 5.4 Resume From Snapshot
User goes to `Snapshots`, opens a snapshot, and requests re-entry.

Expected behavior:

- show title and note first
- show captured desktops, windows, and terminals
- produce a restore plan with clear statuses
- allow user to attempt best-effort restore
- clearly mark items that require manual recovery

## 6. Minimal Data Model

### 6.1 Keep existing tables
- `projects`
- `project_terminal_profiles`
- `snapshots`
- `snapshot_desktops`
- `snapshot_windows`
- `snapshot_terminals`
- `restore_tasks`
- `restore_task_items`

### 6.2 De-emphasize
- `workspaces`

It may remain in storage temporarily for compatibility, but it is not part of the visible model for this track.

### 6.3 Projects
Minimum required fields for `projects`:

- `id`
- `manual_name`
- `root_path`
- `repository_url`
- `github_provider`
- `github_owner`
- `github_repo`
- `default_branch`
- `repo_local_path_confirmed`
- `notes`
- `preferred_desktop_number`
- `is_active`
- `created_at`
- `updated_at`

Rules:

- `root_path` is the primary identity for a project in V1.
- `manual_name` is the primary display name.
- GitHub fields are optional.

### 6.4 Project terminal profiles
Minimum required fields for `project_terminal_profiles`:

- `id`
- `project_id`
- `name`
- `cwd`
- `launch_command`
- `shell`
- `preferred_desktop_number`
- `preferred_zone`
- `sort_order`
- `auto_launch`
- `created_at`
- `updated_at`

Rules:

- a project can have multiple terminal profiles
- `cwd` is required
- `launch_command` is optional
- `preferred_zone` must be one of the allowed zones

### 6.5 Project app profiles
Add `project_app_profiles`.

Minimum required fields:

- `id`
- `project_id`
- `app_type`
- `display_name`
- `launch_target`
- `launch_args_json`
- `preferred_desktop_number`
- `preferred_zone`
- `auto_launch`
- `sort_order`
- `created_at`
- `updated_at`

Allowed `app_type` values in V1:

- `vscode`
- `explorer`
- `browser`
- `custom`

Rules:

- every project should support one `vscode` app profile
- additional app profiles are optional

### 6.6 Snapshots
Minimum required fields for `snapshots`:

- `id`
- `scope`
- `title`
- `note`
- `captured_at`
- `capture_mode`
- `status`
- `desktop_count`
- `window_count`
- `terminal_count`
- `captured_desktop_guid`
- `captured_desktop_number`
- `inferred_project_id`
- `is_pinned`
- `created_at`

Allowed `scope` values:

- `full`
- `desktop`

Rules:

- `title` is optional
- `note` is optional but first-class
- desktop-scoped snapshots must populate either `captured_desktop_guid` or `captured_desktop_number`

### 6.7 Snapshot desktops
Minimum required fields for `snapshot_desktops`:

- `id`
- `snapshot_id`
- `desktop_guid`
- `desktop_number`
- `desktop_name`
- `dominant_project_id`
- `summary_json`

### 6.8 Snapshot windows
Minimum required fields for `snapshot_windows`:

- `id`
- `snapshot_id`
- `desktop_snapshot_id`
- `hwnd_at_capture`
- `pid_at_capture`
- `process_name`
- `title`
- `clean_name`
- `semantic_type`
- `semantic_subtype`
- `tab_count`
- `project_id`
- `restore_hint_json`
- `window_rect_json`

Rules:

- `window_rect_json` stores observed position and size for future restore assistance
- `project_id` is nullable, but should be filled whenever a valid local project can be inferred

### 6.9 Snapshot terminals
Minimum required fields for `snapshot_terminals`:

- `id`
- `snapshot_id`
- `window_snapshot_id`
- `terminal_pid`
- `terminal_name`
- `terminal_cwd`
- `worker_name`
- `worker_cwd`
- `worker_cmdline_json`

Rules:

- `window_snapshot_id` should be linked whenever the terminal can be matched to a captured window

## 7. Project Inference Quality

`Project inference quality` in this track means:

- prefer filesystem-backed local paths
- prefer terminal `cwd`
- prefer editor root paths
- do not create projects from generic browser titles
- do not create projects from GitHub page titles alone
- when in doubt, do not infer a project

Minimum inference rules:

1. If a terminal has a valid local `cwd`, infer project from that path.
2. If a VS Code window exposes a local folder or workspace path, infer project from that path.
3. If a window title only contains a website title or browser tab text with no local path, do not create a project row from it.
4. Browser windows may reference an existing inferred project, but must not create one unless a valid local path is available.

Acceptance threshold for V1:

- no project rows should be created from plain GitHub page titles
- no project rows should be created from generic documentation page titles
- terminal and VS Code inference should dominate project creation

## 8. Layout and Desktop Model

### 8.1 Allowed zones
Allowed zone values:

- `maximized`
- `left`
- `right`
- `top-left`
- `top-right`
- `bottom-left`
- `bottom-right`
- `center`

### 8.2 Positioning contract
V1 layout positioning is best-effort and zone-based.

Expected behavior:

- if a window can be opened and moved, place it in the configured zone
- if zone placement fails, keep the window open and record partial failure
- layout failure must not fail the entire project launch

### 8.3 Desktop targeting contract
If desktop switching is supported by the runtime:

- the launcher should attempt to move focus to the preferred desktop
- then launch or move windows there

If desktop targeting fails:

- the app should still launch the configured items
- the result must indicate partial success

## 9. Restore Rules

### 9.1 Restore statuses
Restore plan items must use these statuses:

- `matched`
- `restorable`
- `pending_manual`
- `unknown`

Definitions:

- `matched`: an equivalent current window already exists
- `restorable`: enough launch information exists to attempt reopen
- `pending_manual`: user-visible item, but not enough structured launch data exists
- `unknown`: inconsistent or insufficient data

### 9.2 Restore priority
Restore should prioritize:

1. title and note display
2. project anchors
3. VS Code windows
4. terminal windows
5. auxiliary app windows
6. everything else

### 9.3 Restore honesty
The product must never imply that a snapshot restore is complete if it is partial.

The UI must explicitly show:

- what was matched
- what was reopened
- what requires manual recovery

## 10. UI Contracts

### 10.1 Live
Minimum V1 controls:

- `Refresh`
- `Save Snapshot`
- `Save Desktop Snapshot`

Minimum V1 outputs:

- current desktops and windows
- jump actions
- quick access to recent snapshots

### 10.2 Projects
Minimum V1 features:

- list projects
- create project
- edit project
- delete project
- edit terminal profiles
- edit app profiles
- launch project

### 10.3 Snapshots
Minimum V1 features:

- list snapshots
- filter by scope
- filter by desktop number
- filter by inferred project
- view detail
- edit title and note
- inspect restore plan
- trigger best-effort restore

## 11. API Contracts

### 11.1 Snapshots
- `POST /api/snapshots`
  - create full snapshot
  - body supports `title`, `note`
- `POST /api/snapshots/desktop/{desktop_id}`
  - create desktop snapshot
  - body supports `title`, `note`
- `GET /api/snapshots`
  - filters: `scope`, `desktop_number`, `project_id`, `limit`
- `GET /api/snapshots/{snapshot_id}`
- `PATCH /api/snapshots/{snapshot_id}`
  - supports `title`, `note`, `is_pinned`
- `POST /api/snapshots/{snapshot_id}/restore-plan`
- `POST /api/snapshots/{snapshot_id}/restore`

### 11.2 Projects
- `GET /api/projects`
- `POST /api/projects`
- `GET /api/projects/{project_id}`
- `PATCH /api/projects/{project_id}`
- `DELETE /api/projects/{project_id}`
- `POST /api/projects/{project_id}/launch`

### 11.3 Project terminals
- `POST /api/projects/{project_id}/terminals`
- `PATCH /api/project-terminals/{profile_id}`
- `DELETE /api/project-terminals/{profile_id}`

### 11.4 Project apps
- `POST /api/projects/{project_id}/apps`
- `PATCH /api/project-apps/{profile_id}`
- `DELETE /api/project-apps/{profile_id}`

## 12. Acceptance Criteria by Capability

### 12.1 Snapshots
- user can save a full snapshot from `Live`
- user can save a desktop snapshot from `Live`
- user can provide title and note
- saved snapshots are visible in `Snapshots`
- desktop-scoped snapshots contain only one desktop
- snapshot detail clearly displays title, note, desktops, windows, and terminals

### 12.2 Projects
- user can create a project with root path and manual name
- user can add at least one VS Code app profile
- user can add multiple terminal profiles
- user can launch the project from UI
- project launch continues even if one item fails

### 12.3 Layout and restore
- launched project items are assigned approximate zones when possible
- restore plan uses only `matched`, `restorable`, `pending_manual`, `unknown`
- restore UI shows partial outcomes honestly

## 13. Non-Functional Requirements

- snapshot creation must be fast enough to feel low-friction
- project launch must degrade gracefully
- inference must prefer false-negative over false-positive when creating project rows
- UI language must preserve the distinction between launch and restore
