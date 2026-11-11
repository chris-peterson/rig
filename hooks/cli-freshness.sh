#!/bin/bash
# SessionStart: report a rig command on PATH that a plugin update left behind.
# Runs from ${CLAUDE_PLUGIN_ROOT}, the one copy guaranteed to be the version now
# loaded; a stale wrapper would report on itself.
set -euo pipefail

[ -n "${CLAUDE_PLUGIN_ROOT:-}" ] || exit 0
exec python3 "$CLAUDE_PLUGIN_ROOT/scripts/rig" freshness
