# Implementation Plan: Projects and Snapshot Memory

## 1. Delivery Strategy
This track should be implemented in narrow, reviewable phases.

The implementation order is locked:

1. strengthen snapshot model and UX
2. add `Snapshots` panel
3. formalize `Projects`
4. add `Projects` panel
5. implement project launch
6. add approximate positioning and restore improvements

Do not start with layout or deep restore before the data model and UI surfaces are stable.

## 2. Phase 1: Snapshot Model Hardening

### Goal
Make snapshots first-class memory artifacts instead of raw persistence rows.

### Tasks
- [ ] Add snapshot fields:
  - `scope`
  - `title`
  - `note`
  - `captured_desktop_guid`
  - `captured_desktop_number`
  - `is_pinned`
- [ ] Add migration path for existing SQLite databases
- [ ] Update snapshot capture service to support:
  - explicit full snapshot creation
  - explicit desktop snapshot creation
- [ ] Ensure desktop snapshot persistence stores only:
  - one desktop row
  - windows on that desktop
  - terminals related to those windows
- [ ] Persist observed window rectangles into `snapshot_windows.window_rect_json`
- [ ] Tighten project inference:
  - prefer local paths
  - prefer terminal cwd
  - stop creating projects from browser titles alone

### Acceptance Criteria
- [ ] full snapshots persist with `scope = full`
- [ ] desktop snapshots persist with `scope = desktop`
- [ ] title and note persist correctly
- [ ] desktop snapshots include only one desktop
- [ ] project inference no longer creates rows from generic GitHub page titles

## 3. Phase 2: Snapshots Panel

### Goal
Turn snapshot history into a visible, usable memory surface.

### Tasks
- [ ] Add top-level `Snapshots` panel
- [ ] Add snapshots list with:
  - title
  - note preview
  - timestamp
  - scope
  - desktop/project summary
- [ ] Add filters:
  - scope
  - desktop number
  - project
  - recent limit
- [ ] Add snapshot detail view
- [ ] Add snapshot editing:
  - patch title
  - patch note
  - toggle pinned
- [ ] Add restore-plan view using statuses:
  - `matched`
  - `restorable`
  - `pending_manual`
  - `unknown`
- [ ] Add `Save Snapshot` and `Save Desktop Snapshot` controls in `Live`

### Acceptance Criteria
- [ ] user can browse snapshot history without leaving the app
- [ ] user can inspect the note before drilling into details
- [ ] user can save a desktop snapshot directly from `Live`
- [ ] snapshot detail exposes restore-plan output clearly

## 4. Phase 3: Project Data Model

### Goal
Promote projects from weak inference artifacts to explicit launch profiles.

### Tasks
- [ ] Extend `projects` with:
  - `notes`
  - `preferred_desktop_number`
- [ ] Add `project_app_profiles`
- [ ] Formalize `project_terminal_profiles` as editable launch data
- [ ] Define allowed `app_type` values:
  - `vscode`
  - `explorer`
  - `browser`
  - `custom`
- [ ] Define allowed `preferred_zone` values:
  - `maximized`
  - `left`
  - `right`
  - `top-left`
  - `top-right`
  - `bottom-left`
  - `bottom-right`
  - `center`
- [ ] Add migration coverage and tests for new schema

### Acceptance Criteria
- [ ] a project can exist with manual name and root path only
- [ ] a project can have multiple terminal profiles
- [ ] a project can have at least one app profile
- [ ] schema stays backward compatible with existing snapshot rows

## 5. Phase 4: Projects Panel

### Goal
Expose projects as the deterministic, reusable setup surface.

### Tasks
- [ ] Add top-level `Projects` panel
- [ ] Add list view
- [ ] Add create/edit/delete project flows
- [ ] Add project detail editor
- [ ] Add terminal profile editor
- [ ] Add app profile editor
- [ ] Add launch button and launch status surface

### Acceptance Criteria
- [ ] user can create a project end-to-end from UI
- [ ] user can add multiple terminal profiles
- [ ] user can define a VS Code app profile
- [ ] user can define desktop and zone preferences

## 6. Phase 5: Launch Engine

### Goal
Make `Launch Project` reliable enough to be the primary setup path.

### Tasks
- [ ] Implement launch planning:
  - ordered list of project app launches
  - ordered list of terminal launches
- [ ] Implement VS Code launch from configured path
- [ ] Implement terminal launch with:
  - cwd
  - optional shell
  - optional command
- [ ] Implement auxiliary app launch for supported app types
- [ ] Return launch result per item:
  - `success`
  - `partial`
  - `failed`
- [ ] Keep running if one item fails

### Acceptance Criteria
- [ ] project launch opens configured VS Code target
- [ ] project launch opens configured terminals
- [ ] launch result is itemized and honest about failures

## 7. Phase 6: Approximate Layout and Desktop Targeting

### Goal
Make launched projects land in roughly the right place without over-engineering.

### Tasks
- [ ] Implement zone-to-rectangle mapping for current monitor work area
- [ ] Implement best-effort window placement for supported windows
- [ ] Implement preferred desktop switching when runtime support exists
- [ ] Record partial placement failures without aborting the launch
- [ ] Reuse the same status vocabulary in restore where possible

### Acceptance Criteria
- [ ] launched windows are placed into approximate zones when possible
- [ ] desktop targeting failures do not cancel launch
- [ ] UI reflects partial positioning outcomes

## 8. Phase 7: Restore and Re-entry

### Goal
Make snapshots useful for context re-entry even when restore is imperfect.

### Tasks
- [ ] Keep restore semantics separate from project launch semantics
- [ ] Improve restore-plan classification using:
  - project links
  - app profiles
  - terminal cwd
  - desktop context
- [ ] Add best-effort restore execution for:
  - VS Code anchors
  - terminal anchors
  - supported auxiliary app anchors
- [ ] Mark unresolved items as `pending_manual`
- [ ] Prioritize note/title visibility in the restore UI

### Acceptance Criteria
- [ ] restore plan reflects structured project/app data when available
- [ ] unresolved items are shown as manual recovery, not hidden
- [ ] snapshot note remains prominent during restore flow

## 9. API Checklist

### Snapshots
- [ ] `POST /api/snapshots`
- [ ] `POST /api/snapshots/desktop/{desktop_id}`
- [ ] `GET /api/snapshots`
- [ ] `GET /api/snapshots/{snapshot_id}`
- [ ] `PATCH /api/snapshots/{snapshot_id}`
- [ ] `POST /api/snapshots/{snapshot_id}/restore-plan`
- [ ] `POST /api/snapshots/{snapshot_id}/restore`

### Projects
- [ ] `GET /api/projects`
- [ ] `POST /api/projects`
- [ ] `GET /api/projects/{project_id}`
- [ ] `PATCH /api/projects/{project_id}`
- [ ] `DELETE /api/projects/{project_id}`
- [ ] `POST /api/projects/{project_id}/launch`

### Project terminals
- [ ] `POST /api/projects/{project_id}/terminals`
- [ ] `PATCH /api/project-terminals/{profile_id}`
- [ ] `DELETE /api/project-terminals/{profile_id}`

### Project apps
- [ ] `POST /api/projects/{project_id}/apps`
- [ ] `PATCH /api/project-apps/{profile_id}`
- [ ] `DELETE /api/project-apps/{profile_id}`

## 10. Testing Plan

### Schema and persistence
- [ ] migration tests for existing DBs
- [ ] snapshot schema tests
- [ ] project schema tests
- [ ] app/terminal profile persistence tests

### Snapshots
- [ ] full snapshot creation
- [ ] desktop snapshot creation
- [ ] title/note patching
- [ ] snapshot filtering
- [ ] snapshot detail retrieval

### Projects
- [ ] project CRUD
- [ ] terminal profile CRUD
- [ ] app profile CRUD

### Launch and restore
- [ ] launch-plan generation
- [ ] launch partial failure handling
- [ ] zone mapping logic
- [ ] restore-plan classification
- [ ] restore partial outcome handling

### Windows-specific integration
- [ ] keep runtime-sensitive tests isolated
- [ ] use unit coverage for classification and planning logic
- [ ] do not rely on Linux CI for exact Windows focus behavior

## 11. Definition of Done

This track is done when all of the following are true:

- [ ] the app exposes `Live`, `Projects`, and `Snapshots`
- [ ] snapshots support title, note, and `full` or `desktop` scope
- [ ] snapshot history and detail are visible in UI
- [ ] projects can be created and launched from UI
- [ ] a project can open VS Code and multiple terminals
- [ ] layout uses approximate zones
- [ ] restore is best-effort and visibly partial when needed
- [ ] project inference is conservative and no longer polluted by browser titles
