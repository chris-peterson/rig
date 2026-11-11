"""Walk through rig against a throwaway HOME and a stand-in claude that prints what it was given.

Nothing here reads or writes your real ~/.rig or ~/.claude, and no Claude Code session starts.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RIG = REPO / "scripts" / "rig"

STAND_IN = textwrap.dedent('''\
    #!{python}
    import json, sys
    args = sys.argv[1:]
    if args == ["--help"]:
        print("Commands:\\n  mcp                     Configure MCP servers\\n  plugin|plugins          Manage plugins")
        sys.exit(0)
    shown = []
    while args:
        arg = args.pop(0)
        if arg == "--settings":
            settings = json.loads(args.pop(0))
            on = sorted(k for k, v in settings["enabledPlugins"].items() if v)
            off = sorted(k for k, v in settings["enabledPlugins"].items() if not v)
            shown.append(f"--settings  enabled: {{', '.join(on)}}; off: {{', '.join(off)}}"
                         + ("; sandbox on" if "sandbox" in settings else ""))
        elif arg == "--plugin-dir":
            shown.append(f"--plugin-dir {{args.pop(0)}}")
        else:
            shown.append(arg)
    print("  claude got:", *shown, sep="\\n    ")
    ''')

RIGS = """\
default: base
rigs:
  base:
    plugins: [anchor@acme, beacon@acme]
  web:
    extends: [base]
    plugins: [frontend-design@acme]
  locked:
    extends: [base]
    plugins: []
    sandbox: true
"""


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        home, bin_dir = Path(tmp) / "home", Path(tmp) / "bin"
        bin_dir.mkdir()
        claude = bin_dir / "claude"
        claude.write_text(STAND_IN.format(python=sys.executable))
        claude.chmod(0o755)
        plugins = home / ".claude" / "plugins"
        plugins.mkdir(parents=True)
        ids = ["anchor@acme", "beacon@acme", "frontend-design@acme", "tack@acme"]
        (plugins / "installed_plugins.json").write_text(json.dumps(
            {"version": 2, "plugins": {i: [{"scope": "user"}] for i in ids}}))
        (home / ".rig").mkdir()
        (home / ".rig" / "rigs.yml").write_text(RIGS)
        checkout = home / "src" / "anchor"
        (checkout / ".claude-plugin").mkdir(parents=True)
        (checkout / ".claude-plugin" / "plugin.json").write_text('{"name": "anchor"}')
        env = {**os.environ, "HOME": str(home), "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}

        def step(title: str, *args: str) -> None:
            print(f"\n$ rig {' '.join(args)}    # {title}", flush=True)
            subprocess.run([sys.executable, str(RIG), *args], env=env, cwd=home, stdin=subprocess.DEVNULL,
                           stderr=subprocess.STDOUT)

        print("A throwaway HOME with four installed plugins and three rigs. The stand-in claude prints its arguments.")
        step("the rigs", "list")
        step("plain launch: the default rig only, everything else off", "-p", "hi")
        step("a named rig adds its plugins to the ones it extends", "use", "web", "-p", "hi")
        step("pin a local checkout of anchor", "pin", "src/anchor")
        step("the rig includes anchor, so the checkout stands in for the installed copy", "-p", "hi")
        step("a rig can turn the sandbox on for every launch", "use", "locked", "-p", "hi")
        step("Claude Code's own subcommands go through untouched", "plugin", "list")


if __name__ == "__main__":
    main()
