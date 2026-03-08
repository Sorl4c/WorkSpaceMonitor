# Specification: Persistent Workspace Snapshots and Context Resume

## Overview
The product is evolving from a live workspace dashboard into a persistent workspace state manager.

The next milestone is to make the application useful across interruptions, shutdowns, reboots, and next-day resumptions. The system should capture full workspace snapshots, persist them locally in SQLite, and provide the foundations for restoring work contexts later.

This track intentionally changes the center of gravity of the product:

- From real-time SSE-first monitoring
- To snapshot refresh + durable persistence + resume-oriented workflows

## Product Reframe

### Previous center
- Observe current desktops and windows
- Visualize structure
- Jump between existing windows

### New center
- Persist the current work state
- Recover the state after interruptions
- Reconstruct mental context with minimal effort
- Prepare the local knowledge base for future agent and AI workflows

## Product Goal
Reduce the cognitive cost of resuming work after disruption by turning the current workspace into a persistent, queryable, restorable model.

## Core User Problems
- After a reboot or crash, the user loses the structure of their desktops.
- The user does not remember which desktop belonged to which project.
- The user cannot easily reconstruct editor, terminal, and browser anchors for each project.
- The user wants the system to become a durable base for future repository-aware and agent-driven actions.

## Primary User Outcomes
- Save the complete workspace state manually.
- Save the complete workspace state automatically on an interval.
- See recent snapshots and identify the most recent valid restore point.
- Re-enter work with a restore flow that prioritizes project anchors and desktop placement.
- Preserve enough context to manually recover any item that cannot be restored automatically.

## Domain Model

### Workspace
A persistent user-defined logical work container. A workspace may represent a project, a cluster of related projects, or a recurring operating mode.

Expected properties:
- stable id
- display name
- optional description
- optional dominant project
- preferred desktop mapping
- restore preferences
- timestamps

### Project
A semantic unit derived initially from root folder and optionally enriched later with manual GitHub/repository linkage.

Expected properties:
- stable id
- root path
- inferred name
- manual name override
- optional repository url
- optional provider metadata
- timestamps

### Snapshot
A historical capture of the full observed workspace state at a point in time.

Expected properties:
- stable id
- capture mode (`manual`, `auto`)
- capture timestamp
- app version
- OS session metadata when available
- validity status
- restore status
- summary statistics

### Desktop Snapshot
Observed state for one Windows virtual desktop within a snapshot.

Expected properties:
- desktop identity as observed
- ordinal number
- display name
- dominant project/workspace inference
- counts by category
- ordering within snapshot

### Window Instance
An ephemeral observed window inside a snapshot.

Expected properties:
- hwnd at capture time
- title
- clean title
- process id at capture time
- process name
- desktop association
- semantic category
- inferred project/workspace
- browser tab count when available
- cwd or other recoverable launch context when available
- restorable capability flags

### Restore Task
A tracked attempt to restore one snapshot, desktop, or window anchor.

Expected properties:
- target snapshot
- restore strategy
- task status
- per-item success/failure
- pending manual actions
- diagnostic messages

## Functional Requirements

### 1. Snapshot Capture
- The system must support manual snapshot capture from the dashboard.
- The system must support automatic snapshot capture on a configurable interval.
- A snapshot in this phase should capture the full workspace, not only "relevant" windows.
- The capture operation should persist all desktops, windows, and terminal-derived context available at that moment.

### 2. Snapshot Persistence
- All snapshot data must be stored locally in SQLite.
- The schema must support historical snapshots, not only the latest state.
- The schema must support future enrichment with AI/context metadata without major redesign.
- The application must survive restart and still display the previously stored snapshots.

### 3. Workspace and Project Modeling
- The system must introduce explicit persistent `Workspace` and `Project` entities.
- Initial project inference may be based primarily on root folder or cwd.
- Manual repository association should be possible later; schema support should exist now.
- A desktop may be associated with a dominant project or workspace.

### 4. Resume and Restore
- The system must provide a resume-oriented UI surface showing available snapshots.
- The first restore mode should be progressive:
  - identify current matches that already exist
  - navigate to existing windows when possible
  - reopen applications and folders when possible
  - preserve unresolved items as pending manual actions
- The desired direction is restore plus desktop positioning, even if the first version only partially achieves it.

### 5. Recovery from Shutdown/Reboot
- The user must be able to open the app the next day and see the last stored snapshot.
- The user must be able to attempt a restore from that snapshot.
- When exact restoration is not possible, the UI must still help the user reconstruct the previous state.

### 6. Diagnostics and Reliability
- The system must keep enough diagnostic data to understand restore failures.
- The app must not silently lose snapshots.
- The app must record snapshot capture errors and restore errors.

## Restore Strategy

### V1 Restore Scope
The user preference is ambitious:
- reopen applications
- reposition them by desktop

This should be treated as the product target, but implemented progressively.

### V1a: Assisted Resume
- show previous desktops and anchors
- detect which anchors already exist
- allow one-click navigation
- list missing windows as pending
- provide manual reopen actions where possible

### V1b: Partial Automatic Restore
- reopen VS Code for saved project roots
- reopen terminals with best-effort cwd
- reopen browser/app anchors when launch targets are known
- move or reopen items into intended desktops where technically possible

### V1c: Full Restore Direction
- recreate a full desktop layout with restored applications
- reconcile restored windows back into intended workspaces

## Snapshot Definition
For this phase, a "useful snapshot" means full desktop capture.

That includes:
- all virtual desktops detected
- all visible windows detected
- semantic categorization
- terminal context when available
- project/workspace inference
- browser metadata already supported

The system should not attempt to decide relevance yet.

## Persistence and History Policy
History depth is not yet decided at product level.

Therefore V1 should support:
- retaining multiple snapshots
- marking one snapshot as the latest successful snapshot
- pruning policy configurable later

The schema should not assume "single latest snapshot only".

## Terminal Persistence Direction
Terminal persistence details are not yet fully defined by product.

The first schema and capture layer should therefore store whatever is already reliably obtainable:
- process name
- cwd when available
- active worker name
- active worker cwd
- command line when available

Avoid over-designing terminal semantics in this phase.

## VS Code Restore Priorities
Current priorities:
- reopen folder/project
- remember associated desktop

Remembering exact active files/tabs is desirable but not required for this phase unless it becomes technically cheap.

## UX Requirements
- The dashboard must expose `Save Snapshot` clearly.
- The dashboard must expose recent snapshots and a resume entry point.
- Restore UI must distinguish:
  - restorable automatically
  - matched to existing windows
  - pending manual action
  - failed
- The system must preserve the product tone: restrained, dense, and low-noise.

## Integration Bug to Track
There is an existing Windows integration issue:

- when jumping to a window on another desktop, the app sometimes switches correctly but leaves a strange flashing state in the Windows taskbar
- this likely relates to the timing and sequence of desktop switch and foreground focus APIs

This bug is not the core objective of this track, but it must be explicitly tracked as a restore/navigation risk because it can degrade confidence in resume behavior.

## Non-Functional Requirements
- SQLite operations must be reliable and crash-safe for local usage.
- Snapshot capture should remain fast enough for background use.
- Automatic capture must not create noticeable UI lag.
- Restore attempts must produce structured logs.
- The app must continue to degrade gracefully when OS APIs fail.

## Out of Scope for This Track
- Full AI decision-making over the snapshot database
- GitHub automation workflows
- PR/issue automation
- Agent orchestration over repositories
- Perfect recreation of every browser tab
- Pixel-perfect restoration of all window positions across monitors

## Future Value Enabled by This Track
This track is foundational for later features such as:
- project-aware agents
- repository-linked workspace actions
- restore recommendations
- drift detection
- context summarization
- automated next-step suggestions

## Acceptance Criteria
- The app uses snapshot refresh as the primary runtime update model for the dashboard.
- The app can capture and persist a full workspace snapshot in SQLite.
- The app can capture snapshots both manually and on a timer.
- The app exposes stored snapshots after restart.
- The app introduces persistent `Workspace`, `Project`, `Snapshot`, and observed window entities in the data model.
- The app provides a visible resume flow from a previous snapshot.
- The resume flow can at minimum identify matched existing windows and unresolved items.
- The system records restore diagnostics for failed or partial restores.
