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
opens the `--select` picker on them, so you can change what loads before the
launch; with no rigs yet, first-run setup comes first.

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
rig use web infra           # base plus both; `web,infra` and "web infra" work too
rig use full                # every installed plugin
rig use none                # stock Claude Code, no plugins at all; asks first
claude --select             # pick the rigs on the graph, then launch
claude "fix the bug"        # a prompt, with the default rigs
rig list                    # every rig and its plugins
rig list --graph            # a table of plugins against rigs
rig list --json             # the same, for scripts
```

`none` is for the times you need Claude Code as it ships: every plugin is off
for that session, the base rig's and your pins included. Since that also drops
the hooks and guardrails you're used to, rig says so and asks before it
launches, and refuses with nobody at a terminal to answer.

`--select` opens a picker before the launch: the `rig list --graph` table with
`full` added, the rigs across the top and their plugins down the side, a 📌 in
front of each pinned plugin. One cursor sits on a rig's name or a plugin's row;
the arrow keys and tab move it, and space or enter toggles what it's on. A click
anywhere in a rig's column toggles the rig, and a click on a plugin's name
toggles the plugin.
A ✓ under a rig's name means the launch loads it (the legend in the graph's
top border says so), and the plugins the launch
loads stay bright and the rest dim. With `full` chosen the summary reads
`all 40 plugins`. `base` always loads, so it can't be toggled, and `full` holds
every other rig's plugins, so choosing it takes the others away and choosing
another rig takes `full` away.

Toggling a plugin's row launches with one plugin more or less: it comes out of
the launch even when a rig holds it, or goes in when none does. A rig the
launch then loads only part of shows a yellow ◐, which the legend explains while
one does; toggling the rig brings it back in whole. The launch summary
names those plugins after the rigs:
`rig: base + web + playwright@acme - sonar@acme`.

Toggling a pinned plugin's row opens its pin instead: its checkout, its age,
and whether it loads. `enter` (or Unpin) unpins it for this launch and the ones
after; the other buttons take the plugin out of this launch or put it in, and
load the checkout or skip it for the installed copy. Escape or the ✕ closes it.

`e` opens the rig editor and brings you back to the picker when you quit it.
`l`, Shift+Enter, or a click on the 🚀 at
the right end of the footer launches; `q` cancels. Escape cancels too, unless a
message is showing: then the first escape just closes the message. `TEXTUAL_ANIMATIONS=none`
holds the 🚀's exhaust still. `rig use web --select` starts the picker with
`web` chosen.

Tab completion offers the rigs after `rig use`, and again after each space or
comma, leaving out the ones already named. After `--resume` or `-r` it offers
the sessions you've had in the current folder, newest first, each with its
`/rename` title or the title Claude Code gave it.

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
| `r` | edit the selected rig's [rules](#default-rigs-by-folder) in your editor |
| `x` | delete the selected rig, or dismiss the selected draft for good; `base` and `full` stay |
| `s` | save to `~/.rig/rigs.yml`; on a draft, name it and save it as a rig |
| `q` | quit; with unsaved changes, asks first: `q` saves and quits, `d` discards, `escape` goes back |
| `escape` | close the message on show |

A rig names plugins as `<plugin>@<marketplace>`. When a rig names one that
isn't installed, the picker opens first (below) and marks it, and launching
installs it first. With nobody at a terminal to confirm, the launch is refused.

Everything rig doesn't recognize goes to Claude Code unchanged. Claude Code's
own subcommands (`claude plugin list`, `claude mcp`) run without a rig.

### Default rigs by folder

A rig can carry rules that make it a default wherever they match, so a plain
`claude` picks up what the folder needs without your naming it. A rig loads
when any of its rules matches, and a rule matches when each condition it gives
does:

```yaml
default: []                       # defaults everywhere; rules add to these
rigs:
  work:
    plugins: [...]
    rules:
      - path: ~/src/acme/         # this folder and everything under it
  infra:
    plugins: [...]
    rules:
      - path: "*infra*/"          # any folder with infra in its name, at any depth
      - exists: ["**/*.tf"]       # or a repo holding Terraform
  spec:
    plugins: [...]
    rules:
      - exists: SPEC.md           # at the repo root
  release:
    plugins: [...]
    rules:
      - path: ~/src/acme/         # both conditions have to match
        exists: [.gitlab-ci.yml]
```

- **`path`** matches the folder you launch in the way git's
  `includeIf "gitdir/i:"` does. Case doesn't matter, and `~/` is your home
  folder. A pattern that doesn't start with `/` or `~/` matches at any depth,
  `*` stays within one folder name, and `**` spans folders. A trailing `/`
  matches that folder and everything under it.
- **`exists`** takes one glob or a list of them, matched from the root of the
  repo you launch in, the way GitLab CI's `rules:exists` matches. It counts
  tracked files and untracked ones git doesn't ignore. Outside a repo, it
  looks at the first 10,000 files under the folder.

The launch says which rule added each rig:

```text
rig: base + work + infra, 21 plugins
by rule: work (path ~/src/acme/), infra (exists **/*.tf)
```

Naming rigs (`rig use web`) skips the rules. `rig list` shows which rigs are
defaults in the current folder and why, `rig list --graph` and the `--select`
picker star them.

To edit a rig's rules, select it in `rig setup` and press `r`. Its rules open as
YAML in git's editor (`git var GIT_EDITOR`), or, without git, in `$VISUAL`,
`$EDITOR`, or `vi`. When you save and close, they become unsaved changes, and
the rig's box shows them; `s` writes them to `~/.rig/rigs.yml`. If what you wrote
isn't valid, the editor says why and keeps the old rules, and the next `r` opens
what you wrote so you can fix it.

## Pins

A pin is a local checkout of a plugin that stands in for its installed copy, so
your edits take effect in real sessions before a marketplace release.

```bash
rig pin ~/src/acme-widget      # pin a checkout by path
rig pin acme-widget            # or by name, found among your local clones
rig pin                        # or the checkout you're in
rig pins                       # list the pins and how long each has been pinned
rig unpin acme-widget          # bare `rig unpin` unpins the checkout you're in
```

`claude plugin pin` and `claude plugin unpin` work the same way.

Pinning by name looks the plugin up in your known marketplaces and expects its
source repo cloned under a folder you name per host in `~/.rig/rigs.yml`:

```yaml
clones:
  github.com: ~/src/github
```

At launch, a pin loads when the rig includes its plugin. A pin the rig doesn't
include is offered in the picker, not loading, and left out with nobody at a
terminal. A pin with no installed copy is different: it stands in for nothing,
so pinning it can only mean loading it. That's a plugin you're writing, one no
marketplace lists yet. It loads in every launch without asking, offered selected
in the picker in case you want to leave it out, and the launch summary marks it
`no installed copy`. Starting inside a pinned checkout offers that pin selected. Starting
inside one, or in a folder above it, marks a loading pin ❗ in place of 📌: the
session runs on the files it edits, which can give unpredictable results. Its
pin's dialog says so and can skip the checkout for that launch only, leaving
the pin in place.

When a loaded pin's checkout holds the folder you start in, or sits inside it,
rig sets `CLAUDE_CODE_AUTO_MODE_SERVER=0` for that session, since auto mode
refuses edits there otherwise
([anthropics/claude-code#95982](https://github.com/anthropics/claude-code/issues/95982)).
A value you set yourself wins. This leans on auto mode's billed classifier
fallback, which Claude Code 2.1.327 announced an upcoming release removes; once
it's gone, edits in a pinned checkout are asked about or denied until #95982 is
fixed.

## Switching rigs mid-session

```text
/rig
```

`/rig` opens the picker inside the session: the same graph as
`--select`, set to what the session loads now, with the same keys for rigs,
plugins, and pins. A toast names the pin that holds the folder you're in, if
one does, and whether its checkout loads. `l` switches and `escape` or `q`
closes it without one. `/rig web infra` skips the picker and switches
to the rigs you name.

A session can't change its plugins while it runs, so the switch happens across
a restart that keeps the conversation: rig records the switch, Claude Code
exits on its own, and rig relaunches the same conversation with what you
chose. A switch from the picker doesn't ask again. One that names rigs opens
the picker first when they leave pins to choose. The sandbox stays as the
session had it, and so do the options you passed to Claude Code, such as
`--plugin-dir` or `--model`. The prompt doesn't carry over, and neither does an
option that picks or starts a conversation (`--continue`, `--resume`,
`--session-id`, `--fork-session`, `--from-pr`, `--teleport`, `--worktree`),
since the switch resumes the conversation itself.

rig stays running while Claude Code does, which is how it sees the exit. A
session started without rig, or with nobody at a terminal, can't be relaunched
this way; the switch prints the `rig use <rig>... --resume <id>` command to run
after you exit.

## Sandbox

```bash
claude --sandbox         # this launch only
```

The sandbox runs Bash commands in Claude Code's sandbox without a permission
prompt for each one, fails the launch when the sandbox isn't available, and
allows no unsandboxed commands. Claude Code 2.1.325 stopped running sandboxed
commands unprompted by default, so rig sets `sandbox.autoAllowBashIfSandboxed`
to keep them that way.

## What a launch shows

When a launch has something to decide (a plugin to install, or a pin the rigs
don't settle), rig opens the `--select` picker first, with a toast saying why:
the pin that holds this folder and whether its checkout loads, a pin the rigs
leave out that has an installed copy, the plugins that install at launch. The cursor starts on that pin's
row, and `enter` there opens its choices. `l` launches, `q` cancels. A launch
with nothing to decide skips the picker.

Before Claude Code starts, rig prints the rigs, the pins, and the sandbox
state:

```text
rig: base + web, 9 plugins
📌 acme-widget  ~/src/acme-widget  (3 days ago)
sandbox: off
```

`rig --help` lists every command.
