# Using rig

## Install

Install the plugin, then run its bootstrap from a Claude Code prompt:

```text
/rig:install-rig
```

That puts `rig` on your PATH at `~/.local/bin/rig`, with zsh tab completion,
and makes `claude` run rig in new shells, so the habit you already have picks
up your rigs and pins. rig runs through [uv](https://docs.astral.sh/uv/), so uv
must be on your PATH too. When a plugin update leaves the `rig` on your PATH
behind, a session start tells you to run `/rig:install-rig` again.

`claude` with no arguments launches your default rigs. `rig` with no arguments
opens first-run setup when you have no rigs yet, and prints its usage after
that.

**Adopting rig turns off the plugins your Claude Code settings enable.** Every
launch sets each plugin `~/.claude/settings.json` enables to off, so a session
starts with exactly the rigs you chose. Put everything you want in every
session in the base rig, as few or as many plugins as you like; first-run
setup starts it from the plugins your settings enable today. Claude Code
started some other way (an IDE, the desktop app) reads the same settings file,
so it starts without them.

If another shell function already defines `claude` (a wrapper of your own),
rig leaves it alone. Have that wrapper call `rig claude "$@"` where it called
`claude`.

To check the setup:

```bash
rig doctor
```

It checks what a new zsh sees: that `rig` on your PATH runs the installed
plugin (or a checkout you're trying out), that `claude` runs rig, and that zsh
completes both. A failed check prints the command that fixes it. Claude Code's
own doctor runs after rig's checks, so `claude doctor` reports both.

## Rigs

A rig is a named list of plugins. Every launch loads the **base** rig, and you
add other rigs on top of it for the work at hand: small sets like `infra` or
`web` that you combine as you need them. `full` is every plugin you have
installed. Pins (below) load with them.

```bash
claude                      # base plus your default rigs
rig use infra               # base plus infra
rig use entsvc infra        # base plus both; `entsvc,infra` and "entsvc infra" work too
rig use full                # every installed plugin
claude "fix the bug"        # a prompt, with the default rigs
rig list                    # every rig and its plugins
rig list --graph            # a table of plugins against rigs
rig list --json             # the same, for scripts
```

A plugin you enable during a session with `/plugin enable` loads in that
session; the next launch turns it off again in `~/.claude/settings.json` and
names it. Plugins a repo's own `.claude/settings.json` enables load alongside
your rigs.

`rig setup` opens the rig editor: your rigs on the left, from `base` at the
top to `full` at the bottom, and the selected rig's plugins on the right. Move
with the arrow keys or the mouse, and toggle a plugin with space or a click.
`base` and `full` are built in: they can't be renamed or deleted, and `full`
can't be edited. Every other rig shows as two boxes, `base` + the rig: toggle
a plugin in the `base` box and it moves down into the rig. `>` does the same
for any plugin, and `<` moves the highlighted plugin onto `base`. The arrow
keys run from one box into the next. A
★ marks the default rigs, the ones a launch adds when it names none, and the
bottom of the rigs pane shows what a plain `claude` launches.

The first launch at a terminal with no rigs opens the editor before starting
Claude Code, with a **base** rig holding the plugins your settings enable. Turn
off the ones not every session needs. Each group of installed plugins that no
rig names shows as a draft, whether your settings turn it on or off: press `s`
on a draft to name it and save it as a rig. If your settings file separates its
`enabledPlugins` entries with blank lines, each group becomes a draft, and the
plugins it doesn't list are grouped by marketplace; otherwise each marketplace
is a draft.

| Key | Does |
| --- | --- |
| `space`, click | toggle the highlighted plugin in the selected rig; in the `base` box, move it into the selected rig |
| `tab` | move between the rigs and the plugins |
| `n` | new rig |
| `F2`, double-click | rename the selected rig |
| `d` | add the selected rig to the defaults, or take it out |
| `>` | put the highlighted plugin in the selected rig, taking it off `base` |
| `<` | put the highlighted plugin on `base`, taking it out of the selected rig |
| `x` | delete the selected rig, or dismiss the selected draft for good; `base` and `full` stay |
| `s` | save to `~/.rig/rigs.yml`; on a draft, name it and save it as a rig |
| `q` | quit; with unsaved changes, asks first: `q` saves and quits, `d` discards, `escape` goes back |

A rig names plugins as `<plugin>@<marketplace>`. When a rig names one that
isn't installed, the launch confirmation (below) lists it, and launching
installs it first. With nobody at a terminal to confirm, the launch is refused.

Everything rig doesn't recognize goes to Claude Code unchanged. Claude Code's
own subcommands (`claude plugin list`, `claude mcp`) run without a rig.

## Pins

A pin is a local checkout of a plugin that stands in for its installed copy, so
your edits take effect in real sessions before a marketplace release.

```bash
rig pin ~/src/acme-widget      # pin a checkout by path
rig pin acme-widget            # or by name, found among your local clones
rig pin                        # list the pins and how long each has been pinned
rig unpin acme-widget
```

`claude plugin pin` and `claude plugin unpin` work the same way.

Pinning by name looks the plugin up in your known marketplaces and expects its
source repo cloned under a folder you name per host in `~/.rig/rigs.yml`:

```yaml
clones:
  github.com: ~/src/github
```

At launch, a pin loads when the rig includes its plugin. A pin the rig doesn't
include is offered on the launch confirmation, unselected, and left out with
nobody at a terminal. Starting inside a pinned checkout offers that pin
selected, so you can leave it out: a plugin loaded into its own checkout
reviews edits to itself.

When a loaded pin's checkout holds the folder you start in, or sits inside it,
rig sets `CLAUDE_CODE_AUTO_MODE_SERVER=0` for that session, since auto mode
refuses edits there otherwise
([anthropics/claude-code#95982](https://github.com/anthropics/claude-code/issues/95982)).
A value you set yourself wins.

## Switching rigs mid-session

```text
/rig:switch web infra
```

A session can't change its plugins while it runs, so the switch happens across
a restart that keeps the conversation: `/rig:switch` records the rigs you name,
you type `/exit`, and rig relaunches the same conversation with the base rig
and those rigs. The launch confirmation opens first when the new rigs leave
pins to choose. The sandbox stays as the session had it; other Claude Code
arguments from the first launch don't carry over. `/rig:switch` with no rig
lists the rigs, marking the ones the session uses.

rig stays running while Claude Code does, which is how it sees the exit. A
session started without rig, or with nobody at a terminal, can't be relaunched
this way; the switch prints the `rig use <rig>... --resume <id>` command to run
after you exit.

## Sandbox

```bash
claude --sandbox         # this launch only
```

The sandbox runs Bash commands in Claude Code's sandbox, fails the launch when
the sandbox isn't available, and allows no unsandboxed commands.

## What a launch shows

When a launch has something to decide (a plugin to install, or a pin the rigs
don't settle), rig opens one launch confirmation first. The top lists the rigs:
add or take one away with space, and the plugins below follow, each naming the
rig it comes from and marking the ones that load from a pin or install at
launch. Under them are the pins left to choose; toggle them with space. `enter`
launches, `q` cancels. A launch with nothing to decide skips it.

Before Claude Code starts, rig prints the rigs, the pins, and the sandbox
state:

```text
rig: base + web, 9 plugins
pins: acme-widget  ~/src/acme-widget  (pinned 3 days ago)
sandbox: off
```

`rig --help` lists every command.
