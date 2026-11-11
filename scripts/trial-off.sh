#!/usr/bin/env bash
# End a trial (`just trial-on`): point the `rig` on PATH back at the highest
# installed plugin build. Runs that build's own `install-cli`, the same path
# `/rig:install-rig` takes, so ending a trial lands exactly what a user has
# rather than a wrapper this script hand-wrote.
set -euo pipefail

cache="${HOME}/.claude/plugins/cache"

# The marketplace rig is installed from is not fixed, so the version
# directories are found by where rig lands rather than by a name baked in here.
# Versions sort as numbers, so 1.10.0 beats 1.9.0.
root=$(find "$cache" -mindepth 3 -maxdepth 3 -type d -path "*/rig/*" 2>/dev/null \
	| awk -F/ '{ split($NF, v, "."); printf "%010d%010d%010d\t%s\n", v[1], v[2], v[3], $0 }' \
	| sort \
	| tail -1 \
	| cut -f2)

if [ -z "$root" ]; then
	echo "No installed rig plugin found under $cache." >&2
	echo "Install it with \`claude plugin install rig\`, then re-run." >&2
	exit 1
fi

script="$root/scripts/rig"
if [ ! -f "$script" ]; then
	echo "Plugin at $root has no scripts/rig." >&2
	exit 1
fi

CLAUDE_PLUGIN_ROOT="$root" uv run --quiet --script "$script" install-cli

echo
echo "Restored $(CLAUDE_PLUGIN_ROOT="$root" uv run --quiet --script "$script" --version) from the plugin cache."
