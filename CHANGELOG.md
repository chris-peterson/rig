# Changelog

## Unreleased

- `claude --select` (or `rig use <rig>... --select`) opens a picker before the
  launch: the `rig list --graph` table with `full` added. One cursor moves over
  the rig names and plugin rows with the arrow keys and tab, and space, enter,
  or a click toggles what it's on: a rig (`full` goes alone, and `base` always
  loads) or a single plugin. A rig you've taken a plugin from, or picked one
  of, shows a ◐ under its name where a loaded one shows a ✓, and the launch
  summary names those plugins: `base + web + x@m - a@m`. `e` opens the rig
  editor and comes back; `l`, Shift+Enter, or the 🚀 at the end of the footer
  launches, and `q` cancels.
- Toggling a pinned plugin's row in the picker shows the pin's checkout, its
  age, and whether it loads, with Unpin as the default and buttons to leave
  the plugin out of the launch or put it in, and to load the checkout or skip
  it; escape or the ✕ closes it.
- `rig use none` launches stock Claude Code with every plugin off, the base
  rig's and your pins included. It says what you'll go without and asks first,
  and refuses without a terminal to ask at.
- A launch with `full` says `all 40 plugins` rather than `base + full`.
- A 📌 marks pinned plugins in the launch summary, `rig pin`, `rig list`, the
  graph, the launch confirmation, and the rig editor, in place of the words
  "pinned" and "pins:".
- Tab completion for `rig use` offers the rigs again after a comma
  (`rig use web,<tab>`) and after comma-joined names, leaves out the rigs
  already named and `base`, and offers `--select` alongside `--sandbox`.

## 0.1.0

- `claude` launches Claude Code with the base rig and your default rigs, and
  `rig use web infra` with the base rig and the rigs you name (`web,infra`
  works too); `full` is every installed plugin. Those plugins are enabled for
  that session. Each launch turns off the plugins your
  `~/.claude/settings.json` enables, so `/plugin enable` works mid-session and
  lasts until the next launch. `rig` on its own prints its usage.
- Arguments rig doesn't recognize go to Claude Code unchanged, so prompts and
  flags work as they do with `claude`. Claude Code's own subcommands
  (`rig plugin list`, `rig mcp`) run without a rig.
- `rig setup` opens a full-screen rig editor, driven by the arrow keys, space,
  and the mouse: pick each rig's plugins, name it, and mark the default rigs.
  An interactive launch with no rigs opens it first, starting a base rig from
  the plugins your settings enable and suggesting draft rigs for the rest.
- `rig pin <path|name>` makes a local plugin checkout stand in for the
  installed copy in rigs that use it. `rig unpin` undoes it, and a bare
  `rig pin` lists the pins. A launch inside a pinned checkout, or from a
  folder that holds one, sets `CLAUDE_CODE_AUTO_MODE_SERVER=0`, since auto
  mode refuses edits there otherwise
  ([anthropics/claude-code#95982](https://github.com/anthropics/claude-code/issues/95982)).
- `rig --sandbox` runs Bash in Claude Code's sandbox with no unsandboxed
  commands.
- A launch with something to decide opens one confirmation screen: the rigs,
  which you can add to or take from, the plugins they load, marking what
  installs at launch, and the pins they leave to choose, each preselected as
  the launch would load it. `enter` launches, `q` cancels.
- `/rig:switch <rig>...` moves a session to other rigs: type `/exit` after it,
  and rig relaunches the same conversation with the new rigs' plugins.
- `/rig:install-rig` puts `rig` on your PATH with zsh tab completion and makes
  `claude` run rig, leaving a `claude` shell function of your own alone. A
  session start tells you when an update left the installed `rig` behind.
- `rig doctor` checks what a new zsh sees (the `rig` on PATH, the `claude`
  function, tab completion for both), prints the fix for each failed check,
  then runs Claude Code's own doctor. `claude doctor` does the same.
