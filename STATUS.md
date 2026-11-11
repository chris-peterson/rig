# rig: Spec Coverage Status

Tracking status of the requirements declared in [`SPEC.md`](SPEC.md).
Maintained by `/sextant:spec-status`.

**Last audit:** 2026-11-10
**Spec version:** root SPEC.md (unversioned)
**Plugin version:** unreleased
**Coverage:** 56 Covered, 0 Partial, 0 Missing/Contradicts
**Evidence pointers:** file

## Status by category

| Prefix | Count | Status | Notes |
|--------|------:|--------|-------|
| RIG-01..11 | 11 | All Covered | `scripts/rig` (`load_config`, `resolve`), tests in `tests/test_rig.py`. RIG-04 is a per-launch `--settings` overlay of `enabledPlugins`, which outranks user and project settings (verified 2026-11-10) |
| SETUP-01..06 | 8 | All Covered | `scripts/rig` (`RigEdits`, `setup`, `launch`), tests in `tests/test_rig.py`; SETUP-01 and SETUP-05 drive the editor through a pty. Includes SETUP-04a..b. SETUP-04a reads the settings file as text, since the blank lines don't survive a JSON parse. `claude plugin disable` rewrites the file without them (verified 2026-11-10, Claude Code project scope), so the groups last only in a file edited by hand |
| EDITOR-01..12 | 12 | All Covered | `scripts/rig` (`RigEdits`, `editor_app`), tests in `tests/test_rig.py` drive it headless with Textual's pilot, keys and clicks |
| PIN-01..10 | 10 | All Covered | `scripts/rig`, tests in `tests/test_rig.py`. PIN-08 uses `--plugin-dir`: the checkout loads as `<name>@inline` and the installed copy doesn't load, including when the overlay disables it (verified 2026-11-10) |
| SANDBOX-01 | 1 | All Covered | `scripts/rig`, tests in `tests/test_rig.py`. The overlay carries ai-sdlc's strict sandbox block; a launch on a machine without the sandbox hasn't been tried |
| LAUNCH-01..04 | 4 | All Covered | `scripts/rig`, tests in `tests/test_rig.py`. A launch whose arguments carry `--settings` is refused, since a second `--settings` replaces the first (verified 2026-11-10) |
| SHELL-01..04 | 4 | All Covered | `scripts/rig`, `commands/install-rig.md`, `hooks/cli-freshness.sh`; tests run the install against a throwaway HOME |
| TAB-01..06 | 6 | All Covered | `scripts/rig` (`ZSH_COMPLETION`); tests check parity, zsh syntax, and the awk readers. Not yet exercised in a live shell |

## Audit history

### 2026-11-10: Rig editor (spec-status)

STATUS.md updated: +12 EDITOR IDs, RIG-10..11 added, SANDBOX-02 removed,
SETUP-02..05 reworded for the rig editor, all Covered. Coverage 56 of 56. A rig
extends one rig, every rig but the base rig extends one, and a rig's definition
no longer carries the sandbox.

### 2026-11-10: Retired RIG requirements removed, RIG renumbered

The retired RIG-06 and RIG-08 are gone from SPEC.md, and the RIG IDs after them
moved down: RIG-07 → RIG-06, RIG-09 → RIG-07, RIG-10 → RIG-08, RIG-11 →
RIG-09. Entries below this one use the old numbers. Coverage unchanged at 43 of
43.

### 2026-11-10: Coverage refresh (spec-status)

STATUS.md updated: 33 → 43 live IDs (RIG-06, RIG-08 retired; LAUNCH-03..04,
SHELL-01..04, TAB-01..06 added), 0 → 43 Covered with the first build of
`scripts/rig`.

### 2026-11-10: Suggested rigs at setup

SETUP-04a..b added, both Missing: setup suggests one rig per blank-line group
in the settings file's `enabledPlugins` block, or one per marketplace when the
block has no groups. Coverage 0 of 33.

### 2026-11-10: First-run setup

New SETUP category, SETUP-01..06 all Missing: an interactive launch with no
rig definitions asks which enabled plugins form the base rig, makes it the
default, then offers named rigs extending it until the rest of the enabled
plugins are covered. `rig setup` reruns it; a headless launch with no
definitions is refused. Coverage 0 of 31.

### 2026-11-10: Pins load with the rig that uses them

A pin stands in for its plugin's installed copy. PIN-01 now records a pin for
the plugin a checkout holds, rather than loading it into every launch, and
PIN-08..10 added, all Missing: a rig that includes a pinned plugin loads the
checkout, and a pin outside the rig is asked about, or left out when no one
can be asked. Coverage 0 of 25.

### 2026-11-10: Plugins a rig names but aren't installed

RIG-10 and RIG-11 added, both Missing: a rig naming an uninstalled plugin
offers the install and waits for confirmation, and refuses when no one can
confirm. Coverage 0 of 22.

### 2026-11-10: First requirements

RIG, PIN, SANDBOX, and LAUNCH requirements added via `/sextant:spec-req new`,
all Missing ahead of the initial build. The PIN requirements describe the
behavior of ai-sdlc's `claude-pins.py`, which the build ports.

### 2026-11-10: Spec bootstrapped

SPEC.md scaffolded with six empty categories via `/sextant:spec-req init`.
