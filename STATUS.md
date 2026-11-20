# rig: Spec Coverage Status

Tracking status of the requirements declared in [`SPEC.md`](SPEC.md).
Maintained by `/sextant:spec-status`.

**Last audit:** 2026-11-20
**Spec version:** root SPEC.md (unversioned)
**Plugin version:** unreleased
**Coverage:** 95 Covered, 0 Partial, 0 Missing/Contradicts
**Evidence pointers:** file

## Status by category

| Prefix | Count | Status | Notes |
|--------|------:|--------|-------|
| RIG-01..20 | 20 | All Covered | `scripts/rig` (`load_config`, `check_rules`, `default_rigs`, `path_matches`, `repo_files`, `rule_match`, `take_rigs`, `plan`, `overlay`, `stock_args`, `turn_off_user_plugins`, `cmd_list`, `graph_of`, `Graph`), tests in `tests/test_rig.py`. Rigs are flat: `base` loads in every launch, the named rigs add to it, and `full` is every plugin installed for the working directory. RIG-04 is a per-launch `--settings` overlay that names only the launch's plugins and pinned plugins' installed copies, since a `--settings` value outranks every settings file. RIG-12 edits `~/.claude/settings.json` as text to keep its blank-line groups. RIG-18..20 match rules against the resolved working directory and `$PWD`, and list a repo's files once per launch with `git ls-files --cached --others --exclude-standard`; the globs support `*`, `?`, and `**`, not bracket classes or GitLab's extglob braces. `/plugin enable` loading mid-session under the new overlay hasn't been tried |
| SETUP-01..06 | 8 | All Covered | `scripts/rig` (`RigEdits`, `setup`, `launch`), tests in `tests/test_rig.py`; SETUP-01 and SETUP-05 drive the editor through a pty. Includes SETUP-04a..b. SETUP-04a reads the settings file as text, since the blank lines don't survive a JSON parse. `claude plugin disable` rewrites the file without them (verified 2026-11-10, Claude Code project scope), so the groups last only in a file edited by hand |
| EDITOR-01..14 | 14 | All Covered | `scripts/rig` (`RigEdits`, `editor_app`, `use_theme`), tests in `tests/test_rig.py` drive it headless with Textual's pilot, keys and clicks. The rig list draws its bracket with box characters down the right of each row; both screens use revdiff's Dracula colors, copied into `DRACULA` |
| PIN-01..14 | 14 | All Covered | `scripts/rig`, `hooks/switch/model.ts`, tests in `tests/test_rig.py` and `tests/switch*.test.ts`. PIN-07 and PIN-09 offer pins in the picker, driven through a pty. PIN-12's 📌 comes from `plugin_cell` and `pin_lines`, one each for a plugin's name and a pin's line, and the graph pads it as two cells (`cells`). PIN-08 uses `--plugin-dir`: the checkout loads as `<name>@inline` and the installed copy doesn't load, including when the overlay disables it (verified 2026-11-10). PIN-11 (`auto_mode_server_off`) works around anthropics/claude-code#95982 |
| SANDBOX-01 | 1 | All Covered | `scripts/rig`, tests in `tests/test_rig.py`. The overlay carries ai-sdlc's strict sandbox block plus `autoAllowBashIfSandboxed`, which Claude Code 2.1.325 turned off by default; a launch on a machine without the sandbox hasn't been tried |
| LAUNCH-01..16 | 16 | All Covered | `scripts/rig` (`launch`, `claude_args`, `confirmation`, `select_app`, `run_claude`, `run_app`), tests in `tests/test_rig.py`; LAUNCH-05 and LAUNCH-07..13 drive the picker with Textual's pilot, keys and clicks, and through a pty. LAUNCH-05 opens the picker with a Textual notification as its notice, the cursor on the first pin to choose. The picker draws the same `Graph` pieces `rig list --graph` prints. LAUNCH-14 is `cmd_badge`, run by `hooks/beacon-badge.sh` at SessionStart; tests use a stand-in beacon, and a live badge hasn't been tried. LAUNCH-13's click is driven through the handler, since Textual's pilot can't click the bar on a bordered screen's inner edge. LAUNCH-06's Ctrl-C handling is untested. A launch whose arguments carry `--settings` is refused, since a second `--settings` replaces the first (verified 2026-11-10). LAUNCH-15's tests close the picker's pty with SIGHUP ignored and with no controlling terminal; the editor shares `run_app` but isn't driven through a hangup |
| SWITCH-01..05 | 5 | All Covered | The `/rig` mod (`hooks/switch.ts`, `hooks/switch/model.ts`, `hooks/switch/view.tsx`) over `scripts/rig` (`cmd_switch`, `switch_state`, `launch`, `claude_args`, `take_switch`); tests in `tests/test_rig.py` have a stand-in claude run `rig switch`, with rigs and with `--picks`, and check the relaunch, and `tests/switch.test.ts` drives the mod under `claude plugin test`. The command is `/rig`, not `/rig:switch`: a mod can't register a name with `:` (Claude Code 2.1.329). The mod's exit through `$.command.run` was tried live; the pane hasn't been driven interactively, and its focus-follow scroll is untested |
| SHELL-01..06 | 6 | All Covered | `scripts/rig` (`main`, `cmd_install_cli`), `commands/install-rig.md`, `hooks/cli-freshness.sh`; tests run the install against a throwaway HOME |
| TAB-01..06 | 6 | All Covered | `scripts/rig` (`ZSH_COMPLETION`); tests check parity, zsh syntax, and the awk readers, and run `_rig` in zsh with stand-ins for `compadd` and `_default` for TAB-03 and TAB-06. Live completion inside a real widget (`IPREFIX` after a comma) hasn't been tried |
| DOCTOR-01..05 | 5 | All Covered | `scripts/rig` (`cmd_doctor`, `shell_probe`), tests in `tests/test_rig.py` probe a new zsh in a throwaway HOME. On a live machine (2026-11-10) it caught a `~/.zcompdump` from before `_rig`, read by `compinit -C` |

## Audit history

### 2026-11-20: Bare rig picks, pins lists

STATUS.md updated: +1 ID (PIN-14 bare `pin`/`unpin` act on the checkout the
working directory is in, Covered); PIN-06 moves the listing to `rig pins`,
SHELL-05 makes bare `rig` open the `--select` picker at a terminal, and PIN-12
follows. PIN-07 marks a loading pin ❗ when the launch starts in or above its
checkout, with a warning and Skip for this launch in its pin dialog.
`claude plugin test` runs only with `hooks/hooks.json` generated by shipyard's
unreleased `hook-modules` branch, since shipyard v2 drops the mod's
`modules`. +1 ID: LAUNCH-16 refuses an option neither rig nor Claude Code
takes, and LAUNCH-03 now refuses a lone word that is neither's command.
Coverage 95 of 95.

### 2026-11-19 — Coverage refresh (spec-status)

STATUS.md updated: coverage unchanged (93 of 93); LAUNCH-05, RIG-08, PIN-07,
PIN-09, PIN-12, LAUNCH-15, and SWITCH-01..05 reworded for the picker replacing
the launch confirmation and the `/rig` mod replacing the switch skill.

### 2026-11-18: Default rigs by rule

STATUS.md updated: +3 IDs (RIG-18 rules make a rig a default where they match,
RIG-19 `path` as git's `gitdir/i:`, RIG-20 `exists` as GitLab CI's
`rules:exists`; all Covered); RIG-07, RIG-11, RIG-13, LAUNCH-02, and EDITOR-08
reworded for rules, still Covered, and the default rigs concept now takes in the
rigs whose rules match. Coverage 93 of 93.

### 2026-11-15: Hangup ends the full-screen apps

STATUS.md updated: +1 ID (LAUNCH-15, Covered). A picker whose terminal closed
with SIGHUP ignored kept running and spun a core. Coverage 90 of 90.

### 2026-11-12: Coverage refresh (spec-status)

STATUS.md updated: +12 IDs (PIN-12 📌 for pins; LAUNCH-07..13 the `--select`
picker, `full` going alone in it, `e` to the editor, single plugins picked or
taken out, `all N plugins`, and the 🚀; PIN-13 a pin's details and Unpin on a click;
RIG-15..17 the `none` preset; all Covered); RIG-11, RIG-14, TAB-03, and
TAB-06 reworded, still Covered. Coverage 88 of 88.

### 2026-11-11: Moving plugins between base and a rig (spec-status)

STATUS.md updated: +1 ID (EDITOR-13, Covered); EDITOR-01, EDITOR-04,
EDITOR-06, SHELL-05, and SETUP-04..04b reworded. Coverage 73 of 73. Then +1
ID (EDITOR-14, dismissing a draft, Covered); EDITOR-04, EDITOR-10, and
EDITOR-13 reworded. Coverage 74 of 74. Then +2 IDs (RIG-13 `rig list --json`,
RIG-14 `rig list --graph`, both Covered). Coverage 76 of 76.

### 2026-11-11: Rigs add to a base rig (spec-status)

STATUS.md updated: coverage unchanged at 72 of 72. RIG-02, RIG-03, RIG-05..07,
RIG-10..11, SETUP-03..04, EDITOR-01..02, EDITOR-04..07, EDITOR-10..12,
LAUNCH-02, LAUNCH-05, PIN-08..10, SWITCH-01..05, and TAB-03 reworded for rigs
that add to the base rig in place of extending one another, and for `full`.

### 2026-11-11: Launch leaves other plugins to the settings files (spec-status)

STATUS.md updated: +1 ID (RIG-12, Covered); RIG-04 reworded, still Covered.
Coverage 72 of 72.

### 2026-11-11: Switching rigs mid-session (spec-status)

STATUS.md updated: +6 IDs (SWITCH-01..05, LAUNCH-06), all Covered. Coverage
71 of 71.

### 2026-11-11: Coverage refresh (spec-status)

STATUS.md updated: +1 ID (LAUNCH-05, Covered); RIG-08, PIN-07, and PIN-09
reworded for the launch confirmation, still Covered. Coverage 65 of 65.

### 2026-11-10: Coverage refresh (spec-status)

STATUS.md updated: +8 IDs (SHELL-05..06, DOCTOR-01..05, PIN-11), all
Covered; SHELL-04 and RIG-06 reworded. Coverage 64 of 64.

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
