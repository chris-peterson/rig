# rig

A Claude Code plugin and CLI that launches Claude Code with a named set of
plugins (a rig), the local plugin checkouts you've pinned, and the sandbox when
a launch or a rig asks for it. What it does for a *user* lives on the docs site
(https://chris-peterson.github.io/rig); this file is for working on rig itself.

rig is spec-driven. `SPEC.md` is the requirement source of record and
`STATUS.md` its coverage ledger, both maintained with sextant
(`/sextant:spec-req`, `/sextant:spec-status`). A change to behavior updates the
requirement and the ledger in the same commit.

## Commands

```bash
just test             # run the test suite, including completion parity
just demo             # run rig against a throwaway HOME and a stand-in claude
just run <args>       # run rig from this checkout against your real setup
just trial-on         # point the rig on PATH at this checkout; just trial-off reverts
just check            # claude plugin validate, as the projection job runs it
just generate         # regenerate plugin.json and docs/ from plugin.yml and the sources
just check-generated  # generate, then show what it wrote
just docs             # render the docsify site and serve it locally
```

The recipes run shipyard straight from its git ref via `uvx`, so there is
nothing to install. They are for seeing the projection before you push; CI is
the writer for what lands.

## Layout

```text
plugin.yml               canonical descriptor: manifest, marketplace entry, docs previews
scripts/rig              the CLI, one Python file run through `uv run --script`; holds the zsh completion
scripts/trial-off.sh     what `just trial-off` runs: reinstalls the CLI from the newest plugin build
commands/install-rig.md  the bootstrap that puts `rig` on PATH
hooks/hooks.yml          hook source; cli-freshness.sh reports a stale `rig` on PATH
tests/                   unittest suite; a test covering a requirement names its ID
dev/demo.py              what `just demo` runs
SPEC.md / STATUS.md      rig's requirements and their coverage
docs/                    docsify site; the tracked pages and sidebar are source
```

`.claude-plugin/plugin.json`, `hooks/hooks.json`, `plugin.yml`'s
`suite.describe` block, and most of `docs/` are **generated** by shipyard from
the sources above. Never hand-edit a
generated file; edit its source and run `just generate`.

Releases are dispatched, not tagged by hand: run the **Release** workflow with a
bump level, and shipyard derives the version from `plugin.yml`, retitles
`CHANGELOG.md`'s `## Unreleased` section, commits, tags that commit, and
publishes. Write the notes into `## Unreleased` first.

## Glossary

The spec's Concepts section defines rig, pin, sandbox, and launch.
