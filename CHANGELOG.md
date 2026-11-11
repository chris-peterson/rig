# Changelog

## Unreleased

- `claude` launches Claude Code with the default rig, and `rig use <name>` with
  a named one: the rig's plugins, and the plugins of the rigs it extends, are
  the only ones enabled for that session. Your Claude Code settings are
  unchanged. `rig` on its own prints its usage.
- Arguments rig doesn't recognize go to Claude Code unchanged, so prompts and
  flags work as they do with `claude`. Claude Code's own subcommands
  (`rig plugin list`, `rig mcp`) run without a rig.
- `rig setup` opens a full-screen rig editor, driven by the arrow keys, space,
  and the mouse: pick each rig's plugins, name it, choose the one rig it
  extends, and set the default. Every rig but the base rig extends one other, so every rig
  carries the base rig's plugins. An interactive launch with no
  rigs opens it first, starting a base rig from the plugins your settings
  enable and suggesting draft rigs for the rest.
- `rig pin <path|name>` makes a local plugin checkout stand in for the
  installed copy in rigs that use it. `rig unpin` undoes it, and a bare
  `rig pin` lists the pins. A launch inside a pinned checkout, or from a
  folder that holds one, sets `CLAUDE_CODE_AUTO_MODE_SERVER=0`, since auto
  mode refuses edits there otherwise
  ([anthropics/claude-code#95982](https://github.com/anthropics/claude-code/issues/95982)).
- `rig --sandbox` runs Bash in Claude Code's sandbox with no unsandboxed
  commands.
- A launch with something to decide opens one confirmation screen: the rig
  and its plugins, marking what installs at launch, then the pins the rig
  leaves to choose, each preselected as the launch would load it. `enter`
  launches, `escape` cancels.
- `/rig:switch <rig>` moves a session to another rig: type `/exit` after it,
  and rig relaunches the same conversation with the new rig's plugins.
- `/rig:install-rig` puts `rig` on your PATH with zsh tab completion and makes
  `claude` run rig, leaving a `claude` shell function of your own alone. A
  session start tells you when an update left the installed `rig` behind.
- `rig doctor` checks what a new zsh sees (the `rig` on PATH, the `claude`
  function, tab completion for both), prints the fix for each failed check,
  then runs Claude Code's own doctor. `claude doctor` does the same.
