# rig specification

rig launches Claude Code, or Grok Build, with a chosen set of plugins (a rig),
loads pinned local plugin checkouts into every launch, and can run a Claude
Code session inside Claude Code's sandbox.

Requirements use [EARS syntax](https://alistairmavin.com/ears). Each is one of:
Ubiquitous (`The <system> shall …`), State-Driven (`While …`), Event-Driven
(`When …`), Optional (`Where …`), or Unwanted Behaviour (`If … then …`).

Each requirement is its own heading carrying a stable ID (`XX-NN`), one level
below its category's heading, so every requirement has a linkable anchor
(`SPEC.md#xx-nn`). Lettered decompositions (`XX-NNa`) each count as one.

## Concepts

- **rig**: a named set of plugins chosen for a kind of work. A launch loads the
  base rig and any number of other rigs on top of it.
- **base rig**: the rig named `base`, which every launch loads. First-run setup
  creates it from the plugins you want in every session.
- **full**: a rig that rig provides, holding every installed plugin.
- **none**: a preset that rig provides, launching the tool as it ships, with no
  plugins at all.
- **default rigs**: the rigs a launch adds to the base rig when it names none:
  the rigs listed as defaults, and the rigs whose rules match the working
  directory.
- **rule**: a condition on a rig, on the working directory's path or the files
  in its repository, under which the rig is a default rig.
- **pin**: a local plugin checkout that stands in for the plugin's installed
  copy, so changes to the checkout can be used for a stretch of real work
  before a marketplace release.
- **sandbox**: Claude Code's sandbox for Bash commands, which a launch can turn
  on.
- **launch**: one start of a tool through rig.
- **tool**: the coding agent a launch starts: Claude Code, or Grok Build when
  the launch is `rig grok`.
- **switch**: moving a session to other rigs, carrying its conversation over.

## Requirements

### `DEFINE`
Rig definitions

#### `DEFINE-01`
The system shall read rig definitions from a user-level file, each naming the
plugins it loads.

#### `DEFINE-02`
If the rig definitions give a rig anything but plugins and rules, give the base
rig rules, give a rule a condition other than `path` and `exists` or no
condition at all, define a rig named `full` or `none`, or define no rig named
`base`, then the system shall refuse the launch, saying which.

### `COMPOSE`
Which rigs a launch loads

#### `COMPOSE-01`
The system shall load the base rig's plugins in every launch, along with the
plugins of each rig the launch names.

#### `COMPOSE-02`
When a launch names several rigs, separated by spaces, commas, or both, the
system shall load the plugins of all of them.

#### `COMPOSE-03`
When the user runs `rig use <rig>...`, the system shall launch the tool with
the base rig and the named rigs.

#### `COMPOSE-04`
When a launch names no rig, the system shall launch the tool with the base
rig and the default rigs.

#### `COMPOSE-05`
The system shall provide a rig named `full` that loads every installed plugin.

#### `COMPOSE-06`
When a launch names `none`, the system shall start the tool with every
plugin it knows of turned off, the base rig's and pinned plugins' included.

#### `COMPOSE-07`
When a launch names `none`, the system shall say what the session goes without
and launch only once the user at the terminal confirms.

#### `COMPOSE-08`
If a launch names `none` along with other rigs, or no one is at a terminal to
confirm it, then the system shall refuse the launch.

### `RULE`
Folder rules

#### `RULE-01`
Where a rig has rules, the system shall make it a default rig in a working
directory where any of its rules matches, a rule matching when each of its
conditions does.

#### `RULE-02`
When a rule gives a `path`, the system shall match the working directory against
it as git's `includeIf "gitdir/i:"` matches its pattern: ignoring case, `~/`
standing for the home folder, a pattern that doesn't start with `/` or `~/`
matching at any depth, `**` spanning folders, and a trailing `/` matching the
folder and everything under it.

#### `RULE-03`
When a rule gives `exists`, the system shall match it when a file that matches
one of its globs, from the root of the working directory's git repository,
is tracked there or untracked and not ignored, as GitLab CI's `rules:exists`
matches; outside a repository, when one of the first 10,000 files under the
working directory matches.

### `INSTALL`
Rig plugins not yet installed

#### `INSTALL-01`
If a rig names a plugin that is not installed, then the system shall install
it once an interactive launch goes ahead; where the picker is open, it shall
mark the plugin there and refuse the launch if the user cancels.

#### `INSTALL-02`
If a rig names a plugin that is not installed and no one is at a terminal to
confirm, then the system shall refuse the launch, naming the plugin.

### `LIST`
Listing the rigs

#### `LIST-01`
When the user runs `rig list`, the system shall list each rig with its plugins,
marking the base rig and the default rigs, and naming the rule that makes a rig
a default in the working directory.

#### `LIST-02`
When the user runs `rig list --json`, the system shall print the rigs, their
plugins and rules, and the default rigs as JSON.

#### `LIST-03`
When the user runs `rig list --graph`, the system shall print a table of
plugins against rigs, marking each rig that loads each plugin, listing the
installed plugins no rig names after the rest, then any pinned plugin neither
lists.

### `SETUP`
First-run setup

#### `SETUP-01`
When an interactive launch finds no rig definitions, the system shall run
first-run setup before launching.

#### `SETUP-02`
When first-run setup opens the rig editor, the system shall start a base rig
with the plugins Claude Code's settings enable already selected.

#### `SETUP-03`
When the user saves first-run setup, the system shall write the base rig to the
rig definitions.

#### `SETUP-04`
While the rig editor is open, the system shall show a draft rig for each group
of installed plugins that no rig names, whether the settings turn them on or
off, saving a draft only once the user keeps it under a name.

#### `SETUP-04a`
Where the `enabledPlugins` block of the user's Claude Code settings file
separates its entries into groups with blank lines, the system shall make one
draft rig per group, counting entries that are on and off alike, and suggest a
name: the plugin's own for a group of one, else the start the plugins' names
share, else their marketplace, else the first plugin's name, unique among the
rigs and drafts.

#### `SETUP-04b`
Where the `enabledPlugins` block has no blank-line groups, or doesn't list an
installed plugin, the system shall put those plugins in one draft rig per
marketplace, named after the marketplace, or after the plugin when it holds
one.

#### `SETUP-05`
When the user runs `rig setup`, the system shall open the rig editor on the
existing rig definitions.

#### `SETUP-06`
If a launch finds no rig definitions and no one is at a terminal, then the
system shall refuse the launch, naming `rig setup`.

### `EDITOR`
Rig editor

#### `EDITOR-01`
The rig editor shall list the rigs in one pane, the base rig first, the other
rigs and drafts after it, and `full` last, joined by a bracket, marking the
base rig and `full` as built in, with the plugins of the selected rig in a
second pane.

#### `EDITOR-02`
The rig editor shall offer every installed plugin, and every plugin a rig
names, as a candidate for the selected rig, and show `full` with every
installed plugin locked.

#### `EDITOR-03`
The rig editor shall move through rigs and plugins with the arrow keys, `j`
and `k`, or the mouse, and toggle the highlighted plugin with space or a click.

#### `EDITOR-04`
The rig editor shall show every rig other than the base rig as the base rig's
plugins in a box of their own, then `+`, then the rig's own box, and when the
user toggles a plugin in the base rig's box, move it into the rig.

#### `EDITOR-05`
When the user creates a rig, the system shall ask for its name, refusing a
name another rig has.

#### `EDITOR-06`
When the user marks a rig as a default, the system shall add it to the rigs a
launch naming no rig uses, or take it out when it is one already, showing the
rigs such a launch loads.

#### `EDITOR-07`
If the user deletes or renames the base rig or `full`, then the system shall
refuse, saying why.

#### `EDITOR-08`
When the user saves, the system shall write the rigs to the rig definitions
file, the base rig first and the rest in alphabetical order, each with its
plugins in alphabetical order and its rules in the order they're written.

#### `EDITOR-09`
If the user quits the rig editor with unsaved changes, then the system shall
ask whether to save them, `q` saving and quitting, `d` discarding, and escape
going back to the editor.

#### `EDITOR-10`
When the user presses F2 on a rig or double-clicks it, or presses `s` on a
draft or double-clicks it, the system shall open it for naming.

#### `EDITOR-11`
When the user renames a rig, the system shall carry the new name to the
default rigs.

#### `EDITOR-12`
The rig editor shall list the rigs between the base rig and `full` in
alphabetical order, re-sorting them as rigs are created or renamed.

#### `EDITOR-13`
When the user presses `>` on a plugin with a rig other than the base rig
selected, the system shall put the plugin in that rig and take it off the base
rig, and when the user presses `<` on a plugin, put it on the base rig and take
it out of the selected rig.

#### `EDITOR-14`
When the user presses `x` on a draft, the system shall dismiss it, and stop
offering its plugins as a draft once the rigs are saved.

#### `EDITOR-15`
When the user presses `r` on a rig other than the base rig and `full`, the
system shall open the rig's rules as YAML in git's editor, or where git isn't
on PATH in `$VISUAL`, then `$EDITOR`, then `vi`, and once the editor closes,
take the rules it saved as an unsaved change and name them in the rig's box;
if they don't parse or aren't rules, keep the rules as they were, say why, and
open what the user wrote on the next `r`.

#### `EDITOR-16`
While a rig is selected, the rig editor shall show its rules, read-only, in a
third box under its plugins, as YAML in the form the rig definitions file
holds them, marked when they aren't saved yet, over the rig definitions file's
path as a terminal hyperlink to the file.

#### `EDITOR-17`
When the rig definitions file changes outside the rig editor, the system shall
take up the change if the editor has none unsaved, or else keep its own and
say that saving would write over the change.

### `PIN`
Local pins

#### `PIN-01`
When the user runs `rig pin <path>`, the system shall record that checkout as a
pin for the plugin it holds.

#### `PIN-02`
When `rig pin` is given a name that is not a path, the system shall resolve it
to the local clone of that plugin's marketplace source repo, found under the
folder `clones:` in `~/.rig/rigs.yml` names for the repo's host, or, where it
names none, under the folder an existing pin's checkout and its `origin` show
that host's clones live in.

#### `PIN-03`
If a pin target holds no plugin manifest, then the system shall refuse the pin.

#### `PIN-04`
If a pinned checkout is missing at launch, then the system shall stop the
launch, naming the pin and how to unpin it.

#### `PIN-05`
When the user runs `rig unpin <path|name>`, the system shall stop loading that
checkout.

#### `PIN-06`
When the user runs `rig pins`, the system shall list the pins, indented one
space, with when each was pinned.

#### `PIN-07`
When an interactive launch starts inside a pinned checkout, the system shall
load that pin, and offer it in the picker loading. When a launch loading a pin starts inside
its checkout or in a folder above it, the system shall mark the pin ❗ in place
of 📌 in the picker and its legend, warn in the pin's dialog that the session
runs on the files it edits, and offer to skip the checkout for that launch
only.

#### `PIN-08`
When a launch's rigs include a pinned plugin, the system shall load the pinned
checkout in place of the installed copy.

#### `PIN-09`
When an interactive launch's rigs do not include a pinned plugin that has a
copy installed for the working directory, the system shall leave that pin out,
and offer it in the picker not loading.

#### `PIN-10`
If a launch's rigs do not include a pinned plugin that has a copy installed
for the working directory and no one is at a terminal to ask, then the system
shall launch without that pin.

#### ~~`PIN-11`~~
~~Where a launch loads a pin whose checkout holds the working directory or sits~~
~~inside it, the system shall start Claude Code with~~
~~`CLAUDE_CODE_AUTO_MODE_SERVER=0`, unless the environment already sets it, and~~
~~say so before Claude Code starts.~~

~~> Rationale: works around anthropics/claude-code#95982 by putting auto mode on~~
~~> its billed classifier fallback. Claude Code 2.1.327 announced that fallback's~~
~~> removal, so this requirement expires with it; retire it once #95982 is fixed.~~

_Retired 2026-11-24: moved to [CLAUDE-03](#claude-03). The ID is not reused._

#### `PIN-12`
The system shall mark each pinned plugin with 📌 in front of its name wherever
it lists plugins or pins: the launch summary, `rig pins`, `rig list`, the graph,
the picker, the switch pane, and the rig editor.

#### `PIN-13`
When the user toggles a pinned plugin's row in the picker, the system shall
show the pin's checkout, when it was pinned, and whether it loads, unpinning it
on enter or Unpin, taking the plugin out of the launch or putting it in on a
second button, loading the checkout or skipping it on a third, and closing on
escape or a click on its ✕.

#### `PIN-14`
When the user runs `rig pin` or `rig unpin` with no arguments, the system shall
act on the checkout the working directory is in: for `pin`, the nearest folder
at or above it that holds a plugin manifest; for `unpin`, the pin whose
checkout holds it.

#### `PIN-15`
When a launch's rigs do not include a pinned plugin and no copy of it is
installed for the working directory, the system shall load the pin without
asking, offer it in the picker loading, and note `no installed copy` on its
line of the launch summary; a launch that starts in or above its checkout
offers it as PIN-07 says.

> Rationale: such a pin stands in for nothing, so pinning it can only mean
> loading it: a plugin under development that no marketplace lists yet.

#### `PIN-16`
If `rig pin` can't resolve a name to a checkout, then the system shall refuse
the pin, saying why and naming `rig pin <path>`.

#### `PIN-17`
When the user presses `p` on a plugin's row in the picker, the system shall
open the pin's dialog for a pinned plugin, and for any other, pin the checkout
its name resolves to as PIN-02 says, asking for no path, or, where it resolves
to none, open a folder browser.

#### `PIN-18`
When the user pins a folder from the picker's folder browser, the system shall
pin it for the row's plugin, refusing a folder that holds no plugin manifest or
holds another plugin's and saying why, and close the browser on escape or a
click on its ✕.

_No SANDBOX category: retired 2026-11-24, when SANDBOX-01 moved to CLAUDE-04, since the
sandbox is Claude Code's. The ID is not reused._

### `LAUNCH`
Launch

#### `LAUNCH-01`
The system shall pass every argument it does not consume to the tool
unchanged.

#### `LAUNCH-02`
When a launch starts, the system shall print the rigs, the rule that made each
rig a default, the pins, and the sandbox state (Claude Code) or the tool's name
(Grok Build) before the tool starts.

#### `LAUNCH-03`
When the user runs `rig` with arguments that start with an option or a prompt
of more than one word, the system shall launch the default rig and pass the
arguments to the tool; if they start with a single word that is neither
rig's command nor the tool's, then the system shall refuse it as an unknown
command.

#### ~~`LAUNCH-04`~~
~~When the first argument is a Claude Code subcommand, the system shall run~~
~~Claude Code with the arguments unchanged, without loading a rig.~~

_Retired 2026-11-24: moved to [TOOL-03](#tool-03). The ID is not reused._

#### `LAUNCH-05`
When an interactive launch has arguments and no `--select`, the system shall
launch without the picker, whatever it has to install or pins to choose, each
pin loading as the picker would offer it, unless a pin it would load holds the
working directory or sits inside it: then it shall open the picker first, since
the session would run on the files it edits. When the picker opens on a launch
with a plugin to install or a pin to choose, it shall start with its cursor on
the first pin to choose, else the first plugin to install, and a notice naming
each: a pin that holds the working directory and whether its checkout loads, a
pin the rigs leave out that has an installed copy, and the plugins that install
at launch.

#### `LAUNCH-06`
While an interactive launch runs, the system shall stay running until Claude
Code exits, leaving Ctrl-C to Claude Code, and then exit with Claude Code's
exit status.

#### `LAUNCH-07`
Where a launch passes `--select`, the system shall first show a picker headed
`rig select` with the command line that opened it: the plugins against the rigs as
`rig list --graph` shows them, with `full` among the rigs, each row on one line,
marking under each rig whether the launch loads it whole or in part, with one
cursor on a rig's name or a plugin's row that the arrow keys, `h`, `j`, `k`,
`l`, and tab move,
toggling what the cursor is on with space or enter, a rig other than the base
rig toggling on a click on its name or anywhere in its column, a plugin
toggling on a click on its name, launching on `g`,
Shift+Enter, or a click on the footer's 🚀, and refusing the launch on `q`.

#### `LAUNCH-09`
When the user chooses `full` in the picker, the system shall take away the other
rigs chosen, and when the user chooses another rig, take away `full`.

#### `LAUNCH-10`
When the user presses `e` in the picker, the system shall open the rig editor,
then reopen the picker on the edited rigs, keeping the rigs chosen that still
exist.

#### `LAUNCH-11`
When the user toggles a plugin with no pin in the picker, or chooses to on a
pinned plugin's dialog, the system shall take that plugin out of the launch, or put it in,
whatever rigs hold it, marking each rig the launch then loads only part of as partly loaded,
explaining that mark only while some rig carries it, and naming the plugins
picked and taken out after the rigs.

#### `LAUNCH-08`
If a launch passes `--select` and no one is at a terminal, then the system
shall refuse the launch.

#### `LAUNCH-12`
When a launch's rigs include `full`, the system shall describe it as all of its
plugins, naming the ones taken out, in place of the rigs.

#### `LAUNCH-13`
The picker shall end its footer with a `g Go` 🚀 launch item, animated unless
Textual's animations are off, that launches on a click.

#### `LAUNCH-14`
Where beacon is installed, when a session rig launched at a terminal starts,
the system shall put the project's name on beacon's pane badge, followed by
` · ` and the session's rigs separated by ` ✦ `. The project's name is the last
segment of the origin remote's URL, else the git repository's folder name, else
the working folder's name, as beacon names it.

Rationale: a caller's badge replaces beacon's own `project · task` text, so the
rigs alone would leave the pane without saying which project it is in.

#### `LAUNCH-15`
If the terminal goes away while the picker or the rig editor is open, then the system shall exit as a hangup ends it, even when it
started with SIGHUP ignored.

#### ~~`LAUNCH-16`~~
~~If a launch's arguments carry, before any `--`, an option that neither rig nor~~
~~Claude Code's `--help` lists, then the system shall refuse the launch before~~
~~the picker opens, naming the option.~~

_Retired 2026-11-24: moved to [TOOL-04](#tool-04). The ID is not reused._

#### `LAUNCH-17`
While the picker or the rig editor shows a message, the system shall take the
message away on escape, leaving the picker or editor open; with no message on
show, escape refuses the picker's launch.

### `SWITCH`
Switching rigs mid-session, in Claude Code

#### `SWITCH-01`
When the user runs `/rig <rig>...` in a session rig launched at a
terminal, the system shall record the switch and exit Claude Code.

#### `SWITCH-02`
When Claude Code exits after a recorded switch, the system shall launch the
named rigs resuming the same conversation, with the launch's sandbox state:
with the plugins and pins chosen in the switch pane, without asking again, or,
for a switch that names rigs, offering pins as any launch does. The resumed
conversation shall open with no new turn, and a toast naming what the session
switched to.

#### `SWITCH-03`
If the user runs `/rig`, naming rigs or not, in a session rig did not
launch at a terminal, then the system shall refuse the switch, naming the
command that resumes the conversation with those rigs, or with the session's
own.

#### `SWITCH-04`
If `/rig` names a rig that isn't defined, then the system shall refuse
the switch, naming the rigs.

#### `SWITCH-05`
When the user runs `/rig` naming no rig in a session rig launched at a
terminal, the system shall open a pane with the picker's graph, set to the
rigs, plugins, and pins the session loads, toggling them as the picker does,
with a toast ending in ✕ naming each pin that holds the working directory and
whether its checkout loads, and `h`, `j`, `k`, and `l` buttons that move its
cursor as the arrow keys move the picker's; it shall record the switch and exit Claude Code on
`g`, or, when the picks are what the session already loads, close and keep the
session, and close without a switch on escape or `q`. The pane shall name each
plugin without its marketplace unless two rows share the name, stagger the rig
names over as few rows as fit when the pane is too narrow for them on one, and
ask a docked seat for no more width than two such rows take. Against what the
session loads, it shall show each rig and plugin the switch brings in in green
and each it takes out in red, listing those plugins under the summary.

#### `SWITCH-06`
When a switch relaunches Claude Code, the system shall pass it the options the
launch before it passed through, each with its values as `claude --help` says
it takes them, leaving out the prompt, anything after `--`, and the options that
pick or start a conversation.

### `TOOL`
The tool a launch starts

#### `TOOL-01`
The system shall launch Claude Code unless the user runs `rig grok`, reading the
same rig definitions and pins whichever tool a launch starts.

#### `TOOL-02`
When the user runs `rig claude` or `rig grok`, the system shall treat the
arguments that follow as arguments to `rig`, launching that tool with the
default rigs when none follow.

#### `TOOL-03`
When the first argument is a command the tool's `--help` lists, the system
shall run the tool with the arguments unchanged, without loading a rig.

#### `TOOL-04`
If a launch's arguments carry, before any `--`, an option that neither rig nor
the tool's `--help` lists, then the system shall refuse the launch before the
picker opens, naming the option.

#### `TOOL-05`
Where no other shell function defines `claude`, the install shall make `claude`
run `rig claude`; and where Grok Build is on PATH and no other shell function
defines `grok`, make `grok` run `rig grok`.

### `CLAUDE`
Launching Claude Code

#### `CLAUDE-01`
When a Claude Code launch uses rigs, the system shall start Claude Code with their
plugins enabled for that session, setting no other plugin's state apart from
pins, so a plugin enabled during the session loads. A rig plugin that a project
settings file covering the working directory sets to `false` is left to the
settings files and named on the launch summary, unless the user picked it on
its own; a `false` in the user's settings file does not keep it out.

#### `CLAUDE-02`
When a Claude Code launch starts, the system shall turn off each plugin the user's Claude
Code settings file enables, naming the ones the launch's rigs don't include.

#### `CLAUDE-03`
Where a launch loads a pin whose checkout holds the working directory or sits
inside it, the system shall start Claude Code with
`CLAUDE_CODE_AUTO_MODE_SERVER=0`, unless the environment already sets it, and
say so before Claude Code starts.

> Rationale: works around anthropics/claude-code#95982 by putting auto mode on
> its billed classifier fallback. Claude Code 2.1.327 announced that fallback's
> removal, so this requirement expires with it; retire it once #95982 is fixed.

#### `CLAUDE-04`
Where a Claude Code launch passes `--sandbox`, the system shall start Claude Code with the
sandbox on, running sandboxed commands without a permission prompt, failing if
the sandbox is unavailable and allowing no unsandboxed commands.

### `GROK`
Launching Grok Build

#### `GROK-01`
When a launch starts Grok Build, the system shall start it with a grok home of
its own for that launch, linking each entry of the user's grok home other than
`config.toml` and `plugins`, so the launch writes no file another grok session
reads.

#### `GROK-02`
When a launch starts Grok Build, the system shall write the launch's
`config.toml` as the user's, with its `[plugins]` table replaced by one that
enables each of the launch's plugins by its name without the marketplace.

#### `GROK-03`
When a launch starts Grok Build, the system shall fill the launch's `plugins`
folder with a link to each entry of the user's grok `plugins` folder and, for
each pin the launch loads, a link to its checkout under the plugin's name,
standing in for the installed copy.

#### `GROK-04`
When Grok Build exits, the system shall carry each file the session wrote in
the launch's grok home back to the user's: a changed `config.toml` with the
user's own `[plugins]` table kept, and each other entry the session created or
replaced; then remove the launch's grok home and exit with Grok Build's exit
status.

#### `GROK-05`
If the user's `config.toml` changed while a Grok Build launch ran, and the
session changed the launch's copy too, then the system shall leave the user's
file as it is, keep the session's copy beside it, and name both.

#### `GROK-06`
When a launch starts Grok Build, the system shall pass `--sandbox` to it as
Grok Build's own option, with its value.

#### `GROK-07`
While a launch starts Grok Build, the system shall leave Claude Code's settings
files unchanged and set no Claude Code environment variable.

#### `GROK-08`
If Grok Build doesn't load one of a launch's plugins, as `grok inspect` reports
in the launch's grok home, then the system shall name it before Grok Build
starts.

#### `GROK-09`
When a launch starts Grok Build, the system shall put its grok home at the
first numbered path no running Grok Build launch holds, so a later launch
reuses the path, and a command grok remembers as always allowed from a pinned
plugin keeps applying.

### `SHELL`
Shell integration

#### `SHELL-01`
When the user runs `/rig:install-rig`, the system shall put a `rig` command on
PATH that runs the installed version.

#### `SHELL-02`
When a session starts and the `rig` command on PATH runs a version other than
the one installed, the system shall tell the user to run `/rig:install-rig`.

#### `SHELL-03`
The system shall accept `rig rig <command>` as `rig <command>`, and `rig plugin
pin|unpin` as `rig pin|unpin`, so `rig` can stand in for `claude`.

#### ~~`SHELL-04`~~
~~Where no other shell function defines `claude`, the install shall make `claude`~~
~~run `rig claude`.~~

_Retired 2026-11-24: moved to [TOOL-05](#tool-05). The ID is not reused._

#### `SHELL-05`
When the user runs `rig` with no arguments and someone is at a terminal, the
system shall launch as `rig --select` does, opening first-run setup first when
no rigs are defined; with no one at a terminal, it shall print its usage without
launching Claude Code.

#### ~~`SHELL-06`~~
~~When the user runs `rig claude`, the system shall treat the arguments that~~
~~follow as arguments to `rig`, launching the default rig when none follow.~~

_Retired 2026-11-24: moved to [TOOL-02](#tool-02). The ID is not reused._

### `TAB`
Tab completion

#### `TAB-01`
When the user completes the first argument of `rig`, the system shall offer
rig's commands together with Claude Code's subcommands.

#### `TAB-02`
Where `claude` runs rig, the system shall complete `claude` as it completes
`rig`, also offering `rig` as the first argument.

#### `TAB-03`
When the user completes an argument of `rig use` that follows only rig names,
or a rig name after rig names joined by commas, the system shall offer the rigs
not yet named apart from the base rig, `full` among them, and `none` when
nothing is named yet.

#### `TAB-04`
When the user completes an argument of `rig pin`, the system shall offer the
marketplace plugins that resolve to a local clone as PIN-02 says and aren't pinned, along with
directories.

#### `TAB-05`
When the user completes an argument of `rig unpin`, the system shall offer the
pinned plugins.

#### `TAB-06`
When the user completes a flag of a launch, the system shall offer `--sandbox`
and `--select`.

#### `TAB-07`
When the user completes the value of `--resume` or `-r` in a launch, the system
shall offer the Claude Code sessions of the working directory, newest first,
each described by its `/rename` title, else the title Claude Code gave it, else
its first prompt.

### `DOCTOR`
Doctor

#### `DOCTOR-01`
When the user runs `rig doctor`, the system shall check that the `rig` command
a new zsh finds on PATH runs the installed version.

#### `DOCTOR-02`
When the user runs `rig doctor`, the system shall check that `claude` runs rig
in a new zsh, naming the file that defines `claude` when it doesn't.

#### `DOCTOR-03`
When the user runs `rig doctor`, the system shall check that a new zsh
completes `rig` and `claude` with the installed version's completion.

#### `DOCTOR-04`
If a doctor check fails, then the system shall print the command that fixes it
and exit non-zero.

#### `DOCTOR-05`
When the user runs `rig doctor`, the system shall run Claude Code's `doctor`
after its own checks.
