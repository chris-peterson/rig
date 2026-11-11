---
name: switch
description: Switch this session to another rig, keeping the conversation. Use when the user asks to switch, change, or use a different rig mid-session, or asks which rigs there are.
argument-hint: "[rig]"
---

Run rig's switch with the rig the user named, then relay its output as-is. With
no rig named, it lists the rigs; ask the user which one they want, then run it
again with that rig.

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}/scripts/rig" switch $ARGUMENTS --session ${CLAUDE_SESSION_ID}
```

The switch takes effect when Claude Code exits: rig relaunches this
conversation with the new rig's plugins and asks about pins again. Plugins
loaded now stay loaded until then. When it succeeds, end the turn by telling
the user to type `/exit`; a skill can't exit Claude Code for them.
