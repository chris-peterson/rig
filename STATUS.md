# rig: Spec Coverage Status

Tracking status of the requirements declared in [`SPEC.md`](SPEC.md).
Maintained by `/sextant:spec-status`.

**Last audit:** 2026-11-24
**Spec version:** root SPEC.md (unversioned)
**Plugin version:** unreleased
**Coverage:** 115 Covered, 0 Partial, 0 Missing/Contradicts
**Evidence pointers:** file

## Status by category

| Prefix | Count | Status | Notes |
|--------|------:|--------|-------|
| DEF-01..02 | 2 | All Covered | `scripts/rig` (`load_config`, `check_rules`, `rule_problem`), tests in `tests/test_rig.py` |
| COMPOSE-01..08 | 8 | All Covered | `scripts/rig` (`take_rigs`, `selection`, `plan`, `default_rigs`, `confirm_none`, `stock_args`), tests in `tests/test_rig.py`. Rigs are flat: `base` loads in every launch, the named rigs add to it, and `full` is every plugin installed for the working directory. COMPOSE-06 turns off every plugin Claude Code knows of in the overlay; a Grok Build launch enables none and loads no pins |
| RULE-01..03 | 3 | All Covered | `scripts/rig` (`default_rigs`, `rule_match`, `path_matches`, `glob_pattern`, `repo_files`), tests in `tests/test_rig.py`. Rules match the resolved working directory and `$PWD`, and list a repo's files once per launch with `git ls-files --cached --others --exclude-standard`; the globs support `*`, `?`, and `**`, not bracket classes or GitLab's extglob braces |
| INSTALL-01..02 | 2 | All Covered | `scripts/rig` (`install`, `claude_args`, `confirmation`), tests in `tests/test_rig.py`. Both tools install through `claude plugin install`, since Grok Build loads the plugins Claude Code installed |
| LIST-01..03 | 3 | All Covered | `scripts/rig` (`cmd_list`, `graph_of`, `Graph`), tests in `tests/test_rig.py` |
| SETUP-01..06 | 8 | All Covered | `scripts/rig` (`RigEdits`, `setup`, `launch`), tests in `tests/test_rig.py`; SETUP-01 and SETUP-05 drive the editor through a pty. Includes SETUP-04a..b. SETUP-04a reads the settings file as text, since the blank lines don't survive a JSON parse. `claude plugin disable` rewrites the file without them (verified 2026-11-10, Claude Code project scope), so the groups last only in a file edited by hand |
| EDITOR-01..17 | 17 | All Covered | `scripts/rig` (`RigEdits`, `editor_app`, `use_theme`, `text_editor`, `edit_text`, `rule_problem`, `file_stamp`), tests in `tests/test_rig.py` drive it headless with Textual's pilot, keys and clicks. The rig list draws its bracket with box characters down the right of each row; both screens use revdiff's Dracula colors, copied into `DRACULA`. EDITOR-15's tests run a stand-in `GIT_EDITOR` under the headless pilot, where Textual can't suspend, so handing a real terminal to the editor (`App.suspend`) hasn't been tried. EDITOR-16's link is an OSC 8 hyperlink (Rich's `link` style, which Textual writes out); the tests check the style, and a cmd+click in a real terminal, where Textual holds the mouse, hasn't been tried. EDITOR-17 polls the file's mtime once a second |
| PIN-01..18 | 17 | All Covered | `scripts/rig` (`plan`, `PinOffer`, `claude_args`, `describe_pins`, `resolve_name`, `inferred_roots`, `select_app`'s `pin_row`, `pin_at`, and `FolderBrowser`), `hooks/switch/model.ts` (`planOf`, `isSelected`), tests in `tests/test_rig.py` and `tests/switch*.test.ts`. PIN-07 and PIN-09 offer pins in the picker under `--select`, driven through a pty. PIN-12's 📌 comes from `plugin_cell` and `pin_lines`, one each for a plugin's name and a pin's line, and the graph pads it as two cells (`cells`). PIN-08 in Claude Code uses `--plugin-dir`: the checkout loads as `<name>@inline` and the installed copy doesn't load, including when the overlay disables it (verified 2026-11-10). PIN-15 counts a copy as installed when it's installed for the working directory (`installed_for`), the set `plan` already takes; a copy installed only for another project doesn't count. PIN-02 infers a host's clone folder from a pin only where the checkout's git toplevel ends in its `origin`'s repo path; `clones:` wins over an inferred folder. PIN-17's tests stand in for `resolve_name`, and PIN-18 drives the browser (Textual's `DirectoryTree`, rooted at the home folder, hidden folders left out) with keys and a click. PIN-11 is retired, moved to CLAUDE-03 |
| LAUNCH-01..17 | 15 | All Covered | `scripts/rig` (`launch`, `claude_args`, `confirmation`, `select_app`, `editor_app`, `run_claude`, `run_app`), tests in `tests/test_rig.py`; LAUNCH-05 and LAUNCH-07..13 drive the picker with Textual's pilot, keys and clicks, and through a pty. LAUNCH-05: a launch with arguments and no `--select` skips the picker (`claude_args`) unless a pin it would load is a live checkout (`PinOffer.live`), checked through a pty; a picker that opens with something to decide shows a Textual notification as its notice, the cursor on the first pin to choose. The picker draws the same `Graph` pieces `rig list --graph` prints. LAUNCH-14 is `cmd_badge`, run by `hooks/beacon-badge.sh` at SessionStart; tests use a stand-in beacon, and a live badge hasn't been tried. LAUNCH-13's click is driven through the handler, since Textual's pilot can't click the bar on a bordered screen's inner edge. LAUNCH-06's Ctrl-C handling is untested. A launch whose arguments carry `--settings` is refused, since a second `--settings` replaces the first (verified 2026-11-10). LAUNCH-15's tests close the picker's pty with SIGHUP ignored and with no controlling terminal; the editor shares `run_app` but isn't driven through a hangup. LAUNCH-04 and LAUNCH-16 are retired, moved to TOOL-03 and TOOL-04 |
| SWITCH-01..06 | 6 | All Covered | The `/rig` mod (`hooks/switch.ts`, `hooks/switch/model.ts`, `hooks/switch/view.tsx`) over `scripts/rig` (`cmd_switch`, `switch_state`, `launch`, `claude_args`, `take_switch`); tests in `tests/test_rig.py` have a stand-in claude run `rig switch`, with rigs and with `--picks`, and check the relaunch, and `tests/switch.test.ts` drives the mod under `claude plugin test`. The command is `/rig`, not `/rig:switch`: a mod can't register a name with `:` (Claude Code 2.1.329). The mod's exit through `$.command.run` was tried live; the pane hasn't been driven interactively, and its focus-follow scroll is untested. SWITCH-05's `h` `j` `k` `l` buttons are tested through `stepOf`; the `$.ui.focus` call that moves the ring isn't, since `claude plugin test` gives a test no stand-in for it. SWITCH-05's narrow layout follows the `Pane`'s `bodyColumns` (`acrossWidth`, `tiersOf`, `stagger`) and asks the dock for `columns`; the staggered rows are checked as text, not as drawn. SWITCH-06 is `carried_args`, which reads each option's value shape (`<value>`, `[value]`, `<values...>`) from `claude --help` (`claude_help`); checked against Claude Code 2.1.329's help, and a relaunch through a stand-in claude |
| TOOL-01..05 | 5 | All Covered | `scripts/rig` (`main` setting `AGENT`, `claude_help` and `refuse_unknown_options` reading the tool's `--help`, `exec_claude`, `install_claude_function`), tests in `tests/test_rig.py` (`Grok`, `Shell`, `Launch`). Help parsing takes options indented up to eight spaces, as `grok --help` lays them out |
| CLAUDE-01..04 | 4 | All Covered | `scripts/rig` (`overlay`, `project_off`, `turn_off_user_plugins`, `auto_mode_server_off`, `SANDBOX_SETTINGS`), tests in `tests/test_rig.py`. CLAUDE-01 is a per-launch `--settings` overlay that names only the launch's plugins and pinned plugins' installed copies, since a `--settings` value outranks every settings file; it leaves out a rig plugin a project settings file sets to `false` (`project_off`), skipping `~/.claude/settings.json` when the walk up from the working directory reaches the home folder. `/plugin enable` loading mid-session under the overlay hasn't been tried. CLAUDE-02 edits `~/.claude/settings.json` as text to keep its blank-line groups. CLAUDE-03 works around anthropics/claude-code#95982. CLAUDE-04's overlay carries ai-sdlc's strict sandbox block plus `autoAllowBashIfSandboxed`, which Claude Code 2.1.325 turned off by default; a launch on a machine without the sandbox hasn't been tried |
| GROK-01..09 | 9 | All Covered | `scripts/rig` (`run_grok`, `grok_slot`, `build_grok_home`, `grok_config`, `without_plugins_table`, `carry_back`, `grok_misses`, `rig_options`), tests in `tests/test_rig.py` (`Grok`) against a stand-in grok. Each launch's grok home is `~/.rig/grok/<n>`, the first slot no running launch holds by `flock` on `<n>.lock` (GROK-09), linking `~/.grok` (or `$GROK_HOME`) entry by entry; the `[plugins]` table is found as text (a header at the start of a line), and the result is checked with `tomllib`. Checked against grok 1.0.92 through `grok inspect` in a rig-built home (2026-11-24): plugins Claude Code installed load by name, pins load from their checkouts, and a plugin grok skips (ClaudeWatch) is named. An interactive grok session through rig, and grok's own writes into its home during one, haven't been tried |
| SHELL-01..06 | 4 | All Covered | `scripts/rig` (`main`, `cmd_install_cli`), `commands/install-rig.md`, `hooks/cli-freshness.sh`; tests run the install against a throwaway HOME. SHELL-04 and SHELL-06 are retired, moved to TOOL-05 and TOOL-02 |
| TAB-01..07 | 7 | All Covered | `scripts/rig` (`ZSH_COMPLETION`, `resumable_sessions`, `session_title`); tests check parity, zsh syntax, and the awk readers, and run `_rig` in zsh with stand-ins for `compadd` and `_default` for TAB-03 and TAB-06. Live completion inside a real widget (`IPREFIX` after a comma) hasn't been tried. TAB-07 reads Claude Code's transcripts under `~/.claude/projects/` (an internal layout: the folder slug, and the `custom-title` and `ai-title` lines), only their first and last 256 KB, and offers the 50 newest |
| DOCTOR-01..05 | 5 | All Covered | `scripts/rig` (`cmd_doctor`, `shell_probe`), tests in `tests/test_rig.py` probe a new zsh in a throwaway HOME. On a live machine (2026-11-10) it caught a `~/.zcompdump` from before `_rig`, read by `compinit -C` |

## Audit history

### 2026-11-24 — Coverage refresh (spec-status)

STATUS.md updated: coverage unchanged (115 of 115); LAUNCH-05 reworded (a launch that would load a pin whose checkout holds or sits under the working directory opens the picker first).

### 2026-11-24 — Coverage refresh (spec-status)

STATUS.md updated: +1 ID (GROK-09, a reused grok home path so grok's remembered grants for a pin's scripts keep applying; Covered). Coverage 115 of 115.

### 2026-11-24: Tools, and the RIG category decomposed

STATUS.md updated: Grok Build support adds TOOL-01..05, CLAUDE-01..04, and
GROK-01..08. RIG-01..20 retired as a category, moved to DEF, COMPOSE, RULE,
INSTALL, LIST, and CLAUDE by what each is about; SANDBOX-01 moved to CLAUDE-04;
PIN-11, LAUNCH-04, LAUNCH-16, SHELL-04, and SHELL-06 struck in place, moved to
CLAUDE-03 and TOOL-03, -04, -05, -02. All Covered; coverage 114 of 114.

### 2026-11-24: Rules on show in the rig editor

STATUS.md updated: +2 IDs (EDITOR-16 the rig editor shows the selected rig's
rules read-only under its plugins, over a link to `rigs.yml`; EDITOR-17 a
change to `rigs.yml` made outside the editor is taken up, or named when the
editor has unsaved changes; both Covered). Coverage 105 of 105.

### 2026-11-24 — Coverage refresh (spec-status)

STATUS.md updated: coverage unchanged (103 of 103); LAUNCH-05 reworded (a
launch with arguments skips the picker), LAUNCH-07 and SWITCH-05 move on hjkl
and launch or switch on `g`, LAUNCH-13's footer item and SWITCH-05's button read `Go`, LAUNCH-07's title is `rig select` over the command line, EDITOR-03 adds `j`/`k`, RIG-08, PIN-07, and PIN-09
reworded for the picker opening only on `rig` alone or `--select`; all Covered.

### 2026-11-23: Pin any plugin

STATUS.md updated: +3 IDs (PIN-16 an unresolved `rig pin <name>` names the
path form, PIN-17 `p` in the picker pins a row, PIN-18 the picker's folder
browser; all Covered); PIN-02 and TAB-04 widened to clone folders inferred from
existing pins, still Covered (#2). Coverage 103 of 103.

### 2026-11-23: A plugin under development stays loaded

STATUS.md updated: +2 IDs (PIN-15 a pin with no installed copy loads without
asking, SWITCH-06 a switch's relaunch keeps the options passed through; both
Covered); PIN-09, PIN-10, and LAUNCH-05 narrowed to pins with an installed
copy, still Covered (#3). SWITCH-02 reworded: the relaunch adds no turn,
and the `/rig` mod toasts what the session switched to (`RIG_SWITCHED`); the
toast at a live session start hasn't been seen yet. Coverage 100 of 100.

### 2026-11-21: A project's plugin opt-out holds

RIG-04 reworded: a rig plugin a project settings file sets to `false` stays
out of the overlay, named on the launch summary, unless picked on its own; a
user-level `false` doesn't count (#1). Still Covered. Coverage 98 of 98.

### 2026-11-21: Rules from the rig editor, escape closes messages

STATUS.md updated: +2 IDs (EDITOR-15 `r` edits a rig's rules in git's
editor, LAUNCH-17 escape takes a message away in the picker and the editor;
both Covered); EDITOR-08 reworded for rules the editor can now change, still
Covered. Coverage 97 of 97. Then +1 ID (TAB-07, `--resume` offers the
folder's sessions, Covered). Coverage 98 of 98.

### 2026-11-20: A narrow switch pane

SWITCH-05 reworded: the pane names plugins without their marketplace,
staggers the rig names over rows when the pane is too narrow for one, asks the
dock for only the width two such rows take, and ends the pin toast in ✕. `l`
with nothing changed now closes the pane and keeps the session: it used to exit
Claude Code with no switch recorded, so rig ended instead of relaunching.
The pane colors what a switch brings in green and what it takes out red
(`changesOf`), and lists those plugins under the summary. Still Covered.
Coverage 95 of 95.

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
