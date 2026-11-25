# Pins

Developing a plugin usually means a loop of edit, publish, update, restart, or
a `--plugin-dir` you have to remember on every launch. A **pin** removes the
loop: it points rig at your local checkout of a plugin, and that checkout
stands in for the installed copy in every launch whose rigs include the plugin.
Your edits take effect in the next session you start, with no marketplace
release.

```bash
rig pin ~/src/acme/widget      # pin a checkout by path
rig pin widget                 # or by name, found among your local clones
rig pin                        # or the checkout you're in
rig pins                       # list the pins and how long each has been pinned
rig unpin widget               # back to the installed copy
rig unpin                      # unpin the checkout you're in
```

`claude plugin pin` and `claude plugin unpin` work the same way. The launch
summary lists the pins that load, with how long each has been pinned, so a pin
you forgot about doesn't go unnoticed:

```text
rig: base + web, 9 plugins
📌 widget  ~/src/acme/widget  (3 days ago)
```

## When a pin loads

A pin follows its plugin: it loads when the launch's rigs include the plugin,
and stays out when they don't. The picker shows a pin the rigs leave out, not
loading, so you can bring it in for one launch. A pin whose checkout holds the
folder you start in loads either way.

A pin with no installed copy is different. It stands in for nothing, so pinning
it can only mean loading it: that's a plugin you're writing that no
marketplace lists yet. It loads in every launch, offered selected in the picker
in case you want to leave it out, and the launch summary marks it
`no installed copy`.

## Pinning from the picker

In the picker, `p` pins the plugin on the cursor's row. rig finds the checkout
the way `rig pin <name>` does, without asking for a path; when it finds none,
it opens a folder browser over your home folder. Move to the plugin's folder
and press `p` or *Pin this folder*. A folder holding no plugin manifest, or
another plugin's, is refused with the reason. A plugin in a subfolder of its
repo is pinned at that subfolder.

Toggling a pinned plugin's row opens its pin: its checkout, its age, and
whether it loads. `enter` (or *Unpin*) unpins it for this launch and the ones
after; the other buttons take the plugin out of this launch or put it in, and
load the checkout or use the installed copy.

## Pinning by name

`rig pin <name>` looks the plugin up in your known marketplaces and expects its
source repo cloned at `<folder>/<owner>/<repo>`, under a folder you name per
host in `~/.rig/rigs.yml`:

```yaml
clones:
  github.com: ~/src/github
```

Without a `clones:` entry, rig learns the folder from your pins: one pin at
`~/src/github/acme/widget`, whose `origin` is `github.com/acme/widget`, puts
github.com's clones in `~/src/github`, so every plugin cloned beside it pins by
name. When a name doesn't resolve, rig says why and you pin it by path. Tab
after `rig pin` offers the names that resolve either way.

## Working inside a pinned checkout

Starting a session inside a pinned checkout, or in a folder above one, means
the session edits the files it's running on. That works, but it can give
unpredictable results, so the launch stops at the picker first, even a plain
`claude`. The picker marks that pin ❗ in place of 📌, and its dialog can skip
the checkout for that launch only, leaving the pin in place; `g` launches with
it as it is.

When a loaded pin's checkout holds the folder you start in, or sits inside it,
rig sets `CLAUDE_CODE_AUTO_MODE_SERVER=0` for that session, since auto mode
refuses edits there otherwise
([anthropics/claude-code#95982](https://github.com/anthropics/claude-code/issues/95982)).
A value you set yourself wins. This leans on auto mode's billed classifier
fallback, which Claude Code 2.1.327 announced an upcoming release removes; once
it's gone, edits in a pinned checkout are asked about or denied until #95982 is
fixed.
