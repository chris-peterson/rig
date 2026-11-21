# Changelog

## Unreleased

- `r` in `rig setup` opens the selected rig's rules in your editor: git's
  editor, or `$VISUAL`, `$EDITOR`, or `vi` without git. Saving and closing
  makes them unsaved changes, and the rig's box shows them. Rules that don't
  hold are refused with the reason, and the next `r` opens what you wrote.
- Tab after `claude --resume` or `-r` (and `rig use … --resume`) offers the
  current folder's sessions, newest first, each with its `/rename` title or the
  title Claude Code gave it. Run `/rig:install-rig` again to pick it up.
- Escape in the picker or the rig editor closes the message on show instead of
  cancelling. With no message showing, escape still cancels the picker.

## 0.3.0

- The `/rig` pane fits a sidebar: it names plugins without their marketplace
  (unless two share a name), staggers the rig names over two or more rows
  when they don't fit on one, and docks only as wide as that needs. The toast for
  a pin holding your folder ends in ✕; a click on it closes it.
- The `/rig` pane shows what you change against what the session loads: rigs
  and plugins coming in turn green, ones going turn red, and a line under the
  summary lists the plugins each way.
- `l` in the `/rig` pane with nothing changed closes the pane and keeps the
  session. It used to exit Claude Code without recording a switch, so rig
  ended instead of relaunching.
- `rig` with no arguments opens the `--select` picker at a terminal instead of
  printing its usage. `claude` with no arguments still launches the default
  rigs straight away.
- `rig pin` with no arguments pins the checkout you're in, and `rig unpin` with
  none unpins it. Listing the pins moved to `rig pins`, which indents them.
- A pin that loads while you launch inside its checkout, or in a folder above
  it, shows ❗ in place of 📌 in the picker, since the session runs on the
  files it edits. Its dialog warns about that and offers Skip for this launch,
  which loads the installed copy this once and leaves the pin in place.
- The picker's 🚀 counts down to launch: five `>` chevrons light toward it,
  one every half second, twice as fast under the pointer.
- A click anywhere in a rig's column toggles the rig, not only a click on its
  name; a click on a plugin's name still toggles the plugin.
- 📌 sits in front of a pinned plugin's name, in a margin of its own in the
  graph, as it does in `rig pins`.
- rig refuses a command it doesn't know: `rig --graph` or `rig lsit` stops
  with what to type instead, rather than opening the picker and handing
  Claude Code an option it refuses. A one-word prompt goes after `--`:
  `rig -- hi`. `claude hi` still starts a session with that prompt.
- The picker drops the line of instructions under the graph; the footer's key
  bindings say the same.
- The picker's legend sits in the graph's top border, so it no longer pushes
  the graph past the window's width, and the vertical scrollbar is thinner.

- A rig can carry `rules` that make it a default wherever they match, so a
  plain `claude` loads what the folder needs: `path` for where you launch
  (`~/src/acme/`, or `*infra*/` for any folder with infra in its name) and
  `exists` for files in the repo (`**/*.tf`, `SPEC.md`). The launch line says
  which rule added each rig, and `rig list` shows the defaults for the current
  folder. Rules add to the `default` list, which still applies everywhere.
- `/rig` replaces `/rig:switch` and opens the `--select` picker inside the
  session, set to what the session loads now: toggle rigs, single plugins, and
  pins, then `l` switches. Claude Code exits on its own and rig relaunches the
  conversation with what you picked, so there's no `/exit` to type. A toast
  names the pin that holds the current folder. `/rig <rig>...` switches
  straight to the rigs you name. This needs a Claude Code with function hooks
  (mods).
- The launch confirmation is gone. A launch with a pin to choose or a plugin
  to install opens the `--select` picker instead, with a toast saying why and
  the cursor on that pin. `l` launches, where `enter` used to.

## 0.2.0

- Closing the terminal under the `--select` picker, the launch confirmation,
  or the rig editor now ends rig. Started with SIGHUP ignored, it used to keep
  running with no terminal, using a full CPU core until killed.
- `--sandbox` launches run sandboxed Bash commands without a permission prompt
  again. Claude Code 2.1.325 started prompting for them by default; rig now
  sets `sandbox.autoAllowBashIfSandboxed` to keep the old behavior.
- With beacon installed, a session rig launches at a terminal shows its rigs
  on the pane badge, `web ✦ docs`, and a switch updates it when the
  conversation relaunches.
- After `/rig:switch` and `/exit`, the relaunched conversation opens with a
  turn saying the switch is done and what the new rigs bring, instead of
  coming back to the old "type `/exit`" message.
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
