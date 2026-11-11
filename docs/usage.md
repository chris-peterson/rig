# Using rig

## Install

Install the plugin, then run its bootstrap from a Claude Code prompt:

```text
/rig:install-rig
```

That puts `rig` on your PATH at `~/.local/bin/rig`, with zsh tab completion.
rig runs through [uv](https://docs.astral.sh/uv/), so uv must be on your PATH
too. When a plugin update leaves the `rig` on your PATH behind, a session start
tells you to run `/rig:install-rig` again.

To have `claude` itself run rig, so the habit you already have picks up your
rigs and pins:

```text
/rig:install-rig --claude
```

If another shell function already defines `claude` (a wrapper of your own),
rig leaves it alone. Have that wrapper call `rig "$@"` where it called
`claude`.

## Rigs

A rig is a named list of plugins. A launch enables exactly that list, plus the
pins below, and turns every other plugin off for that session only. Your Claude
Code settings stay as they are.

The first launch at a terminal with no rigs runs setup: it lists the plugins
your Claude Code settings enable and asks which ones every session needs. Those
become the **base** rig, the default. Setup then suggests named rigs for the
rest, each extending the base. If your settings file separates its
`enabledPlugins` entries with blank lines, each group becomes a suggestion;
otherwise each marketplace does. Run `rig setup` again any time to revise.

```bash
rig                      # the default rig
rig use web              # the web rig: the base plus web's own plugins
rig "fix the bug"        # a prompt, with the default rig
rig list                 # every rig, its plugins, and what it extends
```

A rig names plugins as `<plugin>@<marketplace>`. When a rig names one that
isn't installed, rig offers to install it and launches only once you agree.
With nobody at a terminal to ask, the launch is refused.

Everything rig doesn't recognize goes to Claude Code unchanged. Claude Code's
own subcommands (`rig plugin list`, `rig mcp`, `rig doctor`) run as they would
under `claude`, without a rig.

## Pins

A pin is a local checkout of a plugin that stands in for its installed copy, so
your edits take effect in real sessions before a marketplace release.

```bash
rig pin ~/src/acme-widget      # pin a checkout by path
rig pin acme-widget            # or by name, found among your local clones
rig pin                        # list the pins and how long each has been pinned
rig unpin acme-widget
```

`claude plugin pin` and `claude plugin unpin` work the same way when `claude`
runs rig.

Pinning by name looks the plugin up in your known marketplaces and expects its
source repo cloned under a folder you name per host in `~/.rig/rigs.yml`:

```yaml
clones:
  github.com: ~/src/github
```

At launch, a pin loads when the rig includes its plugin. A pin the rig doesn't
include is asked about at a terminal, and left out otherwise. Starting inside a
pinned checkout asks whether to load that pin, since a plugin loaded into its
own checkout reviews edits to itself.

## Sandbox

```bash
rig --sandbox            # this launch only
```

Or turn it on for every launch of a rig:

```yaml
rigs:
  untrusted:
    extends: [base]
    sandbox: true
```

The sandbox runs Bash commands in Claude Code's sandbox, fails the launch when
the sandbox isn't available, and allows no unsandboxed commands. A rig that
extends a sandboxed rig is sandboxed too.

## What a launch shows

Before Claude Code starts, rig prints the rig, the pins, and the sandbox state:

```text
rig: web (extends base), 9 plugins
pins: acme-widget  ~/src/acme-widget  (pinned 3 days ago)
sandbox: off
```

`rig --help` lists every command.
