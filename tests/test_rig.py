"""rig's tests. Each test that covers a requirement names its ID."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import pty
import re
import select
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RIG = REPO / "scripts" / "rig"

FAKE_CLAUDE = textwrap.dedent('''\
    #!{python}
    import json, os, sys
    HELP = """Usage: claude [options] [command] [prompt]

    Options:
      -p, --print                           Print response and exit

    Commands:
      doctor                                Check the health of your Claude Code
                                            installation.
      install [options] [target]            Install Claude Code native build
      mcp                                   Configure and manage MCP servers
      plugin|plugins                        Manage Claude Code plugins
    """
    if sys.argv[1:] == ["--help"]:
        print(HELP)
        sys.exit(0)
    with open(os.environ["RIG_TEST_ARGV"], "a") as f:
        f.write(json.dumps(sys.argv[1:]) + "\\n")
    ''')


def load_rig():
    loader = importlib.machinery.SourceFileLoader("rig", str(RIG))
    spec = importlib.util.spec_from_loader("rig", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class RigCase(unittest.TestCase):
    """Runs scripts/rig against a temporary HOME with a fake claude on PATH."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name) / "home"
        self.home.mkdir()
        self.bin = Path(self._tmp.name) / "bin"
        self.bin.mkdir()
        self.argv_log = Path(self._tmp.name) / "claude-argv.jsonl"
        fake = self.bin / "claude"
        fake.write_text(FAKE_CLAUDE.format(python=sys.executable))
        fake.chmod(0o755)
        self.env = {
            "HOME": str(self.home),
            "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
            "RIG_TEST_ARGV": str(self.argv_log),
        }

    def tearDown(self):
        self._tmp.cleanup()

    def rig(self, *args: str, cwd: Path | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(RIG), *args], capture_output=True, text=True,
                              env={**self.env, **(env or {})}, cwd=cwd or self.home, stdin=subprocess.DEVNULL)

    def rig_tty(self, *args: str, answers: str = "", cwd: Path | None = None) -> tuple[int, str]:
        """Run rig with a terminal on stdin and stderr, typing the answers; returns (status, terminal text)."""
        master, slave = pty.openpty()
        proc = subprocess.Popen([sys.executable, str(RIG), *args], stdin=slave, stderr=slave,
                                stdout=slave, env=self.env, cwd=cwd or self.home)
        os.close(slave)
        os.write(master, answers.encode())
        output = b""
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            ready, _, _ = select.select([master], [], [], 0.1)
            if ready:
                try:
                    chunk = os.read(master, 4096)
                except OSError:
                    break
                if not chunk:
                    break
                output += chunk
            elif proc.poll() is not None:
                break
        status = proc.wait(timeout=5)
        os.close(master)
        return status, output.decode(errors="replace").replace("\r\n", "\n")

    def claude_calls(self) -> list[list[str]]:
        if not self.argv_log.exists():
            return []
        return [json.loads(line) for line in self.argv_log.read_text().splitlines()]

    def write_rigs(self, text: str) -> None:
        path = self.home / ".rig" / "rigs.yml"
        path.parent.mkdir(exist_ok=True)
        path.write_text(textwrap.dedent(text))

    def write_installed(self, *ids: str, project: dict[str, Path] | None = None) -> None:
        plugins = {i: [{"scope": "user", "installPath": "/x"}] for i in ids}
        for plugin_id, folder in (project or {}).items():
            plugins.setdefault(plugin_id, []).append({"scope": "project", "projectPath": str(folder)})
        path = self.home / ".claude" / "plugins" / "installed_plugins.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"version": 2, "plugins": plugins}))

    def write_settings(self, folder: Path, enabled: dict[str, bool]) -> None:
        path = folder / ".claude" / "settings.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"enabledPlugins": enabled}, indent=2))

    def launched(self) -> tuple[dict, list[str]]:
        """The settings overlay and the remaining arguments of the one claude launch."""
        calls = [c for c in self.claude_calls() if c[:1] == ["--settings"]]
        self.assertEqual(len(calls), 1, self.claude_calls())
        return json.loads(calls[0][1]), calls[0][2:]


BASIC_RIGS = """\
    default: base
    rigs:
      base:
        plugins: [a@m, b@m]
      web:
        extends: [base]
        plugins: [c@n]
    """


class Rigs(RigCase):
    def setUp(self):
        super().setUp()
        self.write_rigs(BASIC_RIGS)
        self.write_installed("a@m", "b@m", "c@n", "d@n")

    def test_rig_01_reads_rigs_from_user_file(self):
        self.assertEqual(self.rig("-p", "hi").returncode, 0)
        enabled = self.launched()[0]["enabledPlugins"]
        self.assertTrue(enabled["a@m"] and enabled["b@m"])

    def test_rig_02_extends_loads_parent_plugins(self):
        self.rig("use", "web", "-p", "hi")
        enabled = self.launched()[0]["enabledPlugins"]
        self.assertEqual({k for k, v in enabled.items() if v}, {"a@m", "b@m", "c@n"})

    def test_rig_03_cycle_names_rigs(self):
        self.write_rigs("""\
            default: a
            rigs:
              a: {extends: [b], plugins: []}
              b: {extends: [a], plugins: []}
            """)
        result = self.rig("-p", "hi")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("a → b → a", result.stderr)
        self.assertEqual(self.claude_calls(), [])

    def test_rig_04_only_rig_plugins_enabled(self):
        self.write_settings(self.home, {"d@n": True, "e@n": True})
        self.rig("-p", "hi")
        enabled = self.launched()[0]["enabledPlugins"]
        self.assertEqual({k for k, v in enabled.items() if v}, {"a@m", "b@m"})
        self.assertIs(enabled["d@n"], False)
        self.assertIs(enabled["e@n"], False)

    def test_rig_04_project_settings_plugins_turned_off(self):
        project = self.home / "src" / "proj"
        project.mkdir(parents=True)
        self.write_settings(project, {"p@n": True})
        self.rig("-p", "hi", cwd=project)
        self.assertIs(self.launched()[0]["enabledPlugins"]["p@n"], False)

    def test_rig_05_use_launches_named_rig(self):
        result = self.rig("use", "web", "-p", "hi")
        self.assertIn("rig: web (extends base), 3 plugins", result.stderr)
        self.assertEqual(self.launched()[1], ["-p", "hi"])

    def test_rig_05_use_unknown_rig(self):
        result = self.rig("use", "nope")
        self.assertIn("no rig named nope. Rigs: base, web", result.stderr)
        self.assertEqual(self.claude_calls(), [])

    def test_rig_07_bare_rig_uses_default(self):
        result = self.rig()
        self.assertIn("rig: base, 2 plugins", result.stderr)
        self.assertEqual(self.launched()[1], [])

    def test_rig_09_list(self):
        result = self.rig("list")
        self.assertEqual(result.stdout, textwrap.dedent("""\
            base (default)
              plugins: a@m, b@m
            web
              extends: base
              plugins: c@n
            """))

    def test_rig_11_missing_plugin_refused_headless(self):
        self.write_installed("a@m")
        result = self.rig("-p", "hi")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("b@m", result.stderr)
        self.assertEqual(self.claude_calls(), [])

    def test_rig_10_missing_plugin_installed_after_yes(self):
        self.write_installed("a@m")
        status, _ = self.rig_tty(answers="y\n")
        self.assertEqual(status, 0)
        self.assertEqual(self.claude_calls()[0], ["plugin", "install", "b@m"])
        self.assertEqual(self.claude_calls()[1][0], "--settings")

    def test_rig_10_missing_plugin_refused_after_no(self):
        self.write_installed("a@m")
        status, output = self.rig_tty(answers="n\n")
        self.assertNotEqual(status, 0)
        self.assertIn("launch refused: b@m isn't installed", output)
        self.assertEqual(self.claude_calls(), [])

    def test_rig_10_project_scope_install_counts(self):
        project = self.home / "proj"
        project.mkdir()
        self.write_installed("a@m", project={"b@m": project})
        self.assertEqual(self.rig("-p", "hi", cwd=project).returncode, 0)


class Launch(RigCase):
    def setUp(self):
        super().setUp()
        self.write_rigs(BASIC_RIGS)
        self.write_installed("a@m", "b@m", "c@n")

    def test_launch_01_args_pass_unchanged(self):
        args = ["--model", "haiku", "-c", "fix the bug", "--", "-x"]
        self.rig(*args)
        self.assertEqual(self.launched()[1], args)

    def test_launch_02_prints_rig_before_claude(self):
        result = self.rig("-p", "hi")
        self.assertTrue(result.stderr.startswith("rig: base"))

    def test_launch_03_prompt_word_goes_to_claude(self):
        self.rig("web", "-p")
        self.assertEqual(self.launched()[1], ["web", "-p"])

    def test_launch_refuses_second_settings_flag(self):
        for flag in (["--settings", "{}"], ["--settings={}"]):
            result = self.rig(*flag)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("a second --settings replaces the first", result.stderr)
        self.assertEqual(self.claude_calls(), [])

    def test_no_rigs_file_refused(self):
        (self.home / ".rig" / "rigs.yml").unlink()
        result = self.rig("-p", "hi")
        self.assertIn("run `rig setup`", result.stderr)


class Help(RigCase):
    def test_help_prints_usage_and_exits_zero(self):
        for flag in ("--help", "-h", "help"):
            result = self.rig(flag)
            self.assertEqual(result.returncode, 0, flag)
            self.assertIn("usage: rig", result.stdout)

    def test_version_matches_plugin_json(self):
        manifest = json.loads((REPO / ".claude-plugin" / "plugin.json").read_text())
        result = self.rig("--version")
        self.assertEqual(result.returncode, 0)
        self.assertRegex(result.stdout.strip(), rf"^rig {re.escape(manifest['version'])}(-dev(\.g[0-9a-f]{{7}}(\.dirty)?)?)?$")


class Shell(RigCase):
    def test_shell_03_rig_prefix_is_dropped(self):
        result = self.rig("rig", "--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("usage: rig", result.stdout)

    def test_launch_04_claude_subcommand_passes_through_unchanged(self):
        result = self.rig("plugin", "list", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.claude_calls(), [["plugin", "list", "--json"]])
        self.assertEqual(result.stderr, "")

    def test_shell_03_plugin_pin_is_rigs(self):
        result = self.rig("plugin", "pin")
        self.assertEqual(result.stdout, "No plugins pinned.\n")
        self.rig("plugins", "unpin", "nope")
        self.rig("plugin", "list")
        self.assertEqual(self.claude_calls(), [["plugin", "list"]])

    def test_launch_04_subcommand_alias(self):
        self.rig("plugins", "list")
        self.assertEqual(self.claude_calls(), [["plugins", "list"]])

    def test_shell_01_install_writes_wrapper_on_path(self):
        result = self.rig("install-cli")
        self.assertEqual(result.returncode, 0, result.stderr)
        wrapper = self.home / ".local" / "bin" / "rig"
        self.assertIn(f'"{RIG.resolve()}"', wrapper.read_text())
        self.assertTrue(os.access(wrapper, os.X_OK))
        self.assertIn("fpath=(~/.zsh/completions $fpath)", (self.home / ".zshrc").read_text())
        self.assertTrue((self.home / ".zsh" / "completions" / "_rig").read_text().startswith("#compdef rig"))

    def test_shell_01_install_is_idempotent(self):
        self.rig("install-cli")
        zshrc = (self.home / ".zshrc").read_text()
        result = self.rig("install-cli")
        self.assertIn("already installed", result.stdout)
        self.assertEqual((self.home / ".zshrc").read_text(), zshrc)

    def test_shell_01_fpath_goes_before_compinit(self):
        (self.home / ".zshrc").write_text("export FOO=1\nautoload -Uz compinit && compinit\n")
        self.rig("install-cli")
        lines = (self.home / ".zshrc").read_text().splitlines()
        self.assertLess(lines.index("fpath=(~/.zsh/completions $fpath)"),
                        lines.index("autoload -Uz compinit && compinit"))

    def test_shell_04_install_offers_claude_function(self):
        result = self.rig("install-cli")
        self.assertIn("--claude", result.stdout)
        self.assertFalse((self.home / ".zsh" / "rig.zsh").exists())

    def test_shell_04_claude_flag_makes_claude_run_rig(self):
        self.rig("install-cli", "--claude")
        self.assertIn('claude() { rig "$@" }', (self.home / ".zsh" / "rig.zsh").read_text())
        self.assertIn("source ~/.zsh/rig.zsh", (self.home / ".zshrc").read_text())
        found = subprocess.run(["zsh", "-ic", "whence -w claude"], capture_output=True, text=True,
                               env=self.env, stdin=subprocess.DEVNULL)
        self.assertIn("claude: function", found.stdout)

    def test_shell_04_leaves_another_claude_function_alone(self):
        other = self.home / "other.zsh"
        other.write_text("claude() { echo other }\n")
        (self.home / ".zshrc").write_text(f"source {other}\n")
        result = self.rig("install-cli", "--claude")
        self.assertIn(f"claude is a shell function from {other}", result.stdout)
        self.assertFalse((self.home / ".zsh" / "rig.zsh").exists())

    def write_wrapper(self, target: Path):
        wrapper = self.home / ".local" / "bin" / "rig"
        wrapper.parent.mkdir(parents=True)
        wrapper.write_text(f'#!/bin/sh\nexec uv run --quiet --script "{target}" "$@"\n')

    def test_shell_02_silent_without_wrapper(self):
        result = self.rig("freshness")
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_shell_02_silent_when_wrapper_runs_this_copy(self):
        self.write_wrapper(RIG.resolve())
        self.assertEqual(self.rig("freshness").stdout, "")

    def test_shell_02_reports_wrapper_into_gone_install(self):
        self.write_wrapper(self.home / ".claude" / "plugins" / "cache" / "m" / "rig" / "0.0.1" / "scripts" / "rig")
        report = json.loads(self.rig("freshness").stdout)
        self.assertEqual(report["systemMessage"], "rig: /rig:install-rig  # cli is outdated")
        self.assertIn("is gone", report["hookSpecificOutput"]["additionalContext"])

    def test_shell_02_reports_wrapper_into_older_install(self):
        old = self.home / ".claude" / "plugins" / "cache" / "m" / "rig" / "0.0.1" / "scripts" / "rig"
        old.parent.mkdir(parents=True)
        old.write_text("")
        self.write_wrapper(old)
        report = json.loads(self.rig("freshness").stdout)
        self.assertIn("is an older install", report["hookSpecificOutput"]["additionalContext"])

    def test_shell_02_silent_for_a_dev_checkout(self):
        checkout = self.home / "src" / "rig" / "scripts" / "rig"
        checkout.parent.mkdir(parents=True)
        checkout.write_text("")
        self.write_wrapper(checkout)
        self.assertEqual(self.rig("freshness").stdout, "")


class Pins(RigCase):
    def setUp(self):
        super().setUp()
        self.write_rigs(BASIC_RIGS)
        self.write_installed("a@m", "b@m", "c@n", "x@n")
        self.ckout = self.checkout("b")

    def checkout(self, name: str, folder: str | None = None) -> Path:
        path = self.home / "src" / (folder or name)
        (path / ".claude-plugin").mkdir(parents=True)
        (path / ".claude-plugin" / "plugin.json").write_text(json.dumps({"name": name}))
        return path

    def pins(self) -> list[dict]:
        import yaml
        return yaml.safe_load((self.home / ".rig" / "pins.yml").read_text())

    def test_pin_01_records_pin_for_the_plugin(self):
        result = self.rig("pin", str(self.ckout))
        self.assertEqual(result.returncode, 0, result.stderr)
        [pin] = self.pins()
        self.assertEqual((pin["plugin"], pin["path"]), ("b", str(self.ckout.resolve())))

    def test_pin_01_same_plugin_twice_refused(self):
        self.rig("pin", str(self.ckout))
        other = self.checkout("b", "b-fork")
        result = self.rig("pin", str(other))
        self.assertIn("b is already pinned", result.stderr)

    def test_pin_02_name_resolves_to_marketplace_clone(self):
        clones = self.home / "src" / "github"
        clone = clones / "acme" / "widget"
        (clone / ".claude-plugin").mkdir(parents=True)
        (clone / ".claude-plugin" / "plugin.json").write_text(json.dumps({"name": "widget"}))
        subprocess.run(["git", "init", "-q", str(clone)], check=True)
        subprocess.run(["git", "-C", str(clone), "remote", "add", "origin", "git@github.com:acme/widget.git"], check=True)
        market = self.home / ".claude" / "plugins" / "marketplaces" / "acme"
        (market / ".claude-plugin").mkdir(parents=True)
        (market / ".claude-plugin" / "marketplace.json").write_text(json.dumps(
            {"plugins": [{"name": "widget", "source": {"source": "github", "repo": "acme/widget"}}]}))
        (self.home / ".claude" / "plugins" / "known_marketplaces.json").write_text(json.dumps(
            {"acme": {"installLocation": str(market), "source": {"source": "github", "repo": "acme/market"}}}))
        no_clones = self.rig("pin", "widget")
        self.assertIn("names no clone folder for github.com", no_clones.stderr)
        self.write_rigs(BASIC_RIGS.rstrip(" ") + f"    clones:\n      github.com: {clones}\n")
        result = self.rig("pin", "widget")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.pins()[0]["path"], str(clone.resolve()))
        self.assertEqual(self.rig("complete", "pinnable").stdout, "")

    def test_pin_03_no_manifest_refused(self):
        empty = self.home / "empty"
        empty.mkdir()
        result = self.rig("pin", str(empty))
        self.assertIn("holds no plugin manifest", result.stderr)
        self.assertFalse((self.home / ".rig" / "pins.yml").exists())

    def test_pin_04_missing_checkout_stops_launch(self):
        self.rig("pin", str(self.ckout))
        (self.ckout / ".claude-plugin" / "plugin.json").unlink()
        (self.ckout / ".claude-plugin").rmdir()
        self.ckout.rmdir()
        result = self.rig("-p", "hi")
        self.assertIn("pinned plugin b is missing", result.stderr)
        self.assertIn("rig unpin b", result.stderr)
        self.assertEqual(self.claude_calls(), [])

    def test_pin_05_unpin_by_name_and_path(self):
        self.rig("pin", str(self.ckout))
        self.assertEqual(self.rig("unpin", "b").returncode, 0)
        self.assertEqual(self.pins(), [])
        self.rig("pin", str(self.ckout))
        self.assertEqual(self.rig("unpin", str(self.ckout)).returncode, 0)
        self.assertEqual(self.pins(), [])
        self.rig("-p", "hi")
        self.assertNotIn("--plugin-dir", self.launched()[1])

    def test_pin_06_bare_pin_lists_with_age(self):
        self.rig("pin", str(self.ckout))
        self.assertRegex(self.rig("pin").stdout, r"^b  ~/src/b  \(pinned just now\)\n$")

    def test_pin_07_asks_inside_pinned_checkout(self):
        self.rig("pin", str(self.ckout))
        status, output = self.rig_tty(answers="n\n", cwd=self.ckout)
        self.assertEqual(status, 0, output)
        self.assertIn("~/src/b is pinned. Load it into this session?", output)
        overlay, args = self.launched()
        self.assertNotIn("--plugin-dir", args)
        self.assertIs(overlay["enabledPlugins"]["b@m"], True)

    def test_pin_08_rig_plugin_loads_from_checkout(self):
        self.rig("pin", str(self.ckout))
        result = self.rig("-p", "hi")
        overlay, args = self.launched()
        self.assertEqual(args[:2], ["--plugin-dir", str(self.ckout.resolve())])
        self.assertIs(overlay["enabledPlugins"]["b@m"], False)
        self.assertIn("pins: b  ~/src/b  (pinned just now)", result.stderr)

    def test_pin_09_asks_about_pin_outside_rig(self):
        self.rig("pin", str(self.checkout("x")))
        status, output = self.rig_tty(answers="y\n")
        self.assertEqual(status, 0, output)
        self.assertIn("x is pinned at ~/src/x, and rig base doesn't include it. Load it?", output)
        self.assertIn("--plugin-dir", self.launched()[1])

    def test_pin_10_pin_outside_rig_left_out_headless(self):
        self.rig("pin", str(self.checkout("x")))
        result = self.rig("-p", "hi")
        self.assertNotIn("--plugin-dir", self.launched()[1])
        self.assertIn("(pinned just now, not loaded)", result.stderr)

    def test_tab_unpin_names_read_from_pins_file(self):
        self.rig("pin", str(self.ckout))
        self.rig("pin", str(self.checkout("x")))
        program = CompletionParity().awk_program("_rig_pinned")
        names = subprocess.run(["awk", program, str(self.home / ".rig" / "pins.yml")],
                               capture_output=True, text=True).stdout.split()
        self.assertEqual(names, ["b", "x"])


class Sandbox(RigCase):
    def setUp(self):
        super().setUp()
        self.write_rigs("""\
            default: base
            rigs:
              base: {plugins: [a@m]}
              locked: {extends: [base], plugins: [], sandbox: true}
              inner: {extends: [locked], plugins: []}
            """)
        self.write_installed("a@m")

    def test_sandbox_01_flag_turns_sandbox_on_strictly(self):
        result = self.rig("--sandbox", "-p", "hi")
        overlay, args = self.launched()
        self.assertEqual(overlay["sandbox"],
                         {"enabled": True, "failIfUnavailable": True, "allowUnsandboxedCommands": False})
        self.assertEqual(args, ["-p", "hi"])
        self.assertIn("sandbox: on", result.stderr)

    def test_sandbox_01_flag_after_rig_name(self):
        self.rig("use", "base", "-p", "hi", "--sandbox")
        overlay, args = self.launched()
        self.assertIn("sandbox", overlay)
        self.assertEqual(args, ["-p", "hi"])

    def test_sandbox_01_flag_after_double_dash_goes_to_claude(self):
        self.rig("-p", "--", "--sandbox")
        overlay, args = self.launched()
        self.assertNotIn("sandbox", overlay)
        self.assertEqual(args, ["-p", "--", "--sandbox"])

    def test_sandbox_02_rig_turns_sandbox_on(self):
        for name in ("locked", "inner"):
            self.argv_log.unlink(missing_ok=True)
            result = self.rig("use", name, "-p", "hi")
            self.assertIn("sandbox", self.launched()[0], name)
            self.assertIn("sandbox: on", result.stderr)

    def test_launch_02_sandbox_off_line(self):
        result = self.rig("-p", "hi")
        self.assertNotIn("sandbox", self.launched()[0])
        self.assertTrue(result.stderr.endswith("pins: none\nsandbox: off\n"), result.stderr)

    def test_rig_09_list_shows_sandbox(self):
        self.assertIn("locked\n  extends: base\n  plugins: none\n  sandbox: on\n", self.rig("list").stdout)


GROUPED_SETTINGS = """{
  "model": "opus",
  "enabledPlugins": {
    "a@m": true,
    "b@m": true,

    "c@n": true,
    "d@n": true,

    "e@o": true,
    "f@o": false
  }
}
"""

FLAT_SETTINGS = """{
  "enabledPlugins": {
    "a@m": true,
    "b@m": true,
    "c@n": true,
    "d@n": true,
    "e@o": true
  }
}
"""


class Setup(RigCase):
    def setUp(self):
        super().setUp()
        self.write_installed("a@m", "b@m", "c@n", "d@n", "e@o", "f@o")

    def settings(self, text: str) -> None:
        path = self.home / ".claude" / "settings.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def config(self) -> dict:
        import yaml
        return yaml.safe_load((self.home / ".rig" / "rigs.yml").read_text())

    def test_setup_01_interactive_launch_runs_setup_then_launches(self):
        self.settings(FLAT_SETTINGS)
        status, output = self.rig_tty(answers="1 2\nq\n")
        self.assertEqual(status, 0, output)
        self.assertIn("first-run setup", output)
        self.assertEqual(self.config()["default"], "base")
        enabled = self.launched()[0]["enabledPlugins"]
        self.assertEqual({k for k, v in enabled.items() if v}, {"a@m", "b@m"})

    def test_setup_02_lists_enabled_plugins(self):
        self.settings(GROUPED_SETTINGS)
        _, output = self.rig_tty("setup", answers="1-2\nq\n")
        self.assertIn("1  a@m", output)
        self.assertIn("5  e@o", output)
        self.assertNotIn("f@o", output)

    def test_setup_03_base_rig_written_as_default(self):
        self.settings(FLAT_SETTINGS)
        self.rig_tty("setup", answers="1,2\nq\n")
        config = self.config()
        self.assertEqual(config["default"], "base")
        self.assertEqual(config["rigs"]["base"]["plugins"], ["a@m", "b@m"])

    def test_setup_04a_one_rig_per_blank_line_group(self):
        self.settings(GROUPED_SETTINGS)
        status, output = self.rig_tty("setup", answers="1 2\nweb\ntools\n")
        self.assertEqual(status, 0, output)
        rigs = self.config()["rigs"]
        self.assertEqual(rigs["web"], {"extends": ["base"], "plugins": ["c@n", "d@n"]})
        self.assertEqual(rigs["tools"], {"extends": ["base"], "plugins": ["e@o"]})

    def test_setup_04b_one_rig_per_marketplace(self):
        self.settings(FLAT_SETTINGS)
        status, output = self.rig_tty("setup", answers="1 2\n\nmine\n")
        self.assertEqual(status, 0, output)
        self.assertIn("Name it [n]", output)
        rigs = self.config()["rigs"]
        self.assertEqual(rigs["n"]["plugins"], ["c@n", "d@n"])
        self.assertEqual(rigs["mine"]["plugins"], ["e@o"])

    def test_setup_04_offers_rigs_until_every_plugin_is_covered(self):
        self.settings(FLAT_SETTINGS)
        status, output = self.rig_tty("setup", answers="1 2\n-\n-\n1 3\nmix\n1\nlast\n")
        self.assertEqual(status, 0, output)
        rigs = self.config()["rigs"]
        self.assertEqual(rigs["mix"]["plugins"], ["c@n", "e@o"])
        self.assertEqual(rigs["last"]["plugins"], ["d@n"])
        self.assertEqual(output.count("aren't in any rig yet"), 2)

    def test_setup_05_rerun_starts_from_existing_rigs(self):
        self.settings(FLAT_SETTINGS)
        self.write_rigs("""\
            default: core
            rigs:
              core: {plugins: [a@m]}
              web: {extends: [core], plugins: [c@n, d@n]}
            """)
        status, output = self.rig_tty("setup", answers="\nq\n")
        self.assertEqual(status, 0, output)
        self.assertIn("*  1  a@m", output)
        self.assertIn("   2  b@m", output)
        self.assertNotIn("Name it [n]", output)
        config = self.config()
        self.assertEqual(config["default"], "core")
        self.assertEqual(config["rigs"]["web"]["plugins"], ["c@n", "d@n"])

    def test_setup_06_headless_launch_without_rigs_refused(self):
        self.settings(FLAT_SETTINGS)
        result = self.rig("-p", "hi")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("run `rig setup`", result.stderr)
        self.assertEqual(self.claude_calls(), [])


class CompletionParity(unittest.TestCase):
    """Every command the dispatcher accepts is offered by the zsh completion, and nothing else is."""

    rig = load_rig()

    def offered(self) -> set[str]:
        block = re.search(r"local -a commands=\(\s*\n(.*?)\n\s*\)", self.rig.ZSH_COMPLETION, re.DOTALL).group(1)
        return {entry.split(":", 1)[0] for entry in re.findall(r"'([^']*)'", block)}

    def test_commands_match(self):
        dispatch = set(self.rig.COMMANDS)
        self.assertGreater(len(dispatch), 0)
        expected = dispatch - self.rig.UNCOMPLETED_COMMANDS
        self.assertEqual(self.offered(), expected,
                         f"missing: {sorted(expected - self.offered())}; stale: {sorted(self.offered() - expected)}")

    def test_taken_claude_subcommands_offered(self):
        block = re.search(r"local -a taken=\((.*?)\)\n", self.rig.ZSH_COMPLETION, re.DOTALL).group(1)
        offered = {entry.split(":", 1)[0] for entry in re.findall(r"'([^']*)'", block)}
        self.assertEqual(offered, set(self.rig.CLAUDE_SUBCOMMANDS_TAKEN["plugin"]))
        self.assertLessEqual(offered, set(self.rig.COMMANDS))

    def test_uncompleted_commands_are_real(self):
        self.assertLessEqual(self.rig.UNCOMPLETED_COMMANDS, set(self.rig.COMMANDS))

    def test_completion_cases_name_real_commands(self):
        cases = set(re.findall(r"^    ([a-z][a-z|-]*)\)", self.rig.ZSH_COMPLETION, re.MULTILINE))
        names = {name for case in cases for name in case.split("|")}
        self.assertLessEqual(names, set(self.rig.COMMANDS))

    def awk_program(self, helper: str) -> str:
        body = re.search(rf"^{helper}\(\) {{\n(.*?)\n}}", self.rig.ZSH_COMPLETION, re.DOTALL | re.MULTILINE).group(1)
        return re.search(r"awk '(.*?)' \$file", body, re.DOTALL).group(1)

    def test_tab_03_rig_names_read_from_rigs_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "rigs.yml"
            for text in (textwrap.dedent(BASIC_RIGS),
                         "default: base\nclones:\n  github.com: ~/src\nrigs:\n  base:\n    plugins:\n    - a@m\n"
                         "  web-dev:\n    extends:\n    - base\n    plugins: []\n"):
                path.write_text(text)
                names = subprocess.run(["awk", self.awk_program("_rig_names"), str(path)],
                                       capture_output=True, text=True).stdout.split()
                self.assertIn(names, (["base", "web"], ["base", "web-dev"]))

    def test_zsh_parses_the_completion(self):
        with tempfile.NamedTemporaryFile("w", suffix=".zsh") as f:
            f.write(self.rig.ZSH_COMPLETION)
            f.flush()
            result = subprocess.run(["zsh", "-n", f.name], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
