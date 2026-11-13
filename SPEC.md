# rig specification

rig launches Claude Code with a chosen set of plugins (a rig), loads pinned
local plugin checkouts into every launch, and can run the session inside
Claude Code's sandbox.

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
- **none**: a preset that rig provides, launching stock Claude Code with no
  plugins at all.
- **default rigs**: the rigs a launch adds to the base rig when it names none.
- **pin**: a local plugin checkout that stands in for the plugin's installed
  copy, so changes to the checkout can be used for a stretch of real work
  before a marketplace release.
- **sandbox**: Claude Code's sandbox for Bash commands, which a launch can turn
  on.
- **launch**: one start of Claude Code through rig.
- **switch**: moving a session to other rigs, carrying its conversation over.

## Requirements

### `RIG`
Rigs

#### `RIG-01`
The system shall read rig definitions from a user-level file, each naming the
plugins it loads.

#### `RIG-02`
The system shall load the base rig's plugins in every launch, along with the
plugins of each rig the launch names.

#### `RIG-03`
When a launch names several rigs, separated by spaces, commas, or both, the
system shall load the plugins of all of them.

#### `RIG-04`
When a launch uses rigs, the system shall start Claude Code with their
plugins enabled for that session, setting no other plugin's state apart from
pins, so a plugin enabled during the session loads.

#### `RIG-05`
When the user runs `rig use <rig>...`, the system shall launch Claude Code with
the base rig and the named rigs.

#### `RIG-06`
When a launch names no rig, the system shall launch Claude Code with the base
rig and the default rigs.

#### `RIG-07`
When the user runs `rig list`, the system shall list each rig with its plugins,
marking the base rig and the default rigs.

#### `RIG-08`
If a rig names a plugin that is not installed, then the system shall list it
on the launch confirmation, install it once the user confirms the launch, and
refuse the launch if the user cancels.

#### `RIG-09`
If a rig names a plugin that is not installed and no one is at a terminal to
confirm, then the system shall refuse the launch, naming the plugin.

#### `RIG-10`
The system shall provide a rig named `full` that loads every installed plugin.

#### `RIG-11`
If the rig definitions give a rig anything but plugins, define a rig named
`full` or `none`, or define no rig named `base`, then the system shall refuse
the launch, saying which.

#### `RIG-13`
When the user runs `rig list --json`, the system shall print the rigs, their
plugins, and the default rigs as JSON.

#### `RIG-14`
When the user runs `rig list --graph`, the system shall print a table of
plugins against rigs, marking each rig that loads each plugin, listing the
installed plugins no rig names after the rest, then any pinned plugin neither
lists.

#### `RIG-15`
When a launch names `none`, the system shall start Claude Code with every
plugin it knows of turned off, the base rig's and pinned plugins' included.

#### `RIG-16`
When a launch names `none`, the system shall say what the session goes without
and launch only once the user at the terminal confirms.

#### `RIG-17`
If a launch names `none` along with other rigs, or no one is at a terminal to
confirm it, then the system shall refuse the launch.

#### `RIG-12`
When a launch starts, the system shall turn off each plugin the user's Claude
Code settings file enables, naming the ones the launch's rigs don't include.

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
The rig editor shall move through rigs and plugins with the arrow keys or the
mouse, and toggle the highlighted plugin with space or a click.

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
plugins in alphabetical order.

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

### `PIN`
Local pins

#### `PIN-01`
When the user runs `rig pin <path>`, the system shall record that checkout as a
pin for the plugin it holds.

#### `PIN-02`
When `rig pin` is given a name that is not a path, the system shall resolve it
to the local clone of that plugin's marketplace source repo.

#### `PIN-03`
If a pin target holds no plugin manifest, then the system shall refuse the pin.

#### `PIN-04`
If a pinned checkout is missing at launch, then the system shall stop the
launch, naming the pin and how to unpin it.

#### `PIN-05`
When the user runs `rig unpin <path|name>`, the system shall stop loading that
checkout.

#### `PIN-06`
When the user runs `rig pin` with no arguments, the system shall list the pins
with when each was pinned.

#### `PIN-07`
When an interactive launch starts inside a pinned checkout, the system shall
offer that pin on the launch confirmation, selected.

#### `PIN-08`
When a launch's rigs include a pinned plugin, the system shall load the pinned
checkout in place of the installed copy.

#### `PIN-09`
When an interactive launch's rigs do not include a pinned plugin, the system
shall offer that pin on the launch confirmation, unselected.

#### `PIN-10`
If a launch's rigs do not include a pinned plugin and no one is at a terminal
to ask, then the system shall launch without that pin.

#### `PIN-11`
Where a launch loads a pin whose checkout holds the working directory or sits
inside it, the system shall start Claude Code with
`CLAUDE_CODE_AUTO_MODE_SERVER=0`, unless the environment already sets it, and
say so before Claude Code starts.

#### `PIN-12`
The system shall mark each pinned plugin with 📌 wherever it lists plugins or
pins: the launch summary, `rig pin`, `rig list`, the graph, the picker, the
launch confirmation, and the rig editor.

#### `PIN-13`
When the user toggles a pinned plugin's row in the picker, the system shall
show the pin's checkout, when it was pinned, and whether it loads, unpinning it
on enter or Unpin, taking the plugin out of the launch or putting it in on a
second button, loading the checkout or skipping it on a third, and closing on
escape or a click on its ✕.

### `SANDBOX`
Sandbox

#### `SANDBOX-01`
Where a launch passes `--sandbox`, the system shall start Claude Code with the
sandbox on, failing if the sandbox is unavailable and allowing no unsandboxed
commands.

### `LAUNCH`
Launch

#### `LAUNCH-01`
The system shall pass every argument it does not consume to Claude Code
unchanged.

#### `LAUNCH-02`
When a launch starts, the system shall print the rigs, the pins, and the sandbox
state before Claude Code starts.

#### `LAUNCH-03`
When the user runs `rig` with arguments that don't start with one of rig's
commands, the system shall launch the default rig and pass the arguments to
Claude Code.

#### `LAUNCH-04`
When the first argument is a Claude Code subcommand, the system shall run
Claude Code with the arguments unchanged, without loading a rig.

#### `LAUNCH-05`
When an interactive launch has a plugin to install or a pin to choose, the
system shall show one launch confirmation: the rigs, which the user can add to
or take from, the plugins they load, and the pins they leave to choose,
launching on enter and refusing the launch on `q`.

#### `LAUNCH-06`
While an interactive launch runs, the system shall stay running until Claude
Code exits, leaving Ctrl-C to Claude Code, and then exit with Claude Code's
exit status.

#### `LAUNCH-07`
Where a launch passes `--select`, the system shall first show a picker headed
with the command line that opened it: the plugins against the rigs as
`rig list --graph` shows them, with `full` among the rigs, each row on one line,
marking under each rig whether the launch loads it whole or in part, with one
cursor on a rig's name or a plugin's row that the arrow keys and tab move,
toggling what the cursor is on with space or enter as a click on it does, a
rig other than the base rig toggling on a click on its name, launching on `l`,
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
The picker shall end its footer with a 🚀 launch item, animated unless
Textual's animations are off, that launches on a click.

### `SWITCH`
Switching rigs mid-session

#### `SWITCH-01`
When the user runs `/rig:switch <rig>...` in a session rig launched at a
terminal, the system shall record the switch and tell the user to exit Claude
Code.

#### `SWITCH-02`
When Claude Code exits after a recorded switch, the system shall launch the
named rigs resuming the same conversation, with the launch's sandbox state, and
offer pins as any launch does.

#### `SWITCH-03`
If the user runs `/rig:switch <rig>...` in a session rig did not launch at a
terminal, then the system shall refuse the switch, naming the command that
resumes the conversation with those rigs.

#### `SWITCH-04`
If `/rig:switch` names a rig that isn't defined, then the system shall refuse
the switch, naming the rigs.

#### `SWITCH-05`
When the user runs `/rig:switch` naming no rig, the system shall list the rigs,
marking the ones the session uses.

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

#### `SHELL-04`
Where no other shell function defines `claude`, the install shall make `claude`
run `rig claude`.

#### `SHELL-05`
When the user runs `rig` with no arguments, the system shall open first-run
setup when no rigs are defined and someone is at a terminal, and print its usage
otherwise, without launching Claude Code.

#### `SHELL-06`
When the user runs `rig claude`, the system shall treat the arguments that
follow as arguments to `rig`, launching the default rig when none follow.

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
marketplace plugins that resolve to a local clone and aren't pinned, along with
directories.

#### `TAB-05`
When the user completes an argument of `rig unpin`, the system shall offer the
pinned plugins.

#### `TAB-06`
When the user completes a flag of a launch, the system shall offer `--sandbox`
and `--select`.

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
