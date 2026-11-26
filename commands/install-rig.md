---
description: Put the rig command on PATH with tab completion and make claude (and grok, when it's on PATH) run rig, or refresh them after a plugin update
disable-model-invocation: true
---

Run rig's install bootstrap, then report its output as-is. Do no other work.

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}/scripts/rig" install-cli
```

The install makes `claude` run rig in new shells, and `grok` too when Grok Build
is on PATH, unless another shell function already defines it.
