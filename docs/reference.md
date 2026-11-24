# Reference

## Commands

| Command | Does |
| --- | --- |
| `claude [<args>]` | launch with the base rig and the default rigs; installed by `/rig:install-rig` to run `rig claude` |
| `rig` | open the picker, then launch; first-run setup first when there are no rigs |
| `rig use <rig>... [<args>]` | launch with the base rig and the named rigs, separated by spaces or commas; `full` is every installed plugin, `none` is stock Claude Code (asks first) |
| `rig list [--graph\|--json]` | list the rigs with their plugins, marking the defaults in this folder and the rule behind each; `--graph` tabulates plugins against rigs |
| `rig setup` | open the rig editor |
| `rig pin [<path\|name>...]` | use a local checkout in place of the installed plugin; with no arguments, the checkout you're in |
| `rig pins` | list the pins and how long each has been pinned |
| `rig unpin [<path\|name>...]` | stop using a pinned checkout; with no arguments, the one you're in |
| `rig doctor` | check the `rig` command, the `claude` function, and tab completion in a new zsh, then run Claude Code's doctor |
| `rig install-cli` | what `/rig:install-rig` runs: put `rig` on PATH with tab completion, and make `claude` run rig |
| `/rig [<rig>...]` | in a session: open the picker and switch, or switch straight to the named rigs |

| Option | Does |
| --- | --- |
| `--select` | with any launch: open the picker first |
| `--version` | print rig's version |
| `-h`, `--help` | list every command and option |

Anything else goes to Claude Code. Its subcommands run unchanged, and its
options and a prompt start a session with the default rigs. rig refuses a word
that is neither, so put a one-word prompt after `--`. `claude plugin pin` and
`claude plugin unpin` are the same as `rig pin` and `rig unpin`.

Tab completion offers the rigs after `rig use`, the pinnable names after
`rig pin`, and after `--resume` or `-r`, the sessions you've had in the current
folder, newest first, each with its title.

## The picker

`rig`, `--select`, and `/rig` open the picker.

| Key | Does |
| --- | --- |
| arrows, `h` `j` `k` `l`, `tab` | move the cursor between the rigs' names and the plugins' rows |
| `space`, `enter`, click | toggle what the cursor is on: a rig, or one plugin; on a pinned plugin, open its pin |
| click in a rig's column | toggle the rig |
| `p` | pin the plugin on the cursor's row, or open its pin |
| `e` | open the rig editor, then come back |
| `g`, `shift+enter`, the 🚀 | launch, or in `/rig`, switch |
| `q` | cancel |
| `escape` | close the message on show, else cancel |

| Mark | Means |
| --- | --- |
| ✓ under a rig | the launch loads the rig |
| ◐ under a rig | the launch loads part of the rig, after you toggled one of its plugins |
| ★ before a rig | a default rig here, by `default:` or a rule |
| 📌 before a plugin | pinned; its checkout loads in place of the installed copy |
| ❗ before a plugin | pinned, and you're starting inside its checkout |

`base` always loads, so it can't be toggled. `full` holds every other rig's
plugins, so choosing it takes the others away, and choosing another rig takes
`full` away. When the launch has something to decide (a plugin to install, or a
pin the rigs don't settle), a toast says what and the cursor starts on its row.
`TEXTUAL_ANIMATIONS=none` holds the 🚀's exhaust still.

## rig setup

| Key | Does |
| --- | --- |
| arrows, `j` `k`, click | move |
| `space`, click | toggle the highlighted plugin in the selected rig; in the `base` box, move it into the selected rig |
| `tab` | move between the rigs and the plugins |
| `n` | new rig |
| `F2`, double-click | rename the selected rig |
| `d` | add the selected rig to the defaults, or take it out |
| `>` | put the highlighted plugin in the selected rig, taking it off `base` |
| `<` | put the highlighted plugin on `base`, taking it out of the selected rig |
| `r` | edit the selected rig's [rules](/rigs#rigs-that-pick-themselves-folder-rules) in your editor |
| `x` | delete the selected rig, or dismiss the selected draft for good; `base` and `full` stay |
| `s` | save to `~/.rig/rigs.yml`; on a draft, name it and save it as a rig |
| `q` | quit; with unsaved changes, asks first: `q` saves and quits, `d` discards, `escape` goes back |
| `escape` | close the message on show |

`base` and `full` are built in: they can't be renamed or deleted, and `full`
can't be edited. When `~/.rig/rigs.yml` changes on disk, the editor takes up
the change; if the editor has unsaved changes of its own, it keeps them and
warns that `s` would write over the file's.

## ~/.rig/rigs.yml

`rig setup` writes this file, and you can edit it by hand.

```yaml
default: [web]                    # rigs a plain launch adds to base, everywhere
clones:                           # where `rig pin <name>` looks, per host
  github.com: ~/src/github
rigs:
  base:                           # required; every launch loads it
    plugins: [anchor@acme, beacon@acme]
  web:
    plugins: [frontend-design@acme, playwright@acme]
  infra:
    plugins: [terraform@acme]
    rules:                        # a default wherever any rule matches
      - path: "*infra*/"
      - exists: ["**/*.tf"]
dismissed: [notebooks@acme]       # drafts rig setup no longer suggests
```

A rig holds only `plugins` and `rules`. `full` and `none` are reserved names.
Pins live beside it, in `~/.rig/pins.yml`; change them with `rig pin` and
`rig unpin`.

## What a launch prints

Before Claude Code starts, rig prints the rigs, how many plugins they load, the
rule behind each default rig, and the pins that load:

```text
rig: base + web + infra, 12 plugins
by rule: infra (exists **/*.tf)
📌 widget  ~/src/acme/widget  (3 days ago)
```
