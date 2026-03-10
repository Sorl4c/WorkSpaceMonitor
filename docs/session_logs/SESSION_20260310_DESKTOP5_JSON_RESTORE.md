# Session Log - 2026-03-10

## Goal

Validate a fast-iteration workflow for single-desktop snapshots using JSON instead of history-heavy SQLite snapshots, with a real end-to-end test on desktop 5.

The product decision for this session was:

- keep `Live` as the main operating surface
- deprioritize `Studio`
- focus on one real workflow:
  - capture one desktop
  - close it
  - restore it
  - understand what fails

## Scope Worked

Primary focus:

- desktop-scoped JSON snapshot capture
- backend-only restore validation first
- terminal context detection improvements
- real restore testing on Windows desktop 5
- handling the case where VS Code is already open on another desktop

Out of focus:

- `Studio` UI iteration
- pixel-perfect positioning
- snapshot history
- browser tab/session restore

## Files Involved

Main code paths used during the session:

- `src/json_snapshot_service.py`
- `src/main.py`
- `src/window.py`
- `src/project_inference.py`
- `static/index.html`
- `static/js/store/wm-store.js`
- `tests/test_json_snapshot_service.py`

Temporary runtime artifacts created for validation:

- `.runtime_check/desktop5_restore_result.json`
- `.runtime_check/desktop5_real_restore_result.json`
- `.runtime_check/desktop5_real_restore_result_2.json`

These `.runtime_check` files are diagnostic outputs only and are not part of the product surface.

## What Changed

### 1. Real desktop JSON restore became the primary validation loop

We stopped optimizing around the `Studio` surface and switched to a simpler loop:

- save current desktop to JSON
- close the windows
- run restore
- inspect the actual Windows result

This reduced ambiguity and made progress measurable.

### 2. Terminal context heuristics were hardened for real Windows behavior

Problem discovered:

- `WindowsTerminal.exe` often exposed a shared PID context
- `terminal_cwd` frequently fell back to `C:\\Windows\\System32`
- generic titles like `Windows PowerShell` and `cmd.exe` were not useful enough on their own

What was implemented:

- if a desktop contains exactly one plausible local project root, use it as fallback context
- apply that fallback to:
  - generic Windows Terminal windows
  - VS Code `Welcome` windows with no reliable inferred root
- prefer non-system paths from terminal worker cwd before accepting terminal cwd
- ignore obvious system paths such as `C:\\Windows\\...` as project roots

Result:

- desktop 5 now resolves `C:\\local\\AppsPython\\WorkspaceMonitor` as the dominant local context
- both terminal windows and the VS Code welcome window inherit that project root when direct detection is weak

### 3. Restore no longer suppresses useful terminal relaunches

Problem discovered:

- restore deduplication was too aggressive
- two visible terminal windows on the same desktop could collapse into one restore action

What was changed:

- window-based terminal restore actions are allowed even if they share the same cwd
- only the extra terminal aggregate item is suppressed when it would duplicate a real window restore

Result:

- two visible terminal windows can now reopen
- the plan no longer shows a misleading extra `pending_manual` terminal item

### 4. Explorer restore was verified in the same real cycle

Explorer path capture and relaunch had already been introduced, but this session validated it inside the real desktop 5 workflow.

Confirmed behavior:

- Explorer path was captured
- Explorer window was closed
- Explorer window was restored successfully on desktop 5

### 5. VS Code launch was made more realistic on Windows

Problem discovered:

- `code` was not always resolvable through `subprocess.Popen(["code", ...])`

What was changed:

- the restore path now tries:
  - `code`
  - `code.cmd`
  - `%LOCALAPPDATA%\\Programs\\Microsoft VS Code\\Code.exe`
  - `%LOCALAPPDATA%\\Programs\\Cursor\\Cursor.exe`

This removed a false-negative launch failure from the backend.

### 6. VS Code already-open-on-another-desktop is now treated explicitly

Problem discovered:

- `WorkspaceMonitor`'s VS Code instance was already open on another desktop
- backend launch could succeed while not producing a new visible editor on desktop 5
- this should not be reported as a normal restore failure

What was changed:

- restore plan now includes `already_open_elsewhere`
- for editor windows, the planner checks:
  - inferred project root on other desktops
  - editor titles on other desktops for the project name

Result:

- the `Welcome - Visual Studio Code` snapshot item for desktop 5 is now classified as:
  - `status: already_open_elsewhere`
  - `action: focus_existing_editor`

This is a more honest model of the real situation.

## Real Test Performed

### Desktop 5 live case

The real desktop 5 setup under test included:

- one Explorer window for `WorkspaceMonitor`
- two visible Windows Terminal windows
- one VS Code window

Workflow executed:

1. capture desktop 5 JSON snapshot
2. close the desktop 5 windows
3. inspect restore plan
4. execute restore
5. inspect restored windows on desktop 5

Observed successful restore behavior:

- Explorer reopened
- two terminal windows reopened visibly

Observed special-case behavior:

- VS Code was recognized as already open elsewhere and therefore should not be interpreted as a missing restore

## Current Restore Plan Semantics for Desktop 5

After the session changes, the plan is clean:

- `restorable: 3`
- `already_open_elsewhere: 1`
- `pending_manual: 0`

Meaning:

- Explorer is restorable
- both terminal windows are restorable
- VS Code is already available elsewhere
- no fake residual terminal item remains in the plan

## Product Meaning

This session materially improved the product direction.

Before:

- restore existed, but terminal context was too unreliable
- the plan included noisy terminal artifacts
- VS Code behavior was ambiguous

After:

- single-desktop JSON memory is now a real iteration loop
- desktop restore works well enough to guide the next sprint
- the system is moving toward:
  - `capture context`
  - `resume context`
  - honest partial restore reporting

## Technical Debt Noted

`src/json_snapshot_service.py` now mixes several responsibilities:

- snapshot capture
- local inference heuristics
- restore planning
- launching apps

That was acceptable for fast iteration in this session, but it should be split soon.

Likely extraction target:

- `src/json_snapshot_inference.py`

Candidate responsibilities to move:

- terminal cwd normalization
- desktop local root fallback logic
- already-open-elsewhere detection

## Verification

Automated:

- `tests/test_json_snapshot_service.py`
- result: `3 passed`

Manual / real Windows validation:

- desktop 5 capture
- desktop 5 close
- desktop 5 restore
- inspection of actual restored windows

## Recommended Next Step

Next useful step:

1. extract restore inference heuristics out of `json_snapshot_service.py`
2. keep iterating on desktop JSON restore before investing more in `Studio`
3. later, add focus/jump behavior for the `already_open_elsewhere` editor case
