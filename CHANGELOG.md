# Changelog

## Unreleased

- `rig` launches Claude Code with the default rig, and `rig use <name>` with a
  named one: the rig's plugins, and the plugins of the rigs it extends, are the
  only ones enabled for that session. Your Claude Code settings are unchanged.
- Arguments rig doesn't recognize go to Claude Code unchanged, so prompts and
  flags work as they do with `claude`. Claude Code's own subcommands
  (`rig plugin list`, `rig mcp`) run without a rig.
- `rig setup` builds the base rig from the plugins your settings enable, then
  suggests named rigs for the rest. An interactive launch with no rigs runs it
  first.
- `rig pin <path|name>` makes a local plugin checkout stand in for the
  installed copy in rigs that use it. `rig unpin` undoes it, and a bare
  `rig pin` lists the pins.
- `rig --sandbox`, or `sandbox: true` on a rig, runs Bash in Claude Code's
  sandbox with no unsandboxed commands.
- A rig that names a plugin you haven't installed offers to install it.
- `/rig:install-rig` puts `rig` on your PATH with zsh tab completion, and
  `--claude` makes `claude` run rig. A session start tells you when an update
  left the installed `rig` behind.
