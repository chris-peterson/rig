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

- **rig**: a named set of plugins chosen for a kind of work. Every rig but the
  base rig extends one other rig and loads its plugins too, so each rig carries
  the base rig's plugins.
- **base rig**: the one rig that extends no other. First-run setup creates it
  from the plugins you want in every session.
- **default rig**: the rig a launch uses when it names none.
- **pin**: a local plugin checkout that stands in for the plugin's installed
  copy, so changes to the checkout can be used for a stretch of real work
  before a marketplace release.
- **sandbox**: Claude Code's sandbox for Bash commands, which a launch can turn
  on.
- **launch**: one start of Claude Code through rig.
- **switch**: moving a session to another rig, carrying its conversation over.

## Requirements

### `RIG`
Rigs

#### `RIG-01`
The system shall read rig definitions from a user-level file, each naming the
plugins it loads.

#### `RIG-02`
Where a rig extends another rig, the system shall load the plugins of that
rig, and of the rig it extends in turn, along with its own.

#### `RIG-03`
If the rigs a rig extends form a cycle, then the system shall refuse the
launch, naming the rigs in the cycle.

#### `RIG-04`
When a launch uses a rig, the system shall start Claude Code with that rig's
plugins enabled for that session, setting no other plugin's state apart from
pins, so a plugin enabled during the session loads.

#### `RIG-05`
When the user runs `rig use <name>`, the system shall launch Claude Code with
the named rig.

#### `RIG-06`
When a launch names no rig, the system shall launch Claude Code with the
default rig.

#### `RIG-07`
When the user runs `rig list`, the system shall list each rig with its plugins
and the rig it extends.

#### `RIG-08`
If a rig names a plugin that is not installed, then the system shall list it
on the launch confirmation, install it once the user confirms the launch, and
refuse the launch if the user cancels.

#### `RIG-09`
If a rig names a plugin that is not installed and no one is at a terminal to
confirm, then the system shall refuse the launch, naming the plugin.

#### `RIG-10`
If a rig extends more than one rig, then the system shall refuse the launch,
naming the rig.

#### `RIG-11`
If more than one rig extends no other rig, then the system shall refuse the
launch, naming those rigs.

#### `RIG-12`
When a launch starts, the system shall turn off each plugin the user's Claude
Code settings file enables, naming the ones the rig doesn't include.

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
rig definitions as the default rig.

#### `SETUP-04`
While the rig editor is open, the system shall show a draft rig, extending the
base rig, for each group of enabled plugins that no rig loads, saving a
draft only once the user keeps it under a name.

#### `SETUP-04a`
Where the `enabledPlugins` block of the user's Claude Code settings file
separates its entries into groups with blank lines, the system shall make one
draft rig per group.

#### `SETUP-04b`
Where the `enabledPlugins` block has no blank-line groups, the system shall
make one draft rig per marketplace, named after the marketplace.

#### `SETUP-05`
When the user runs `rig setup`, the system shall open the rig editor on the
existing rig definitions.

#### `SETUP-06`
If a launch finds no rig definitions and no one is at a terminal, then the
system shall refuse the launch, naming `rig setup`.

### `EDITOR`
Rig editor

#### `EDITOR-01`
The rig editor shall show the rigs in one pane as a tree rooted at the base
rig, each rig appearing once, under the rig it extends, and the plugins of the
selected rig in a second pane.

#### `EDITOR-02`
The rig editor shall offer every installed plugin, and every plugin a rig
names, as a candidate for the selected rig.

#### `EDITOR-03`
The rig editor shall move through rigs and plugins with the arrow keys or the
mouse, and toggle the highlighted plugin with space or a click.

#### `EDITOR-04`
The rig editor shall show the plugins the selected rig inherits as included and
locked, naming the rig each comes from.

#### `EDITOR-05`
When the user creates a rig or changes the rig a rig extends, the system shall
require one rig to extend, offering only the rigs that would not form a cycle.

#### `EDITOR-06`
When the user marks a rig as the default, the system shall make it the rig a
launch uses when it names none.

#### `EDITOR-07`
If the user deletes the base rig, the default rig, or a rig that other rigs
extend, then the system shall refuse, saying which.

#### `EDITOR-08`
When the user saves, the system shall write the rigs to the rig definitions
file, the base rig first and the rest in alphabetical order, each with its
plugins in alphabetical order.

#### `EDITOR-09`
If the user quits the rig editor with unsaved changes, then the system shall
ask whether to save them, with saving as the default choice and discarding as
the other.

#### `EDITOR-10`
When the user double-clicks a rig or a draft, or presses enter on it, the
system shall open it for naming, and for choosing the rig it extends unless it
is the base rig.

#### `EDITOR-11`
When the user renames a rig, the system shall carry the new name to the rigs
that extend it and to the default.

#### `EDITOR-12`
The rig editor shall list the rigs that extend each rig in alphabetical order,
re-sorting them as rigs are created, renamed, or moved.

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
When a launch's rig includes a pinned plugin, the system shall load the pinned
checkout in place of the installed copy.

#### `PIN-09`
When an interactive launch's rig does not include a pinned plugin, the system
shall offer that pin on the launch confirmation, unselected.

#### `PIN-10`
If a launch's rig does not include a pinned plugin and no one is at a terminal
to ask, then the system shall launch without that pin.

#### `PIN-11`
Where a launch loads a pin whose checkout holds the working directory or sits
inside it, the system shall start Claude Code with
`CLAUDE_CODE_AUTO_MODE_SERVER=0`, unless the environment already sets it, and
say so before Claude Code starts.

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
When a launch starts, the system shall print the rig, the pins, and the sandbox
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
system shall show one launch confirmation: the rig and its plugins, read-only,
then the pins the rig leaves to choose, launching on enter and refusing the
launch on escape.

#### `LAUNCH-06`
While an interactive launch runs, the system shall stay running until Claude
Code exits, leaving Ctrl-C to Claude Code, and then exit with Claude Code's
exit status.

### `SWITCH`
Switching rigs mid-session

#### `SWITCH-01`
When the user runs `/rig:switch <rig>` in a session rig launched at a
terminal, the system shall record the switch and tell the user to exit Claude
Code.

#### `SWITCH-02`
When Claude Code exits after a recorded switch, the system shall launch the
named rig resuming the same conversation, with the launch's sandbox state, and
offer pins as any launch does.

#### `SWITCH-03`
If the user runs `/rig:switch <rig>` in a session rig did not launch at a
terminal, then the system shall refuse the switch, naming the command that
resumes the conversation with that rig.

#### `SWITCH-04`
If `/rig:switch` names a rig that isn't defined, then the system shall refuse
the switch, naming the rigs.

#### `SWITCH-05`
When the user runs `/rig:switch` naming no rig, the system shall list the rigs,
marking the one the session uses.

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
When the user runs `rig` with no arguments, the system shall print its usage
without launching Claude Code.

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
When the user completes the argument after `rig use`, the system shall offer
the names of the rigs.

#### `TAB-04`
When the user completes an argument of `rig pin`, the system shall offer the
marketplace plugins that resolve to a local clone and aren't pinned, along with
directories.

#### `TAB-05`
When the user completes an argument of `rig unpin`, the system shall offer the
pinned plugins.

#### `TAB-06`
When the user completes a flag of a launch, the system shall offer `--sandbox`.

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
