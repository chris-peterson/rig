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

- **rig**: a named set of plugins chosen for a kind of work. A rig can extend
  or include other rigs, so a base rig carries the plugins every rig shares.
- **base rig**: the rig first-run setup creates from the plugins you want in
  every session; other rigs extend it.
- **default rig**: the rig a launch uses when it names none.
- **pin**: a local plugin checkout that stands in for the plugin's installed
  copy, so changes to the checkout can be used for a stretch of real work
  before a marketplace release.
- **sandbox**: Claude Code's sandbox for Bash commands, which a launch can turn
  on.
- **launch**: one start of Claude Code through rig.

## Requirements

### `RIG`
Rigs

#### `RIG-01`
The system shall read rig definitions from a user-level file, each naming the
plugins it loads.

#### `RIG-02`
Where a rig extends or includes other rigs, the system shall load the plugins
of each of those rigs along with its own.

#### `RIG-03`
If the rigs a rig extends or includes form a cycle, then the system shall
refuse the launch, naming the rigs in the cycle.

#### `RIG-04`
When a launch uses a rig, the system shall start Claude Code with that rig's
plugins as the only plugins enabled, apart from pins.

#### `RIG-05`
When the user runs `rig use <name>`, the system shall launch Claude Code with
the named rig.

#### `RIG-06`
When the user runs `rig <name>` and `<name>` is not one of rig's commands, the
system shall launch Claude Code with the named rig.

#### `RIG-07`
When the user runs `rig` with no rig named, the system shall launch Claude Code
with the default rig.

#### `RIG-08`
If a rig's name matches one of rig's commands, then the system shall reject the
definition, naming the clash.

#### `RIG-09`
When the user runs `rig list`, the system shall list each rig with its plugins
and the rigs it extends or includes.

#### `RIG-10`
If a rig names a plugin that is not installed, then the system shall offer to
install it, launch only after the user confirms, and refuse the launch if the
user declines.

#### `RIG-11`
If a rig names a plugin that is not installed and no one is at a terminal to
confirm, then the system shall refuse the launch, naming the plugin.

### `SETUP`
First-run setup

#### `SETUP-01`
When an interactive launch finds no rig definitions, the system shall run
first-run setup before launching.

#### `SETUP-02`
During first-run setup, the system shall list the plugins Claude Code's
settings enable and ask which of them form the base rig.

#### `SETUP-03`
When the user confirms the base rig, the system shall write it to the rig
definitions as the default rig.

#### `SETUP-04`
After writing the base rig, the system shall offer to create named rigs that
extend it, until each enabled plugin outside the base rig is in at least one
rig or the user stops.

#### `SETUP-04a`
Where the `enabledPlugins` block of the user's Claude Code settings file
separates its entries into groups with blank lines, the system shall suggest
one named rig per group of plugins outside the base rig, asking the user to
name each.

#### `SETUP-04b`
Where the `enabledPlugins` block has no blank-line groups, the system shall
suggest one named rig per marketplace, named after the marketplace.

#### `SETUP-05`
When the user runs `rig setup`, the system shall run first-run setup, starting
from the existing rig definitions.

#### `SETUP-06`
If a launch finds no rig definitions and no one is at a terminal, then the
system shall refuse the launch, naming `rig setup`.

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
ask whether to load that pin.

#### `PIN-08`
When a launch's rig includes a pinned plugin, the system shall load the pinned
checkout in place of the installed copy.

#### `PIN-09`
When an interactive launch's rig does not include a pinned plugin, the system
shall ask whether to load that pin.

#### `PIN-10`
If a launch's rig does not include a pinned plugin and no one is at a terminal
to ask, then the system shall launch without that pin.

### `SANDBOX`
Sandbox

#### `SANDBOX-01`
Where a launch passes `--sandbox`, the system shall start Claude Code with the
sandbox on, failing if the sandbox is unavailable and allowing no unsandboxed
commands.

#### `SANDBOX-02`
Where a rig's definition turns the sandbox on, the system shall sandbox every
launch of that rig.

### `LAUNCH`
Launch

#### `LAUNCH-01`
The system shall pass every argument it does not consume to Claude Code
unchanged.

#### `LAUNCH-02`
When a launch starts, the system shall print the rig, the pins, and the sandbox
state before Claude Code starts.

### `SHELL`
Shell integration

_(none yet, add with `/sextant:spec-req new`)_

### `TAB`
Tab completion

_(none yet, add with `/sextant:spec-req new`)_
