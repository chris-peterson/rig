# Supported tools

rig launches two coding agents. **Claude Code** is the one it was built for and
the default. **Grok Build** gets the same rigs, folder rules, picker, and pins,
with the differences below.

| Tool | Launch | Tested with |
| --- | --- | --- |
| Claude Code | `claude`, or `rig` | Claude Code 2.1.329 |
| Grok Build | `grok`, or `rig grok` | grok 1.0.92 |

Each launch runs one tool. Your rigs, `~/.rig/rigs.yml`, and your pins are the
same for both.

## What each tool gets

| | Claude Code | Grok Build |
| --- | --- | --- |
| Rigs, `base`, `full`, `none` | ✓ | ✓ |
| Folder rules | ✓ | ✓ |
| The `--select` picker and `rig setup` | ✓ | ✓ |
| Pins | ✓ | ✓ |
| Installs a missing rig plugin at launch | ✓ | ✓, through Claude Code |
| `/rig` switching mid-session | ✓ | – |
| Plugins from the tool's own marketplaces | ✓ | – |

## Grok Build

```bash
grok                        # base plus your default rigs, in Grok Build
grok use web infra          # base plus both
grok --select               # pick on the graph, then launch
rig grok -p "fix the bug"   # the same through rig; grok's own options pass through
```

`/rig:install-rig` makes `grok` run `rig grok` in new shells when grok is on
your PATH, as it does for `claude`. Grok's own commands (`grok plugin list`,
`grok inspect`) run unchanged, with no rig.

**Plugins come from Claude Code.** Grok Build finds the plugins Claude Code
installed and loads them by name, so a rig's `anchor@acme` is grok's `anchor`.
A plugin a rig names that isn't installed is installed with
`claude plugin install`, so Claude Code needs to be on your PATH too. Plugins
you installed through grok's own marketplace aren't part of any rig.

**Not every plugin loads in grok.** Grok reads Claude Code's plugin format, but
it skips some plugins without saying so. Before grok starts, rig asks it which
of the launch's plugins it loaded, and names the ones it didn't:

```text
rig: base + web, 9 plugins
tool: Grok Build
not loaded by grok, which doesn't find it: ClaudeWatch
```

Check that line before relying on a plugin's hooks, guardrails especially.

**Each launch has a grok home of its own.** Grok has no way to choose plugins
for one session: its only switch is `[plugins]` in `~/.grok/config.toml`, which
every grok session shares. So rig never writes that table. It starts each grok
launch with a grok home of its own, under `~/.rig/grok/`, that links everything
in `~/.grok` except two things:

- **`config.toml`** is a copy of yours whose `[plugins]` table turns on the
  launch's plugins and nothing else. Your `paths`, `enabled`, and `disabled`
  entries don't apply to a rig launch.
- **`plugins/`** links your grok plugins folder's entries, plus each pin's
  checkout under its plugin's name, standing in for the installed copy.

Two grok sessions on different rigs run side by side without touching each
other's plugins.

The launch's grok home is `~/.rig/grok/1`, or the next number up while another
grok launch holds it, so a pinned plugin's scripts keep the same path from one
launch to the next. An *Always allow* you give one of them in grok goes on
applying, as grok's grants name the command's path.

When grok exits, rig carries back what the session wrote. A setting changed
with `/settings` goes into your `config.toml`, which keeps your own `[plugins]`
table. A file grok created or replaced, such as a refreshed sign-in, goes back
into `~/.grok`. If your `config.toml` changed while the session ran, rig leaves
it alone and saves the session's settings beside it as
`config.toml.rig-<number>`, naming both.

**What doesn't apply to grok:**

- `/rig` mid-session switching runs on Claude Code's own extension points.
  To change rigs in grok, exit and relaunch: `grok use infra --resume <id>`.
- rig doesn't touch Claude Code's settings for a grok launch: the plugins
  `~/.claude/settings.json` enables stay as they are.
- `--sandbox` is grok's own option, `--sandbox <profile>`, and passes to grok
  unchanged.
- Tab completion after `grok` is grok's own, so it doesn't offer your rigs.
