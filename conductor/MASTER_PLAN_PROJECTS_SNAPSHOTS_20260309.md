# Master Plan: Projects, Snapshots, and Live Context

## Executive Summary
Workspace Monitor is no longer just a live dashboard for open windows.

The product is now centered on three user capabilities:

1. `Live`
   - See and navigate the current state of desktops and windows.
   - Use the existing detail, radar, and matrix views as the operational surface.

2. `Projects`
   - Create manual, reusable launch profiles for real work.
   - A project should be able to relaunch a known setup: VS Code, terminals, optional apps, preferred desktop, and approximate window zones.

3. `Snapshots`
   - Capture cognitive checkpoints of real work in progress.
   - A snapshot is not a project template; it is a memory artifact that helps the user pause and later resume context with minimal mental load.

This product direction explicitly optimizes for:
- productivity
- reduced context switching cost
- resuming interrupted work
- ADHD-friendly externalization of working memory

## Core Product Thesis
The application should support two complementary workflows:

### A. Launch structured work
The user selects a `Project` and presses launch.

Expected result:
- VS Code opens on the correct root path
- one or more default terminals open
- optional project apps open
- windows are placed into approximate screen zones
- the project lands on its preferred desktop when possible

### B. Capture and resume exploratory work
The user saves a `Snapshot` of the current situation, optionally for one desktop only, with a human note.

Expected result:
- the context is not mentally lost
- the user can later browse, search, and restore or partially relaunch that context
- future AI/agent features can enrich the snapshot

## Product Model

### Primary Concept: Project
The main long-lived configurable unit.

Each project should eventually support:
- name
- root path
- GitHub repository metadata
- VS Code launch configuration
- default terminal profiles
- optional auxiliary apps
- preferred desktop
- preferred layout zones
- notes and metadata

### Secondary Concept: Snapshot
The historical memory artifact.

A snapshot should support:
- full system scope or single desktop scope
- note/comment
- optional title
- timestamp
- observed desktops/windows/terminals
- dominant project inference
- future AI summary and granular browser context

### Live View
The current operational UI remains valuable.

`Live` should stay as the place to:
- inspect current state
- jump between windows/desktops
- save snapshots
- later trigger project launch and restore actions

## Simplification Decisions
- `Workspace` is no longer a first-class product concept in the UI.
- `Project` becomes the main manual configuration concept.
- `Snapshot` becomes the main memory and resume concept.
- `Live` remains the current-state operational view.

If `workspace` remains in the database temporarily, it should be treated as internal legacy structure rather than surfaced product language.

## UX Navigation Direction
Top-level product surfaces should become:

- `Live`
- `Projects`
- `Snapshots`

### Live
- Existing detail/radar/matrix views
- Quick actions:
  - Save full snapshot
  - Save current desktop snapshot
  - Jump to window
  - Jump to desktop

### Projects
- list of manual project profiles
- project detail editor
- launch actions
- terminal and app definitions
- preferred desktop and layout zones

### Snapshots
- recent and pinned snapshots
- filters by date, project, desktop, type
- note/title editing
- restore / reopen / inspect actions

## Launch vs Restore
The system must treat these as different operations.

### Launch Project
- user-driven
- deterministic
- based on manual configuration
- primary reliability path

### Restore Snapshot
- recovery-oriented
- best-effort
- based on observed past state
- acceptable to be partial

This distinction should stay clear in both UI and architecture.

## Window Positioning Direction
Window restore does not need to be pixel-perfect in the first serious version.

Use approximate zones instead:
- `maximized`
- `left`
- `right`
- `top-left`
- `top-right`
- `bottom-left`
- `bottom-right`
- `center`

This is sufficient for early product value and reduces fragility across monitors and DPI setups.

## Snapshot Philosophy
Snapshots are primarily for reducing mental overload, not for templating.

Typical user flow:
- user is investigating or exploring something
- the context is valuable but not actionable now
- user saves a snapshot and writes a note
- user later revisits and reconstructs the context

Therefore snapshots should prioritize:
- notes
- memory
- inspection
- contextual re-entry

before perfect full automation.

## Recommended Build Order

### Phase 1
- solidify current snapshot persistence
- add snapshot notes and scope (`full` vs `desktop`)
- improve project inference quality
- add `Snapshots` panel

### Phase 2
- add `Projects` panel
- add manual project configuration
- add project terminal profiles
- add project launch orchestration

### Phase 3
- add approximate layout positioning
- add project desktop targeting
- add snapshot desktop-level restore and assisted relaunch

### Phase 4
- add richer browser/context capture
- add AI/agent enrichment over snapshots
- add granular resume support

## Success Criteria
The product is succeeding when:
- the user can intentionally launch work setups from `Projects`
- the user can intentionally save context checkpoints from `Live`
- the user can later browse and resume those checkpoints from `Snapshots`
- the user feels less cognitive load when switching or pausing work

## Recommended Execution Path
The best option is to keep both the master plan and the detailed track inside the repo.

Why:
- one source of truth
- easier to evolve with code
- Gemini or Codex Web can implement directly against the same spec
- avoids divergence between planning chat and implementation branch

Therefore:
- keep this master plan in `conductor/`
- create a detailed track in `conductor/tracks/`
- then feed that track into Gemini Conductor or Codex Web
