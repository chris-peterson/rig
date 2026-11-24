"""Render rig's full-screen views to SVG for the docs, against a throwaway HOME and sample rigs.

The views draw in rig's own Dracula theme, so the SVGs match what a terminal shows. Re-run after a
change to the picker or the editor: `just screenshots`. Nothing reads or writes your real ~/.rig.
"""

from __future__ import annotations

import asyncio
import importlib.machinery
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "docs" / "resources"
SIZE = (100, 24)

RIGS = {
    "base": {"plugins": ["anchor@acme", "beacon@acme", "guardrails@acme"]},
    "web": {"plugins": ["frontend-design@acme", "playwright@acme", "widget@acme"]},
    "infra": {"plugins": ["terraform@acme", "k8s@acme"], "rules": [{"path": "*infra*/"}, {"exists": ["**/*.tf"]}]},
    "spec": {"plugins": ["sextant@acme"], "rules": [{"exists": "SPEC.md"}]},
    "data": {"plugins": ["notebooks@acme", "warehouse@acme"]},
}
DEFAULT = ["web"]
INSTALLED = sorted({p for rig in RIGS.values() for p in rig["plugins"]})


def load_rig():
    loader = importlib.machinery.SourceFileLoader("rig", str(REPO / "scripts" / "rig"))
    spec = importlib.util.spec_from_loader("rig", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


async def picker(rig, name: str, selected: list[str], keys: list[str]) -> None:
    pins = [{"plugin": "widget", "path": str(Path.home() / "src" / "acme" / "widget"),
             "pinned_at": "2026-11-20T09:00:00+00:00"}]
    rig.write_pins(pins)
    rigs = {name: {"plugins": r["plugins"]} for name, r in RIGS.items()}
    plan_for = lambda names, *picks: rig.plan(names, rigs, set(INSTALLED), pins, Path.home() / "src" / "acme" / "shop", *picks)
    columns = [{"name": n, "default": n in DEFAULT, "plugins": INSTALLED if n == "full" else rigs[n]["plugins"]}
               for n in rig.rig_order(rigs)]
    app = rig.select_app(plan_for, columns, INSTALLED, pins, plan_for(selected), False, "rig --select")
    await shoot(app, name, keys)


async def editor(rig, name: str, keys: list[str]) -> None:
    config = {"default": DEFAULT, "clones": {}, "rigs": RIGS}
    app = rig.editor_app(rig.RigEdits(config, [], [], INSTALLED))
    await shoot(app, name, keys)


async def shoot(app, name: str, keys: list[str]) -> None:
    async with app.run_test(size=SIZE) as pilot:
        await pilot.pause()
        for key in keys:
            await pilot.press(key)
        await pilot.pause()
        path = app.save_screenshot(filename=f"{name}.svg", path=str(OUT))
    print(f"wrote {Path(path).relative_to(REPO)}")


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as home:
        os.environ["HOME"] = home
        os.environ["TEXTUAL_ANIMATIONS"] = "none"
        rig = load_rig()
        await picker(rig, "picker", ["web"], ["right", "space"])
        await editor(rig, "setup", ["down", "down"])


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
