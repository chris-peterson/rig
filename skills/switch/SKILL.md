---
name: switch
description: Switch this session to other rigs, keeping the conversation. Use when the user asks to switch, change, add, or use different rigs mid-session, or asks which rigs there are.
argument-hint: "[rig...]"
---

Run rig's switch with the rigs the user named, then relay its output as-is.
The base rig loads with any rigs named, and `full` is every installed plugin.
With no rig named, it lists the rigs, marking the ones this session uses; ask
the user which they want, then run it again with them.

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}/scripts/rig" switch $ARGUMENTS --session ${CLAUDE_SESSION_ID}
```

The switch takes effect when Claude Code exits: rig relaunches this
conversation with the new rigs' plugins and asks about pins again. Plugins
loaded now stay loaded until then. When it succeeds, end the turn by telling
the user to type `/exit`; a skill can't exit Claude Code for them.
