---
description: Put the rig command on PATH with tab completion, or refresh it after a plugin update
argument-hint: "[--claude]"
disable-model-invocation: true
---

Run rig's install bootstrap, then report its output as-is. Do no other work.

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}/scripts/rig" install-cli ${ARGUMENTS}
```

`--claude` also makes `claude` run rig in new shells, unless another shell
function already defines `claude`.
