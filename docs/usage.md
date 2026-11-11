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

`claude` with no arguments launches the default rig; `rig` with no arguments
prints its usage.

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

A rig is a named list of plugins. A launch enables exactly that list, plus the
pins below, and turns every other plugin off for that session only. Your Claude
Code settings stay as they are.

Every rig but the base rig extends one other rig, so every rig carries the
base rig's plugins.

`rig setup` opens the rig editor: your rigs on the left, as a tree rooted at
the base rig with each rig under the one it extends, and the selected rig's
plugins on the right. Move with the arrow
keys or the mouse, and toggle a plugin with space or a click. Plugins a rig
inherits show as locked, naming the rig they come from; change them on that
rig.

The first launch at a terminal with no rigs opens the editor before starting
Claude Code, with a **base** rig holding the plugins your settings enable. Turn
off the ones not every session needs. Each group of enabled plugins that no rig
loads shows as a draft under the base rig: press `s` on a draft to name it
and save it as a rig. If your settings file separates its `enabledPlugins`
entries with blank lines, each group becomes a draft; otherwise each
marketplace does.

| Key | Does |
| --- | --- |
| `space`, click | toggle the highlighted plugin in the selected rig |
| `tab` | move between the rigs and the plugins |
| `n` | new rig, extending the selected rig unless you choose another |
| double-click, `enter`, `e` | edit the selected rig's name and the rig it extends; on a draft, name it and save it as a rig |
| `d` | make the selected rig the default |
| `x` | delete the selected rig, unless it's the base rig, the default, or extended by another |
| `s` | save to `~/.rig/rigs.yml`; on a draft, name it and save it as a rig |
| `q` | quit; with unsaved changes, asks first: save (the default, `enter` or `s`) or discard (`d`) |

```bash
claude                   # the default rig
rig use web              # the web rig: the base plus web's own plugins
claude "fix the bug"     # a prompt, with the default rig
rig list                 # every rig, its plugins, and what it extends
```

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
/rig:switch web
```

A session can't change its plugins while it runs, so the switch happens across
a restart that keeps the conversation: `/rig:switch` records the rig you name,
you type `/exit`, and rig relaunches the same conversation with that rig. The
launch confirmation opens first when the new rig leaves pins to choose. The
sandbox stays as the session had it; other Claude Code arguments from the
first launch don't carry over. `/rig:switch` with no rig lists the rigs.

rig stays running while Claude Code does, which is how it sees the exit. A
session started without rig, or with nobody at a terminal, can't be relaunched
this way; the switch prints the `rig use <rig> --resume <id>` command to run
after you exit.

## Sandbox

```bash
claude --sandbox         # this launch only
```

The sandbox runs Bash commands in Claude Code's sandbox, fails the launch when
the sandbox isn't available, and allows no unsandboxed commands.

## What a launch shows

When a launch has something to decide (a plugin to install, or a pin the rig
doesn't settle), rig opens one launch confirmation first. The top shows the rig
you're launching and its plugins, read-only, marking the ones that load from a
pin or install at launch. Below it are the pins left to choose; toggle them
with space. `enter` launches, `escape` cancels. A launch with nothing to decide
skips it.

Before Claude Code starts, rig prints the rig, the pins, and the sandbox state:

```text
rig: web (extends base), 9 plugins
pins: acme-widget  ~/src/acme-widget  (pinned 3 days ago)
sandbox: off
```

`rig --help` lists every command.
