#!/bin/bash
# SessionStart: show the session's rigs on beacon's pane badge. Only a session
# rig launched at a terminal carries RIG_CURRENT, so any other session pays for
# nothing but this check.
set -euo pipefail

[ -n "${RIG_CURRENT:-}" ] && [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] || exit 0
exec python3 "$CLAUDE_PLUGIN_ROOT/scripts/rig" badge
