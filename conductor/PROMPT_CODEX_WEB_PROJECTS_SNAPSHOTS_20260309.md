# Prompt: Codex Web Implementation for Projects and Snapshot Memory

You are working on the repository `WorkspaceMonitor` on Windows-focused product code.

Your job is to implement the track defined in these files. Read them first and treat them as the source of truth:

- `conductor/MASTER_PLAN_PROJECTS_SNAPSHOTS_20260309.md`
- `conductor/tracks/projects_and_snapshot_memory_20260309/spec.md`
- `conductor/tracks/projects_and_snapshot_memory_20260309/plan.md`
- `conductor/tech-stack.md`
- `conductor/workflow.md`

## Product direction already decided

The product is now organized around three user-facing surfaces:

- `Live`
- `Projects`
- `Snapshots`

Core decisions that are already locked:

- `Project` is the main manual reusable launch profile.
- `Snapshot` is a memory/checkpoint artifact, not a reusable template.
- `Workspace` is not a first-class visible concept in this track.
- `Launch Project` and `Restore Snapshot` are distinct flows and must remain distinct in UI and architecture.
- Window placement is approximate by zone, not pixel-perfect.
- Snapshot scope must support:
  - `full`
  - `desktop`

## What to implement

Implement this track in the order defined in:

- `conductor/tracks/projects_and_snapshot_memory_20260309/plan.md`

Do not skip ahead into deep restore or browser automation before the data model and UI surfaces are in place.

## Mandatory implementation order

1. Upgrade the snapshot model.
2. Add the `Snapshots` panel.
3. Formalize the `Projects` data model.
4. Add the `Projects` panel.
5. Implement project launch.
6. Implement approximate layout positioning and desktop targeting.
7. Improve restore-plan and best-effort restore.

## Required behavior

### Snapshots
- Support title and note.
- Support `scope = full` and `scope = desktop`.
- Support saving from `Live`.
- Support browsing, filtering, inspecting, and editing snapshots.
- Support restore-plan statuses:
  - `matched`
  - `restorable`
  - `pending_manual`
  - `unknown`

### Projects
- Manual CRUD from UI and API.
- Root path is the main identity in V1.
- Support multiple terminal profiles.
- Support app profiles with at least:
  - `vscode`
  - `explorer`
  - `browser`
  - `custom`
- Support preferred desktop and preferred zone.

### Launch
- Launch VS Code on configured root path.
- Launch configured terminals with cwd and optional command.
- Launch optional auxiliary apps.
- Attempt best-effort desktop targeting and zone placement.
- Return per-item results and continue on partial failure.

## Constraints

- Do not reintroduce `Workspace` as a major user-facing concept.
- Do not implement pixel-perfect positioning.
- Do not implement exact browser tab restore in this track.
- Do not add AI or GitHub automation beyond data fields already specified.
- Prefer conservative project inference over noisy false positives.
- Do not create project rows from browser page titles alone.

## Technical expectations

- Use SQLite migrations or safe schema evolution for the existing database.
- Keep snapshot persistence backward compatible where feasible.
- Preserve the existing `Live` dashboard value.
- Add focused tests for schema, API, planning logic, and persistence.
- Isolate Windows-sensitive runtime behavior from generic unit tests.

## Deliverables

At the end of the implementation, leave:

- working code
- updated tests
- updated persistence and API layers
- UI for `Projects` and `Snapshots`
- launch and restore-plan behavior aligned with the spec

## Reporting expectations

When you finish, explain:

- what you implemented
- which files changed
- what tests pass
- which parts are partial or best-effort
- what risks remain, especially around Windows desktop/focus behavior
