"""rig's tests. Each test that covers a requirement names its ID."""

from __future__ import annotations

import fcntl
import importlib.machinery
import importlib.util
import json
import os
import pty
import re
import select
import struct
import subprocess
import sys
import tempfile
import termios
import textwrap
import time
import unittest
from pathlib import Path

KEYS = {"space": b" ", "tab": b"\t", "enter": b"\r", "escape": b"\x1b", "down": b"\x1b[B", "s": b"s", "q": b"q", "d": b"d", "e": b"e", "x": b"x", "l": b"l"}
ALT_SCREEN = b"\x1b[?1049h"

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
    with open(os.environ["RIG_TEST_ARGV"] + ".auto-mode", "a") as f:
        f.write(json.dumps(os.environ.get("CLAUDE_CODE_AUTO_MODE_SERVER")) + "\\n")
    if os.environ.get("RIG_TEST_SWITCH_TO") and "--resume" not in sys.argv:
        import subprocess
        subprocess.run([sys.executable, os.environ["RIG_TEST_RIG"], "switch", os.environ["RIG_TEST_SWITCH_TO"],
                        "--session", "abc"], check=True)
    sys.exit(int(os.environ.get("RIG_TEST_EXIT", "0")))
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
            "TERM": "xterm-256color",
            "TEXTUAL_ANIMATIONS": "none",
        }

    def tearDown(self):
        self._tmp.cleanup()

    def rig(self, *args: str, cwd: Path | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(RIG), *args], capture_output=True, text=True,
                              env={**self.env, **(env or {})}, cwd=cwd or self.home, stdin=subprocess.DEVNULL)

    def rig_tty(self, *args: str, answers: str = "", keys: list[str] = (), cwd: Path | None = None) -> tuple[int, str]:
        """Run rig with a terminal on stdin and stderr, typing the answers, or pressing the keys once a
        full-screen app is drawing; returns (status, terminal text)."""
        master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 30, 110, 0, 0))
        proc = subprocess.Popen([sys.executable, str(RIG), *args], stdin=slave, stderr=slave,
                                stdout=slave, env=self.env, cwd=cwd or self.home)
        os.close(slave)
        os.write(master, answers.encode())
        pending = [KEYS[key] for key in keys]
        output = b""
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            ready, _, _ = select.select([master], [], [], 0.3)
            if pending and not ready and ALT_SCREEN in output:
                os.write(master, pending.pop(0))
                continue
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

    def auto_mode_server(self) -> str | None:
        """CLAUDE_CODE_AUTO_MODE_SERVER as the one claude launch saw it."""
        values = Path(f"{self.argv_log}.auto-mode").read_text().splitlines()
        self.assertEqual(len(values), 1, values)
        return json.loads(values[0])

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

    def write_wrapper(self, target: Path):
        wrapper = self.home / ".local" / "bin" / "rig"
        wrapper.parent.mkdir(parents=True, exist_ok=True)
        wrapper.write_text(f'#!/bin/sh\nexec uv run --quiet --script "{target}" "$@"\n')
        wrapper.chmod(0o755)

    def launched(self) -> tuple[dict, list[str]]:
        """The settings overlay and the remaining arguments of the one claude launch."""
        calls = [c for c in self.claude_calls() if c[:1] == ["--settings"]]
        self.assertEqual(len(calls), 1, self.claude_calls())
        return json.loads(calls[0][1]), calls[0][2:]


BASIC_RIGS = """\
    rigs:
      base:
        plugins: [a@m, b@m]
      web:
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

    def enabled_sets(self) -> list[set[str]]:
        return [{k for k, v in json.loads(c[1])["enabledPlugins"].items() if v}
                for c in self.claude_calls() if c[:1] == ["--settings"]]

    def test_rig_02_base_loads_with_the_named_rig(self):
        self.rig("use", "web", "-p", "hi")
        self.assertEqual(self.enabled_sets(), [{"a@m", "b@m", "c@n"}])

    def test_rig_03_several_rigs_by_spaces_commas_or_quotes(self):
        self.write_rigs(BASIC_RIGS.rstrip(" ") + "      tools:\n        plugins: [d@n]\n")
        for names in (["web", "tools"], ["web,tools"], ["web tools"], ["web, tools"]):
            self.rig("use", *names, "-p", "web")
        self.assertEqual(self.enabled_sets(), [{"a@m", "b@m", "c@n", "d@n"}] * 4)
        self.assertEqual({tuple(c[2:]) for c in self.claude_calls()}, {("-p", "web")})

    def test_rig_10_full_loads_every_installed_plugin(self):
        result = self.rig("use", "full", "-p", "hi")
        self.assertEqual(self.enabled_sets(), [{"a@m", "b@m", "c@n", "d@n"}])
        self.assertIn("rig: all 4 plugins", result.stderr)

    def test_rig_11_rig_definitions_out_of_shape_refused(self):
        cases = {
            "rigs:\n  base: {plugins: []}\n  none: {plugins: []}\n": "defines a rig named none",
            "rigs:\n  base: {plugins: []}\n  web: {extends: base, plugins: []}\n": "Take out anything else, such as `extends`",
            "rigs:\n  base: {plugins: [], sandbox: true}\n": "a rig holds only `plugins`",
            "rigs:\n  base: {plugins: []}\n  full: {plugins: []}\n": "defines a rig named full",
            "rigs:\n  core: {plugins: []}\n": "defines no rig named base",
        }
        for text, message in cases.items():
            self.write_rigs(text)
            result = self.rig("-p", "hi")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(message, result.stderr)
        self.assertEqual(self.claude_calls(), [])

    def test_rig_04_launch_settings_name_only_the_rig(self):
        self.write_settings(self.home, {"d@n": False})
        self.rig("-p", "hi")
        self.assertEqual(self.launched()[0]["enabledPlugins"], {"a@m": True, "b@m": True})

    def test_rig_04_project_settings_left_to_the_project(self):
        project = self.home / "src" / "proj"
        project.mkdir(parents=True)
        self.write_settings(project, {"p@n": True})
        self.rig("-p", "hi", cwd=project)
        self.assertNotIn("p@n", self.launched()[0]["enabledPlugins"])
        self.assertIn('"p@n": true', (project / ".claude" / "settings.json").read_text())

    def test_rig_12_user_settings_plugins_turned_off(self):
        path = self.home / ".claude" / "settings.json"
        path.write_text('{\n  "enabledPlugins": {\n    "a@m": true,\n\n    "d@n": true,\n    "e@n": false\n  },\n'
                        '  "model": "opus"\n}\n')
        result = self.rig("-p", "hi")
        self.assertIn("turned off in ~/.claude/settings.json: d@n\n", result.stderr)
        self.assertEqual(path.read_text(), '{\n  "enabledPlugins": {\n    "a@m": false,\n\n    "d@n": false,\n'
                                           '    "e@n": false\n  },\n  "model": "opus"\n}\n')
        self.assertNotIn("turned off", self.rig("-p", "hi").stderr)

    def test_rig_05_use_launches_named_rig(self):
        result = self.rig("use", "web", "-p", "hi")
        self.assertIn("rig: base + web, 3 plugins", result.stderr)
        self.assertEqual(self.launched()[1], ["-p", "hi"])

    def test_rig_05_use_unknown_rig(self):
        result = self.rig("use", "nope")
        self.assertIn("no rig named nope. Rigs: base, web, full", result.stderr)
        self.assertEqual(self.claude_calls(), [])

    def test_rig_06_launch_naming_no_rig_uses_default(self):
        result = self.rig("claude")
        self.assertIn("rig: base, 2 plugins", result.stderr)
        self.assertEqual(self.launched()[1], [])

    def test_rig_06_default_rigs_added_to_base(self):
        self.write_rigs("default: [web]\n" + textwrap.dedent(BASIC_RIGS))
        result = self.rig("-p", "hi")
        self.assertIn("rig: base + web, 3 plugins", result.stderr)

    def test_shell_06_rig_claude_runs_rig_commands(self):
        self.assertTrue(self.rig("claude", "list").stdout.startswith("base (every launch)"))
        self.assertEqual(self.claude_calls(), [])

    def test_shell_06_rig_claude_launches_with_arguments(self):
        self.rig("claude", "-p", "hi")
        self.assertEqual(self.launched()[1], ["-p", "hi"])

    def test_rig_07_list(self):
        result = self.rig("list")
        self.assertEqual(result.stdout, textwrap.dedent("""\
            base (every launch)
              plugins: a@m, b@m
            web
              plugins: c@n
            full
              plugins: every installed plugin
            """))

    def test_rig_13_list_json(self):
        self.write_rigs("default: [web]\n" + textwrap.dedent(BASIC_RIGS))
        listed = json.loads(self.rig("list", "--json").stdout)
        self.assertEqual(listed["default"], ["web"])
        self.assertEqual([(r["name"], r["built_in"], r["default"]) for r in listed["rigs"]],
                         [("base", True, False), ("web", False, True), ("full", True, False)])
        self.assertEqual(listed["rigs"][2]["plugins"], ["a@m", "b@m", "c@n", "d@n"])

    def test_rig_14_list_graph(self):
        self.write_rigs("default: [web]\n" + textwrap.dedent(BASIC_RIGS))
        self.assertEqual(self.rig("list", "--graph").stdout, textwrap.dedent("""\
            plugin  base  ★web
            a@m      ●     ·
            b@m      ●     ·
            c@n      ·     ●
            d@n      ·     ·
            """))

    def test_rig_17_none_refused_headless_and_alongside_other_rigs(self):
        result = self.rig("use", "none", "-p", "hi")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("needs someone at a terminal to confirm it", result.stderr)
        status, output = self.rig_tty("use", "none", "web", answers="y\n")
        self.assertNotEqual(status, 0)
        self.assertIn("none launches Claude Code with no plugins, so it goes alone", output)
        self.assertEqual(self.claude_calls(), [])

    def test_rig_16_none_launches_once_confirmed(self):
        self.write_settings(self.home / "proj", {"p@n": True})
        status, output = self.rig_tty("use", "none", answers="n\n")
        self.assertNotEqual(status, 0)
        self.assertIn("Launch with no plugins? [y/N]", output)
        self.assertEqual(self.claude_calls(), [])
        status, output = self.rig_tty("use", "none", "--sandbox", answers="y\n", cwd=self.home / "proj")
        self.assertEqual(status, 0, output)
        self.assertIn("rig: none, no plugins", output)
        settings, rest = self.launched()
        self.assertEqual(settings["enabledPlugins"], dict.fromkeys(["a@m", "b@m", "c@n", "d@n", "p@n"], False))
        self.assertTrue(settings["sandbox"]["enabled"])
        self.assertEqual(rest, [])

    def test_rig_09_missing_plugin_refused_headless(self):
        self.write_installed("a@m")
        result = self.rig("-p", "hi")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("b@m", result.stderr)
        self.assertEqual(self.claude_calls(), [])

    def test_rig_08_missing_plugin_installed_on_launch(self):
        self.write_installed("a@m")
        status, output = self.rig_tty("claude", keys=["enter"])
        self.assertEqual(status, 0, output)
        self.assertEqual(self.claude_calls()[0], ["plugin", "install", "b@m"])
        self.assertEqual(self.claude_calls()[1][0], "--settings")

    def test_rig_08_missing_plugin_refused_on_cancel(self):
        self.write_installed("a@m")
        status, output = self.rig_tty("claude", keys=["q"])
        self.assertNotEqual(status, 0)
        self.assertIn("launch cancelled", output)
        self.assertEqual(self.claude_calls(), [])

    def test_rig_08_project_scope_install_counts(self):
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


class Switch(RigCase):
    def setUp(self):
        super().setUp()
        self.write_rigs(BASIC_RIGS)
        self.write_installed("a@m", "b@m", "c@n")
        self.env["RIG_TEST_RIG"] = str(RIG)

    def launches(self) -> list[tuple[set[str], list[str]]]:
        """(enabled plugins, remaining arguments) for each claude launch, in order."""
        return [({p for p, on in json.loads(c[1])["enabledPlugins"].items() if on}, c[2:])
                for c in self.claude_calls() if c[:1] == ["--settings"]]

    def test_switch_02_exit_relaunches_the_conversation_with_the_new_rig(self):
        self.env["RIG_TEST_SWITCH_TO"] = "web"
        status, output = self.rig_tty("claude", "--sandbox", "fix the bug")
        self.assertEqual(status, 0, output)
        self.assertIn("rig relaunches this conversation with base + web", output)
        (first, first_args), (second, second_args) = self.launches()
        self.assertEqual((first, first_args), ({"a@m", "b@m"}, ["fix the bug"]))
        self.assertEqual((second, second_args[:2]), ({"a@m", "b@m", "c@n"}, ["--resume", "abc"]))
        self.assertEqual(len(second_args), 3)
        self.assertIn("rig relaunched this conversation with base + web", second_args[2])
        self.assertIn("sandbox", json.loads(self.claude_calls()[1][1]))
        self.assertEqual(list((self.home / ".rig" / "switch").iterdir()), [])

    def test_launch_06_exits_with_claudes_status(self):
        self.env["RIG_TEST_EXIT"] = "3"
        status, output = self.rig_tty("claude")
        self.assertEqual(status, 3, output)
        self.assertEqual(len(self.launches()), 1)

    def test_switch_03_session_rig_did_not_launch_refused(self):
        result = self.rig("switch", "web", "--session", "abc")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("rig use web --resume abc", result.stderr)

    def test_switch_04_unknown_rig_refused(self):
        result = self.rig("switch", "nope", "--session", "abc", env={"RIG_SWITCH_FILE": str(self.home / "s.yml")})
        self.assertIn("no rig named nope. Rigs: base, web, full", result.stderr)
        self.assertFalse((self.home / "s.yml").exists())

    def test_switch_05_no_rig_lists_rigs(self):
        result = self.rig("switch", "--session", "abc", env={"RIG_CURRENT": "web"})
        self.assertEqual(result.stdout, "base (this session)\nweb (this session)\nfull\n")

    def test_switch_01_records_several_rigs(self):
        request = self.home / "s.yml"
        result = self.rig("switch", "web", "full", "--session", "abc", env={"RIG_SWITCH_FILE": str(request)})
        self.assertIn("with base + web + full", result.stdout)
        import yaml
        self.assertEqual(yaml.safe_load(request.read_text())["rigs"], ["web", "full"])

    def test_switch_01_records_the_rig_and_session(self):
        request = self.home / "s.yml"
        result = self.rig("switch", "web", "--session", "abc",
                          env={"RIG_SWITCH_FILE": str(request), "RIG_CURRENT": "base"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("/exit", result.stdout)
        import yaml
        self.assertEqual(yaml.safe_load(request.read_text()), {"rigs": ["web"], "session": "abc"})


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

    def test_shell_01_bashcompinit_is_not_compinit(self):
        (self.home / ".zshrc").write_text("autoload -U bashcompinit && bashcompinit\n")
        self.rig("install-cli")
        lines = (self.home / ".zshrc").read_text().splitlines()
        self.assertEqual(lines[1:3], ["fpath=(~/.zsh/completions $fpath)", "autoload -Uz compinit && compinit"])

    def test_shell_04_install_makes_claude_run_rig(self):
        self.rig("install-cli")
        self.assertIn('claude() { rig claude "$@" }', (self.home / ".zsh" / "rig.zsh").read_text())
        self.assertIn("source ~/.zsh/rig.zsh", (self.home / ".zshrc").read_text())
        found = subprocess.run(["zsh", "-ic", "whence -w claude"], capture_output=True, text=True,
                               env=self.env, stdin=subprocess.DEVNULL)
        self.assertIn("claude: function", found.stdout)

    def test_shell_04_leaves_another_claude_function_alone(self):
        other = self.home / "other.zsh"
        other.write_text("claude() { echo other }\n")
        (self.home / ".zshrc").write_text(f"source {other}\n")
        result = self.rig("install-cli")
        self.assertIn(f"claude is a shell function from {other}", result.stdout)
        self.assertFalse((self.home / ".zsh" / "rig.zsh").exists())

    def test_install_cli_takes_no_arguments(self):
        result = self.rig("install-cli", "--claude")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("install-cli takes no arguments", result.stderr)

    def test_shell_05_bare_rig_prints_usage(self):
        result = self.rig()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("usage: rig"))
        self.assertEqual(self.claude_calls(), [])

    def test_shell_06_rig_claude_rig_is_bare_rig(self):
        self.assertTrue(self.rig("claude", "rig").stdout.startswith("usage: rig"))
        self.assertEqual(self.claude_calls(), [])

    def test_shell_06_rig_claude_passes_subcommands_through(self):
        self.rig("claude", "plugin", "list")
        self.assertEqual(self.claude_calls(), [["plugin", "list"]])

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


class Badge(RigCase):
    def setUp(self):
        super().setUp()
        self.beacon_log = Path(self._tmp.name) / "beacon-argv.jsonl"
        beacon = self.bin / "beacon"
        beacon.write_text(f"#!{sys.executable}\nimport json, sys\n"
                          f"open({str(self.beacon_log)!r}, 'a').write(json.dumps(sys.argv[1:]) + '\\n')\n"
                          "print('beacon chatter')\n")
        beacon.chmod(0o755)

    def beacon_calls(self) -> list[list[str]]:
        if not self.beacon_log.exists():
            return []
        return [json.loads(line) for line in self.beacon_log.read_text().splitlines()]

    def test_launch_14_badge_names_the_rigs(self):
        result = self.rig("badge", env={"RIG_CURRENT": "web docs"})
        self.assertEqual((result.returncode, result.stdout), (0, ""))
        self.assertEqual(self.beacon_calls(), [["badge", "web ✦ docs"]])

    def test_launch_14_badge_names_base_alone(self):
        self.rig("badge", env={"RIG_CURRENT": "base"})
        self.assertEqual(self.beacon_calls(), [["badge", "base"]])

    def test_launch_14_no_badge_outside_a_rig_launch(self):
        result = self.rig("badge")
        self.assertEqual((result.returncode, result.stdout), (0, ""))
        self.assertEqual(self.beacon_calls(), [])

    def test_launch_14_silent_without_beacon(self):
        (self.bin / "beacon").unlink()
        result = self.rig("badge", env={"RIG_CURRENT": "web", "PATH": f"{self.bin}{os.pathsep}/usr/bin:/bin"})
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))

    def test_launch_14_hook_skips_a_session_rig_did_not_launch(self):
        env = {**self.env, "CLAUDE_PLUGIN_ROOT": str(RIG.parent.parent)}
        subprocess.run(["bash", str(RIG.parent.parent / "hooks" / "beacon-badge.sh")], env=env, check=True)
        subprocess.run(["bash", str(RIG.parent.parent / "hooks" / "beacon-badge.sh")],
                       env={**env, "RIG_CURRENT": "web"}, check=True)
        self.assertEqual(self.beacon_calls(), [["badge", "web"]])


class Doctor(RigCase):
    """`rig doctor` against a new zsh in the throwaway HOME, with its ~/.local/bin first on PATH
    and no other rig on PATH."""

    def setUp(self):
        super().setUp()
        rest = [p for p in self.env["PATH"].split(os.pathsep) if not (Path(p) / "rig").exists()]
        self.env["PATH"] = os.pathsep.join([str(self.home / ".local" / "bin"), *rest])
        # CI images can ship group-writable system completion directories, which make a plain
        # compinit abort; -u keeps that machine detail out of the checks under test.
        (self.home / ".zshrc").write_text("autoload -Uz compinit && compinit -u\n")

    def plugin_build(self, version: str) -> Path:
        script = self.home / ".claude" / "plugins" / "cache" / "m" / "rig" / version / "scripts" / "rig"
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("")
        return script

    def install_rig_plugin(self, version: str) -> None:
        path = self.home / ".claude" / "plugins" / "installed_plugins.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        entry = {"scope": "user", "installPath": str(self.plugin_build(version).parent.parent)}
        path.write_text(json.dumps({"version": 2, "plugins": {"rig@m": [entry]}}))

    def test_doctor_01_to_03_pass_after_install(self):
        self.rig("install-cli")
        result = self.rig("doctor")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, textwrap.dedent(f"""\
            rig shell setup:
              ✓ rig runs the checkout at {REPO}
              ✓ claude runs rig (~/.zsh/rig.zsh)
              ✓ zsh completes rig
              ✓ zsh completes claude as rig

            """))

    def test_doctor_01_wrapper_into_older_install(self):
        self.install_rig_plugin("0.0.2")
        self.write_wrapper(self.plugin_build("0.0.1"))
        result = self.rig("doctor")
        self.assertEqual(result.returncode, 1)
        self.assertIn("✗ rig runs ~/.claude/plugins/cache/m/rig/0.0.1/scripts/rig, not the installed "
                      "~/.claude/plugins/cache/m/rig/0.0.2/scripts/rig\n"
                      "      fix: run /rig:install-rig in Claude Code\n", result.stdout)

    def test_doctor_01_wrapper_into_gone_install(self):
        self.write_wrapper(self.home / ".claude" / "plugins" / "cache" / "m" / "rig" / "0.0.1" / "scripts" / "rig")
        self.assertIn("✗ rig runs ~/.claude/plugins/cache/m/rig/0.0.1/scripts/rig, which is gone",
                      self.rig("doctor").stdout)

    def test_doctor_01_installed_plugin_passes(self):
        self.install_rig_plugin("0.0.2")
        self.write_wrapper(self.plugin_build("0.0.2"))
        self.assertIn("✓ rig runs the installed plugin at ~/.claude/plugins/cache/m/rig/0.0.2",
                      self.rig("doctor").stdout)

    def test_doctor_01_no_rig_on_path(self):
        result = self.rig("doctor")
        self.assertIn("✗ a new zsh finds no rig on PATH\n      fix: run /rig:install-rig in Claude Code",
                      result.stdout)

    def test_doctor_02_another_claude_function(self):
        other = self.home / "other.zsh"
        other.write_text("claude() { echo other }\n")
        (self.home / ".zshrc").write_text(f"source {other}\n")
        self.rig("install-cli")
        result = self.rig("doctor")
        self.assertEqual(result.returncode, 1)
        self.assertIn("✗ claude is a shell function from ~/other.zsh\n"
                      "      fix: remove that claude function, then run /rig:install-rig in Claude Code\n",
                      result.stdout)

    def test_doctor_03_outdated_completion(self):
        self.rig("install-cli")
        (self.home / ".zsh" / "completions" / "_rig").write_text("#compdef rig\n")
        self.assertIn("✗ ~/.zsh/completions/_rig is out of date", self.rig("doctor").stdout)

    def test_doctor_03_fpath_after_compinit(self):
        self.rig("install-cli")
        zshrc = self.home / ".zshrc"
        lines = zshrc.read_text().splitlines()
        lines.remove("fpath=(~/.zsh/completions $fpath)")
        zshrc.write_text("\n".join(lines + ["fpath=(~/.zsh/completions $fpath)"]) + "\n")
        self.assertIn("✗ compinit didn't register rig's completion\n"
                      "      fix: put `fpath=(~/.zsh/completions $fpath)` before compinit in ~/.zshrc\n",
                      self.rig("doctor").stdout)

    def test_doctor_03_compinit_reads_a_dump_from_before_rig(self):
        (self.home / ".zshrc").write_text("fpath=(~/.zsh/completions $fpath)\nautoload -Uz compinit && compinit -C\n")
        subprocess.run(["zsh", "-ic", "true"], env=self.env, stdin=subprocess.DEVNULL, capture_output=True)
        self.rig("install-cli")
        self.assertIn("✗ compinit didn't register rig's completion\n"
                      "      fix: rm ~/.zcompdump*, then open a new shell; compinit read a dump from before "
                      "rig's completion\n", self.rig("doctor").stdout)
        for dump in self.home.glob(".zcompdump*"):
            dump.unlink()
        self.assertIn("✓ zsh completes rig", self.rig("doctor").stdout)

    def test_doctor_03_install_under_group_writable_umask_passes(self):
        old = os.umask(0o002)
        try:
            self.rig("install-cli")
        finally:
            os.umask(old)
        for folder in (self.home / ".zsh", self.home / ".zsh" / "completions"):
            self.assertEqual(folder.stat().st_mode & 0o777, 0o755)
        self.assertIn("✓ zsh completes rig", self.rig("doctor").stdout)

    def test_doctor_03_claude_not_completed_as_rig(self):
        self.assertIn("✗ zsh doesn't complete claude as rig", self.rig("doctor").stdout)

    def test_doctor_05_runs_claude_doctor_after_its_checks(self):
        result = self.rig("doctor")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.claude_calls(), [["doctor"]])


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
        self.assertRegex(self.rig("pin").stdout, r"^📌 b  ~/src/b  \(just now\)\n$")

    def test_pin_07_pin_holding_cwd_can_be_left_out(self):
        self.rig("pin", str(self.ckout))
        status, output = self.rig_tty("claude", keys=["space", "enter"], cwd=self.ckout)
        self.assertEqual(status, 0, output)
        overlay, args = self.launched()
        self.assertNotIn("--plugin-dir", args)
        self.assertIs(overlay["enabledPlugins"]["b@m"], True)

    def test_pin_08_rig_plugin_loads_from_checkout(self):
        self.rig("pin", str(self.ckout))
        result = self.rig("-p", "hi")
        overlay, args = self.launched()
        self.assertEqual(args[:2], ["--plugin-dir", str(self.ckout.resolve())])
        self.assertIs(overlay["enabledPlugins"]["b@m"], False)
        self.assertIn("\n📌 b  ~/src/b  (just now)\n", result.stderr)

    def test_pin_11_pin_holding_cwd_turns_auto_mode_server_off(self):
        self.rig("pin", str(self.ckout))
        result = self.rig("-p", "hi", cwd=self.ckout)
        self.assertEqual(self.auto_mode_server(), "0")
        self.assertIn("auto mode: CLAUDE_CODE_AUTO_MODE_SERVER=0, since b is pinned here", result.stderr)

    def test_pin_11_folder_holding_pin_turns_auto_mode_server_off(self):
        self.rig("pin", str(self.ckout))
        self.rig("-p", "hi", cwd=self.home / "src")
        self.assertEqual(self.auto_mode_server(), "0")

    def test_pin_11_unrelated_folder_leaves_auto_mode_server(self):
        self.rig("pin", str(self.ckout))
        elsewhere = self.home / "elsewhere"
        elsewhere.mkdir()
        result = self.rig("-p", "hi", cwd=elsewhere)
        self.assertIsNone(self.auto_mode_server())
        self.assertNotIn("auto mode:", result.stderr)

    def test_pin_11_pin_not_loaded_leaves_auto_mode_server(self):
        x = self.checkout("x")
        self.rig("pin", str(x))
        self.rig("-p", "hi", cwd=x)
        self.assertIsNone(self.auto_mode_server())

    def test_pin_11_environment_value_kept(self):
        self.rig("pin", str(self.ckout))
        result = self.rig("-p", "hi", cwd=self.ckout, env={"CLAUDE_CODE_AUTO_MODE_SERVER": "1"})
        self.assertEqual(self.auto_mode_server(), "1")
        self.assertNotIn("auto mode:", result.stderr)

    def test_pin_09_pin_outside_rig_can_be_loaded(self):
        self.rig("pin", str(self.checkout("x")))
        status, output = self.rig_tty("claude", keys=["space", "enter"])
        self.assertEqual(status, 0, output)
        self.assertIn("--plugin-dir", self.launched()[1])

    def test_launch_05_nothing_to_choose_launches_without_confirmation(self):
        self.rig("pin", str(self.ckout))
        status, output = self.rig_tty("claude")
        self.assertEqual(status, 0, output)
        self.assertNotIn(ALT_SCREEN.decode(), output)
        self.assertEqual(self.launched()[1][:1], ["--plugin-dir"])

    def test_pin_10_pin_outside_rig_left_out_headless(self):
        self.rig("pin", str(self.checkout("x")))
        result = self.rig("-p", "hi")
        self.assertNotIn("--plugin-dir", self.launched()[1])
        self.assertIn("📌 x  ~/src/x  (just now, not loaded)", result.stderr)

    def test_pin_12_list_and_graph_mark_pinned_plugins(self):
        self.rig("pin", str(self.ckout))
        self.assertIn("  plugins: a@m, b@m 📌\n", self.rig("list").stdout)
        self.assertEqual(self.rig("list", "--graph").stdout, textwrap.dedent("""\
            plugin  base  web
            a@m      ●     ·
            b@m 📌   ●     ·
            c@n      ·     ●
            x@n      ·     ·
            """))

    def test_launch_07_select_needs_a_terminal(self):
        result = self.rig("--select", "-p", "hi")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--select opens a picker, so it needs a terminal", result.stderr)
        self.assertEqual(self.claude_calls(), [])

    def test_launch_07_select_picks_rigs_before_launching(self):
        status, output = self.rig_tty("--select", "--", "hi", keys=["space", "l"])
        self.assertEqual(status, 0, output)
        self.assertIn("rig: base + web, 3 plugins", output)
        self.assertNotIn("--select", self.launched()[1])
        self.assertEqual(self.launched()[1], ["--", "hi"])

    def test_launch_11_plugins_picked_on_their_own(self):
        status, output = self.rig_tty("--select", "--", "hi", keys=["down", "enter", "down", "down", "down", "enter", "l"])
        self.assertEqual(status, 0, output)
        self.assertIn("rig: base + x@n - a@m, 2 plugins", output)
        self.assertEqual(self.launched()[0]["enabledPlugins"], {"a@m": False, "b@m": True, "x@n": True})

    def test_launch_07_e_opens_the_editor_then_the_picker_again(self):
        status, output = self.rig_tty("--select", "--", "hi", keys=["space", "e", "q", "l"])
        self.assertEqual(status, 0, output)
        self.assertIn("rig setup", output)
        self.assertIn("rig: base + web, 3 plugins", output)
        self.assertEqual(self.launched()[1], ["--", "hi"])

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
            """)
        self.write_installed("a@m")

    def test_sandbox_01_flag_turns_sandbox_on_strictly(self):
        result = self.rig("--sandbox", "-p", "hi")
        overlay, args = self.launched()
        self.assertEqual(overlay["sandbox"],
                         {"enabled": True, "failIfUnavailable": True, "allowUnsandboxedCommands": False,
                          "autoAllowBashIfSandboxed": True})
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

    def test_launch_02_sandbox_off_line(self):
        result = self.rig("-p", "hi")
        self.assertNotIn("sandbox", self.launched()[0])
        self.assertTrue(result.stderr.endswith("📌 none\nsandbox: off\n"), result.stderr)


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
    """First-run setup and `rig setup` driven through a terminal, as a person would."""

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
        status, output = self.rig_tty("claude", keys=["tab", "space", "s", "q"])
        self.assertEqual(status, 0, output)
        self.assertEqual(self.config()["rigs"]["base"]["plugins"], ["b@m", "c@n", "d@n", "e@o"])
        enabled = self.launched()[0]["enabledPlugins"]
        self.assertEqual({k for k, v in enabled.items() if v}, {"b@m", "c@n", "d@n", "e@o"})

    def test_setup_01_launch_stops_when_setup_saves_nothing(self):
        self.settings(FLAT_SETTINGS)
        status, output = self.rig_tty("claude", keys=["q", "d"])
        self.assertNotEqual(status, 0)
        self.assertIn("setup closed without saving any rigs", output)
        self.assertEqual(self.claude_calls(), [])

    def test_setup_05_rerun_opens_existing_rigs(self):
        self.settings(FLAT_SETTINGS)
        self.write_rigs("""\
            default: [web]
            rigs:
              base: {plugins: [a@m]}
              web: {plugins: [c@n, d@n]}
            """)
        status, output = self.rig_tty("setup", keys=["tab", "down", "space", "s", "q"])
        self.assertEqual(status, 0, output)
        config = self.config()
        self.assertEqual(config["default"], ["web"])
        self.assertEqual(config["rigs"]["base"]["plugins"], ["a@m", "b@m"])
        self.assertEqual(config["rigs"]["web"]["plugins"], ["c@n", "d@n"])

    def test_shell_05_bare_rig_opens_setup_without_rigs(self):
        self.settings(FLAT_SETTINGS)
        status, output = self.rig_tty(keys=["s", "q"])
        self.assertEqual(status, 0, output)
        self.assertEqual(self.config()["rigs"]["base"]["plugins"], ["a@m", "b@m", "c@n", "d@n", "e@o"])
        self.assertEqual(self.claude_calls(), [])

    def test_shell_05_bare_rig_prints_usage_once_rigs_exist(self):
        self.write_rigs("rigs:\n  base: {plugins: [a@m]}\n")
        status, output = self.rig_tty()
        self.assertEqual(status, 0, output)
        self.assertIn("usage: rig", output)

    def test_setup_needs_a_terminal(self):
        result = self.rig("setup")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("needs a terminal", result.stderr)

    def test_setup_06_headless_launch_without_rigs_refused(self):
        self.settings(FLAT_SETTINGS)
        result = self.rig("-p", "hi")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("run `rig setup`", result.stderr)
        self.assertEqual(self.claude_calls(), [])


ENABLED = ["a@m", "b@m", "c@n", "d@n", "e@o"]
GROUPS = [["a@m", "b@m"], ["c@n", "d@n"], ["e@o"]]
INSTALLED = [*ENABLED, "f@o"]


def three_rigs() -> dict:
    """base, and the rigs api and web, with web a default."""
    return {"default": ["web"], "clones": {}, "rigs": {
        "base": {"plugins": ["a@m", "b@m"]},
        "web": {"plugins": ["c@n"]},
        "api": {"plugins": ["d@n"]},
    }}


class Edits(unittest.TestCase):
    """The rig editor's changes to the rig definitions, apart from the screen."""

    rig = load_rig()

    def existing(self):
        return self.rig.RigEdits(three_rigs(), ENABLED, [], INSTALLED)

    def first_run(self, groups=()):
        edits = self.rig.RigEdits(None, ENABLED, list(groups), INSTALLED)
        for plugin_id in ("c@n", "d@n", "e@o"):
            edits.toggle("base", plugin_id, False)
        return edits

    def test_setup_02_first_run_starts_base_with_enabled_plugins(self):
        edits = self.rig.RigEdits(None, ENABLED, [], INSTALLED)
        self.assertEqual(edits.rigs, {"base": ENABLED})
        self.assertEqual(edits.default, [])
        self.assertEqual(edits.drafts(), [("f", ["f@o"])])
        self.assertTrue(edits.dirty)

    def test_setup_04a_one_draft_per_blank_line_group(self):
        self.assertEqual(self.first_run(GROUPS).drafts(), [("n", ["c@n", "d@n"]), ("e", ["e@o"]), ("f", ["f@o"])])

    def test_setup_04a_plugins_turned_off_group_with_the_rest(self):
        groups = [["a@m", "b@m"], ["c@n", "d@n"], ["e@o", "f@o"]]
        self.assertEqual(self.first_run(groups).drafts(), [("n", ["c@n", "d@n"]), ("o", ["e@o", "f@o"])])

    def test_setup_04a_draft_names(self):
        name = self.rig.draft_name
        self.assertEqual(name(["robot-sheriff@g"]), "robot-sheriff")
        self.assertEqual(name(["uni-audit@g", "uni-merge@g", "uni-tools@g"]), "uni")
        self.assertEqual(name(["infra-sql@g", "infra-tools@h"]), "infra")
        self.assertEqual(name(["anchor@g", "beacon@g"]), "g")
        self.assertEqual(name(["anchor@g", "mate@h"]), "anchor")

    def test_setup_04a_draft_names_kept_unique(self):
        groups = [["a@m", "b@m"], ["c@n"], ["d@n"], ["e@o", "f@o"]]
        edits = self.rig.RigEdits({"default": [], "rigs": {"base": {"plugins": ["a@m", "b@m"]}, "o": {"plugins": []}}},
                                  ENABLED, groups, INSTALLED)
        self.assertEqual([name for name, _ in edits.drafts()], ["c", "d", "o-2"])

    def test_setup_04b_one_draft_per_marketplace(self):
        self.assertEqual(self.first_run().drafts(), [("n", ["c@n", "d@n"]), ("o", ["e@o", "f@o"])])

    def test_setup_04_draft_kept_under_a_name(self):
        edits = self.first_run()
        edits.keep_draft(0, "web")
        self.assertEqual(edits.rigs["web"], ["c@n", "d@n"])
        self.assertEqual(edits.drafts(), [("o", ["e@o", "f@o"])])

    def test_editor_01_base_first_full_last(self):
        edits = self.existing()
        edits.create("Zed")
        self.assertEqual(edits.order(), ["base", "api", "web", "Zed", "full"])

    def test_editor_02_candidates_are_installed_and_named_plugins(self):
        config = {"default": [], "rigs": {"base": {"plugins": ["z@gone"]}}}
        edits = self.rig.RigEdits(config, ["a@m"], [], INSTALLED)
        self.assertEqual(set(edits.candidates), {*INSTALLED, "z@gone"})

    def test_editor_04_base_plugins_shown_in_every_other_rig(self):
        edits = self.existing()
        self.assertEqual(edits.inherited("web"), {"a@m": "base", "b@m": "base"})
        self.assertEqual(edits.inherited("base"), {})

    def test_editor_06_default_toggles(self):
        edits = self.existing()
        edits.make_default("api")
        self.assertEqual(edits.default, ["web", "api"])
        edits.make_default("web")
        self.assertEqual(edits.default, ["api"])
        with self.assertRaisesRegex(self.rig.Refused, "loads in every launch"):
            edits.make_default("base")

    def test_editor_13_plugins_move_between_base_and_a_rig(self):
        edits = self.existing()
        edits.move_down("web", "b@m")
        self.assertEqual((edits.rigs["base"], edits.rigs["web"]), (["a@m"], ["b@m", "c@n"]))
        edits.move_up("web", "c@n")
        self.assertEqual((edits.rigs["base"], edits.rigs["web"]), (["a@m", "c@n"], ["b@m"]))
        edits.move_down("web", "e@o")
        self.assertEqual(edits.rigs["web"], ["b@m", "e@o"])
        edits.move_up("base", "f@o")
        self.assertEqual(edits.rigs["base"], ["a@m", "c@n", "f@o"])
        with self.assertRaisesRegex(self.rig.Refused, "on base already"):
            edits.move_up("web", "a@m")
        with self.assertRaisesRegex(self.rig.Refused, "Select the rig"):
            edits.move_down("base", "d@n")

    def test_editor_07_base_and_full_kept(self):
        edits = self.existing()
        for name in ("base", "full"):
            with self.assertRaisesRegex(self.rig.Refused, "can't be deleted"):
                edits.delete(name)
        edits.delete("web")
        self.assertNotIn("web", edits.rigs)
        self.assertEqual(edits.default, [])

    def test_editor_11_rename_carries_to_the_default(self):
        edits = self.existing()
        edits.rename("web", "front")
        self.assertEqual(edits.default, ["front"])
        self.assertEqual(edits.order(), ["base", "api", "front", "full"])
        for name in ("base", "full"):
            with self.assertRaisesRegex(self.rig.Refused, "can't be renamed"):
                edits.rename(name, "core")

    def test_editor_10_refused_rename_changes_nothing(self):
        edits = self.existing()
        for taken in ("api", "full"):
            with self.assertRaisesRegex(self.rig.Refused, "already a rig"):
                edits.rename("web", taken)
        self.assertIn("web", edits.rigs)

    def test_editor_12_rigs_listed_alphabetically_as_they_change(self):
        edits = self.existing()
        edits.create("zeta")
        edits.create("Alpha")
        self.assertEqual(edits.order(), ["base", "Alpha", "api", "web", "zeta", "full"])
        edits.rename("zeta", "beta")
        self.assertEqual(edits.order(), ["base", "Alpha", "api", "beta", "web", "full"])

    def test_editor_08_saved_in_alphabetical_order(self):
        config = {"default": ["web", "api"], "clones": {}, "rigs": {
            "web": {"plugins": ["z@m", "a@m"]}, "base": {"plugins": ["b@m"]}, "api": {"plugins": []}}}
        edits = self.rig.RigEdits(config, [], [], [])
        edits.toggle("base", "a@m", True)
        self.assertEqual(edits.rigs["base"], ["a@m", "b@m"])
        with tempfile.TemporaryDirectory() as home:
            previous, os.environ["HOME"] = os.environ["HOME"], home
            try:
                edits.save()
                import yaml
                saved = yaml.safe_load((Path(home) / ".rig" / "rigs.yml").read_text())
            finally:
                os.environ["HOME"] = previous
        self.assertEqual(list(saved["rigs"]), ["base", "api", "web"])
        self.assertEqual(saved["rigs"]["web"]["plugins"], ["a@m", "z@m"])
        self.assertEqual(saved["default"], ["api", "web"])

    def test_editor_05_new_rig_name_checked(self):
        edits = self.existing()
        for taken in ("web", "full"):
            with self.assertRaisesRegex(self.rig.Refused, "already a rig"):
                edits.create(taken)
        with self.assertRaisesRegex(self.rig.Refused, "letters, digits"):
            edits.create("no spaces")


class Editor(unittest.IsolatedAsyncioTestCase):
    """The rig editor on screen, driven by keys and clicks."""

    rig = load_rig()

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._home = os.environ.get("HOME")
        os.environ["HOME"] = self._tmp.name

    def tearDown(self):
        os.environ["HOME"] = self._home
        self._tmp.cleanup()

    NAMED = ["a@m", "b@m", "c@n", "d@n"]

    def existing(self):
        return self.rig.RigEdits(three_rigs(), self.NAMED, [], self.NAMED)

    def saved(self) -> dict:
        import yaml
        return yaml.safe_load((Path(self._tmp.name) / ".rig" / "rigs.yml").read_text())

    def running(self, edits):
        app = self.rig.editor_app(edits)
        return app, app.run_test(size=(110, 30))

    def options(self, app) -> list[tuple[str, bool, bool]]:
        """(plugin, selected, locked) for each row of the plugins pane."""
        listing = app.screen.query_one("#plugins")
        rows = [listing.get_option_at_index(i) for i in range(listing.option_count)]
        return [(row.value, row.value in listing.selected, row.disabled) for row in rows]

    def rows(self, app) -> list[tuple[str, str | int]]:
        return [node.data for node in app.screen.query_one("#rigs").root.children]

    def test_setup_04a_groups_read_from_the_settings_file(self):
        path = Path(self._tmp.name) / ".claude" / "settings.json"
        (path.parent / "plugins").mkdir(parents=True)
        path.write_text(GROUPED_SETTINGS)
        (path.parent / "plugins" / "installed_plugins.json").write_text(
            json.dumps({"plugins": {i: [{"scope": "user"}] for i in INSTALLED}}))
        edits = self.rig.open_edits()
        self.assertEqual(edits.rigs["base"], ENABLED)
        edits.toggle("base", "e@o", False)
        self.assertEqual(edits.drafts(), [("o", ["e@o", "f@o"])])

    async def test_editor_01_base_at_the_top_full_at_the_bottom(self):
        app, running = self.running(self.existing())
        async with running as pilot:
            await pilot.pause()
            self.assertEqual(self.rows(app), [("rig", "base"), ("rig", "api"), ("rig", "web"), ("rig", "full")])
            labels = [str(node.label) for node in app.screen.query_one("#rigs").root.children]
            self.assertEqual([label[-1] for label in labels], ["┐", "│", "│", "┘"])
            self.assertEqual([label.split()[0] for label in labels], ["base", "api", "★", "full"])
            self.assertTrue(labels[0].startswith("  base") and labels[1].startswith("    api"))
            self.assertEqual(app.screen.border_title, "rig setup")

    async def test_editor_03_space_and_click_toggle_plugins(self):
        edits = self.rig.RigEdits(None, ENABLED, [], INSTALLED)
        app, running = self.running(edits)
        async with running as pilot:
            await pilot.pause()
            self.assertIs(app.screen.focused, app.screen.query_one("#rigs"))
            await pilot.press("tab", "space")
            await pilot.pause()
            self.assertNotIn("a@m", edits.rigs["base"])
            row = [value for value, _, _ in self.options(app)].index("f@o")
            await pilot.click(app.screen.query_one("#plugins"), offset=(4, row + 1))
            await pilot.pause()
            self.assertIn("f@o", edits.rigs["base"])
            await pilot.press("s")
            await pilot.pause()
        self.assertEqual(self.saved()["rigs"]["base"], {"plugins": ["b@m", "c@n", "d@n", "e@o", "f@o"]})

    async def test_editor_04_base_box_then_the_rigs_own(self):
        app, running = self.running(self.existing())
        async with running as pilot:
            await pilot.pause()
            app.screen.query_one("#rigs").focus()
            await pilot.press("down")
            await pilot.pause()
            base_box = app.screen.query_one("#base-plugins")
            self.assertEqual((base_box.border_title, app.screen.query_one("#plugins").border_title), ("base", "api"))
            self.assertEqual([base_box.get_option_at_index(i).value for i in range(base_box.option_count)],
                             ["a@m", "b@m"])
            self.assertEqual([value for value, _, _ in self.options(app)], ["c@n", "d@n"])
            app.screen.query_one("#rigs").focus()
            await pilot.press("up")
            await pilot.pause()
            self.assertFalse(base_box.display)

    async def test_editor_04_toggling_a_base_plugin_moves_it_into_the_rig(self):
        edits = self.existing()
        app, running = self.running(edits)
        async with running as pilot:
            await pilot.pause()
            app.screen.query_one("#rigs").focus()
            await pilot.press("down")
            app.screen.query_one("#base-plugins").focus()
            await pilot.press("space")
            await pilot.pause()
            self.assertEqual((edits.rigs["base"], edits.rigs["api"]), (["b@m"], ["a@m", "d@n"]))
            listing = app.screen.query_one("#plugins")
            self.assertIs(app.screen.focused, listing)
            self.assertEqual(listing.get_option_at_index(listing.highlighted).value, "a@m")

    async def test_editor_04_arrows_cross_from_the_base_box_into_the_rigs(self):
        app, running = self.running(self.existing())
        async with running as pilot:
            await pilot.pause()
            app.screen.query_one("#rigs").focus()
            await pilot.press("down")
            base_box = app.screen.query_one("#base-plugins")
            base_box.focus()
            base_box.highlighted = 0
            await pilot.press("down", "down")
            await pilot.pause()
            listing = app.screen.query_one("#plugins")
            self.assertIs(app.screen.focused, listing)
            self.assertEqual(listing.highlighted, 0)
            await pilot.press("up")
            self.assertIs(app.screen.focused, base_box)

    async def test_editor_13_keys_move_a_plugin_down_and_back(self):
        edits = self.existing()
        app, running = self.running(edits)
        async with running as pilot:
            await pilot.pause()
            app.screen.query_one("#rigs").focus()
            await pilot.press("down")
            base_box = app.screen.query_one("#base-plugins")
            base_box.focus()
            base_box.highlighted = 0
            await pilot.press("greater_than_sign")
            await pilot.pause()
            self.assertEqual((edits.rigs["base"], edits.rigs["api"]), (["b@m"], ["a@m", "d@n"]))
            await pilot.press("less_than_sign")
            await pilot.pause()
            self.assertEqual((edits.rigs["base"], edits.rigs["api"]), (["a@m", "b@m"], ["d@n"]))

    async def test_editor_13_push_onto_base_from_base_and_space_named_in_the_footer(self):
        edits = self.existing()
        app, running = self.running(edits)
        async with running as pilot:
            await pilot.pause()
            listing = app.screen.query_one("#plugins")
            listing.highlighted = [value for value, _, _ in self.options(app)].index("c@n")
            await pilot.press("less_than_sign")
            await pilot.pause()
            self.assertIn("c@n", edits.rigs["base"])
            self.assertIn("space", [binding.key for binding in type(listing).BINDINGS if binding.show])

    async def test_editor_14_x_dismisses_a_draft_for_good(self):
        edits = self.rig.RigEdits(None, ENABLED, [], INSTALLED)
        edits.toggle("base", "e@o", False)
        app, running = self.running(edits)
        async with running as pilot:
            await pilot.pause()
            app.screen.query_one("#rigs").focus()
            await pilot.press("down", "down", "x", "s")
            await pilot.pause()
            self.assertEqual(self.rows(app), [("rig", "base"), ("rig", "full")])
        self.assertEqual(self.saved()["dismissed"], ["e@o", "f@o"])
        reopened = self.rig.RigEdits(self.rig.load_config(), ENABLED, [], INSTALLED)
        self.assertEqual(reopened.drafts(), [])

    async def test_editor_messages_replace_each_other(self):
        app, running = self.running(self.existing())
        async with running as pilot:
            await pilot.pause()
            await pilot.press("x", "f2", "x")
            await pilot.pause()
            self.assertEqual(len(app._notifications), 1)

    async def test_editor_06_shows_what_a_plain_launch_loads(self):
        app, running = self.running(self.existing())
        async with running as pilot:
            await pilot.pause()
            self.assertEqual(app.screen.query_one("#rigs").border_subtitle, "claude launches base + web")

    async def test_editor_02_full_shows_every_installed_plugin_locked(self):
        app, running = self.running(self.existing())
        async with running as pilot:
            await pilot.pause()
            app.screen.query_one("#rigs").focus()
            await pilot.press("down", "down", "down")
            await pilot.pause()
            self.assertEqual(self.options(app), [(p, True, True) for p in self.NAMED])

    async def test_pin_12_editor_marks_pinned_plugins(self):
        app, running = self.running(self.rig.RigEdits(three_rigs(), self.NAMED, [], self.NAMED, {"b"}))
        async with running as pilot:
            await pilot.pause()
            listing = app.screen.query_one("#plugins")
            prompts = [str(listing.get_option_at_index(i).prompt) for i in range(listing.option_count)]
            self.assertEqual(prompts, ["a@m", "b@m 📌", "c@n", "d@n"])

    async def test_setup_04_draft_kept_from_the_editor(self):
        edits = self.rig.RigEdits(None, ENABLED, [], INSTALLED)
        app, running = self.running(edits)
        async with running as pilot:
            await pilot.pause()
            await pilot.press("tab", "down", "down", "space", "down", "space", "down", "space")
            await pilot.pause()
            app.screen.query_one("#rigs").focus()
            await pilot.press("down", "down", "s")
            await pilot.pause()
            self.assertEqual(app.screen.query_one("#name").value, "n")
            await pilot.press("enter")
            await pilot.pause()
            self.assertEqual(self.rows(app), [("rig", "base"), ("rig", "n"), ("heading", 0), ("draft", 0), ("rig", "full")])
        rigs = self.saved()["rigs"]
        self.assertEqual(rigs["n"], {"plugins": ["c@n", "d@n"]})
        self.assertNotIn("o", rigs)

    async def test_editor_new_rig_from_keys(self):
        edits = self.existing()
        app, running = self.running(edits)
        async with running as pilot:
            await pilot.pause()
            await pilot.press("n")
            await pilot.pause()
            await pilot.press(*"tools", "enter")
            await pilot.pause()
            self.assertEqual(self.rows(app)[2], ("rig", "tools"))
        self.assertEqual(edits.rigs["tools"], [])

    async def test_editor_10_double_click_opens_a_rig_for_renaming(self):
        edits = self.existing()
        app, running = self.running(edits)
        async with running as pilot:
            await pilot.pause()
            await pilot.double_click("#rigs", offset=(8, 2))
            await pilot.pause()
            name = app.screen.query_one("#name")
            self.assertEqual(name.value, "api")
            name.value = "back"
            await pilot.press("enter")
            await pilot.pause()
            self.assertEqual(self.rows(app), [("rig", "base"), ("rig", "back"), ("rig", "web"), ("rig", "full")])

    async def test_setup_04_s_names_a_draft_and_keeps_it(self):
        edits = self.rig.RigEdits(None, ENABLED, [], INSTALLED)
        edits.toggle("base", "e@o", False)
        app, running = self.running(edits)
        async with running as pilot:
            await pilot.pause()
            app.screen.query_one("#rigs").focus()
            await pilot.press("down", "down", "s")
            await pilot.pause()
            self.assertEqual(app.screen.query_one("#name").value, "o")
            await pilot.press("enter")
            await pilot.pause()
        self.assertEqual(self.saved()["rigs"]["o"], {"plugins": ["e@o", "f@o"]})

    async def test_editor_10_f2_opens_a_rig_for_renaming(self):
        app, running = self.running(self.existing())
        async with running as pilot:
            await pilot.pause()
            app.screen.query_one("#rigs").focus()
            await pilot.press("down", "f2")
            await pilot.pause()
            self.assertEqual(app.screen.query_one("#name").value, "api")

    async def test_editor_06_default_from_keys(self):
        edits = self.existing()
        app, running = self.running(edits)
        async with running as pilot:
            await pilot.pause()
            app.screen.query_one("#rigs").focus()
            await pilot.press("down", "d")
            await pilot.pause()
        self.assertEqual(edits.default, ["web", "api"])

    async def test_editor_07_refusals_shown(self):
        edits = self.existing()
        app, running = self.running(edits)
        async with running as pilot:
            await pilot.pause()
            await pilot.press("x")
            await pilot.pause()
            self.assertIn("base", edits.rigs)
            self.assertIn("can't be deleted", str(list(app._notifications)[0].message))
            await pilot.press("f2")
            await pilot.pause()
            self.assertIn("can't be renamed", str(list(app._notifications)[0].message))

    async def test_editor_09_quit_with_unsaved_changes_saves_by_default(self):
        edits = self.existing()
        app, running = self.running(edits)
        async with running as pilot:
            await pilot.pause()
            await pilot.press("tab", "space", "q")
            await pilot.pause()
            self.assertEqual(type(app.screen).__name__, "SaveOnQuit")
            await pilot.press("escape")
            await pilot.pause()
            self.assertEqual(type(app.screen).__name__, "Editor")
            await pilot.press("q", "q")
            await pilot.pause()
            self.assertFalse(app.is_running)
        self.assertEqual(self.saved()["rigs"]["base"], {"plugins": ["b@m"]})

    async def test_editor_dropped_keys_do_nothing(self):
        edits = self.existing()
        app, running = self.running(edits)
        async with running as pilot:
            await pilot.pause()
            await pilot.press("enter", "e", "delete", "escape", "tab", "enter", "shift+up", "ctrl+s")
            await pilot.pause()
            self.assertTrue(app.is_running)
            self.assertEqual(type(app.screen).__name__, "Editor")
            self.assertEqual(edits.rigs, {name: rig["plugins"] for name, rig in three_rigs()["rigs"].items()})
            self.assertFalse((Path(self._tmp.name) / ".rig" / "rigs.yml").exists())

    async def test_editor_09_q_twice_saves_and_quits(self):
        app, running = self.running(self.existing())
        async with running as pilot:
            await pilot.pause()
            await pilot.press("tab", "space", "q", "q")
            await pilot.pause()
            self.assertFalse(app.is_running)
        self.assertEqual(self.saved()["rigs"]["base"], {"plugins": ["b@m"]})

    async def test_editor_09_quit_can_discard(self):
        edits = self.existing()
        app, running = self.running(edits)
        async with running as pilot:
            await pilot.pause()
            await pilot.press("tab", "space", "q", "d")
            await pilot.pause()
            self.assertFalse(app.is_running)
        self.assertFalse((Path(self._tmp.name) / ".rig" / "rigs.yml").exists())

    async def test_editor_09_quit_without_changes_asks_nothing(self):
        app, running = self.running(self.existing())
        async with running as pilot:
            await pilot.pause()
            await pilot.press("q")
            await pilot.pause()
            self.assertFalse(app.is_running)
        self.assertFalse((Path(self._tmp.name) / ".rig" / "rigs.yml").exists())

    async def test_editor_08_save_key(self):
        app, running = self.running(self.existing())
        async with running as pilot:
            await pilot.pause()
            await pilot.press("tab", "space", "s", "q")
            await pilot.pause()
            self.assertFalse(app.is_running)
        self.assertEqual(self.saved()["rigs"]["base"], {"plugins": ["b@m"]})


class LaunchConfirmation(unittest.IsolatedAsyncioTestCase):
    """The launch confirmation on screen, driven by keys."""

    rig = load_rig()
    RIGS = {"base": {"plugins": ["a@m", "inrig@m"]}, "web": {"plugins": ["here@m", "z@m"]}}
    INSTALLED = {"a@m", "inrig@m", "here@m", "outside@m"}

    def running(self):
        pin = lambda name: {"plugin": name, "path": f"/src/{name}", "pinned_at": "2026-01-01T00:00:00+00:00"}
        pins = [pin("inrig"), pin("here"), pin("outside")]
        plan_for = lambda names: self.rig.plan(names, self.RIGS, self.INSTALLED, pins, Path("/src/here"))
        app = self.rig.launch_app(plan_for, self.rig.rig_order(self.RIGS), plan_for(["web"]), False)
        return app, app.run_test(size=(110, 40))

    def choices(self, app) -> dict[str, bool]:
        return {pin["plugin"]: load for pin, load in app.return_value[1]}

    def shown(self, app) -> str:
        return str(app.query_one("#plugin-lines").render())

    async def test_launch_05_rigs_and_their_plugins_shown(self):
        app, running = self.running()
        async with running as pilot:
            await pilot.pause()
            rigs = app.query_one("#rigs")
            rows = [rigs.get_option_at_index(i) for i in range(rigs.option_count)]
            self.assertEqual([(r.value, r.value in rigs.selected, r.disabled) for r in rows],
                             [("base", True, True), ("web", True, False), ("full", False, False)])
            self.assertEqual(app.query_one("#plugins").border_title, "base + web: 4 plugins")
            self.assertIn("a@m  from base", self.shown(app))
            self.assertIn("inrig@m  from base  📌 /src/inrig", self.shown(app))
            self.assertIn("z@m  from web  not installed; installs at launch", self.shown(app))
            await pilot.press("enter")
        self.assertEqual(app.return_value[0], ["web"])
        self.assertEqual(self.choices(app), {"inrig": True, "here": True, "outside": False})

    async def test_launch_05_only_pins_the_rigs_leave_open_are_offered(self):
        app, running = self.running()
        async with running as pilot:
            await pilot.pause()
            listing = app.query_one("#pins")
            values = [listing.get_option_at_index(i).value for i in range(listing.option_count)]
            self.assertEqual(values, [1, 2])
            self.assertEqual(listing.selected, [1])

    async def test_launch_05_space_toggles_a_pin(self):
        app, running = self.running()
        async with running as pilot:
            await pilot.pause()
            await pilot.press("space", "down", "space", "enter")
        self.assertEqual(self.choices(app), {"inrig": True, "here": False, "outside": True})

    async def test_launch_05_changing_rigs_updates_plugins_and_keeps_pin_choices(self):
        app, running = self.running()
        async with running as pilot:
            await pilot.pause()
            await pilot.press("down", "space")
            rigs = app.query_one("#rigs")
            rigs.focus()
            rigs.highlighted = 1
            await pilot.press("space")
            await pilot.pause()
            self.assertEqual(app.query_one("#plugins").border_title, "base: 2 plugins")
            self.assertEqual(app.query_one("#pins").selected, [1, 2])
            await pilot.press("down", "space")
            await pilot.pause()
            self.assertEqual(app.query_one("#plugins").border_title, "all 4 plugins")
            self.assertIn("outside@m  from full", self.shown(app))
            self.assertNotIn("z@m", self.shown(app))
            await pilot.press("enter")
        self.assertEqual(app.return_value[0], ["full"])
        self.assertEqual(self.choices(app), {"inrig": True, "here": True, "outside": True})

    async def test_launch_05_q_cancels(self):
        app, running = self.running()
        async with running as pilot:
            await pilot.pause()
            await pilot.press("q")
        self.assertIsNone(app.return_value)


class Picker(unittest.IsolatedAsyncioTestCase):
    """The --select picker on screen, driven by keys and clicks."""

    rig = load_rig()
    RIGS = {"base": {"plugins": ["a@m", "inrig@m"]}, "web": {"plugins": ["here@m", "z@m"]}}
    INSTALLED = ["a@m", "here@m", "inrig@m", "outside@m"]

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._home = os.environ.get("HOME")
        os.environ["HOME"] = self._tmp.name

    def tearDown(self):
        os.environ["HOME"] = self._home
        self._tmp.cleanup()

    def running(self, selected=("web",)):
        pin = lambda name: {"plugin": name, "path": f"/src/{name}", "pinned_at": "2026-01-01T00:00:00+00:00"}
        pins = [pin("inrig"), pin("here"), pin("outside")]
        self.rig.write_pins(pins)
        plan_for = lambda names, *picks: self.rig.plan(names, self.RIGS, set(self.INSTALLED), pins, Path("/src/here"), *picks)
        columns = [{"name": name, "default": name == "web",
                    "plugins": self.INSTALLED if name == "full" else self.RIGS[name]["plugins"]}
                   for name in self.rig.rig_order(self.RIGS)]
        app = self.rig.select_app(plan_for, columns, self.INSTALLED, pins, plan_for(list(selected)), False)
        self.layout = app.LAYOUT
        return app, app.run_test(size=(110, 30))

    def summary(self, app) -> str:
        return str(app.query_one("#summary").render())

    def lines(self, app) -> list[str]:
        return [line.rstrip() for line in str(app.query_one("#graph").render()).splitlines()]

    def choices(self, app) -> dict[str, bool]:
        return {pin["plugin"]: load for pin, load in app.return_value[1]}

    def x_of(self, column: int) -> int:
        """A terminal column inside the graph's column: -1 the plugin's name, 0.. a rig."""
        at = 0
        for text, piece in self.layout.header():
            if piece == column and text.strip():
                return at + 1
            at += self.rig.cells(text)

    async def test_launch_07_the_graph_with_full_and_the_pins(self):
        app, running = self.running()
        async with running as pilot:
            await pilot.pause()
            lines = self.lines(app)
            self.assertEqual(lines, ["plugin        base  ★web  full",
                                     "               ✓     ✓            ★ = default  ✓ = loads",
                                     "a@m            ●     ·     ●",
                                     "inrig@m 📌     ●     ·     ●",
                                     "here@m 📌      ·     ●     ●",
                                     "z@m            ·     ●     ·    installs at launch",
                                     "outside@m 📌   ·     ·     ●"])
            self.assertEqual(lines[0], self.layout.text().splitlines()[0])
            self.assertEqual(self.summary(app), "base + web: 4 plugins")
            await pilot.press("l")
        self.assertEqual(app.return_value[0], ["web"])
        self.assertEqual(self.choices(app), {"inrig": True, "here": True, "outside": False})

    async def test_launch_07_header_names_the_command_and_rows_never_wrap(self):
        app, running = self.running()
        async with running as pilot:
            await pilot.pause()
            self.assertEqual(app.screen.border_title, "rig --select")
            await pilot.resize_terminal(40, 30)
            await pilot.pause()
            graph = app.query_one("#graph")
            self.assertEqual(graph.size.width, max(self.rig.cells(line) for line in self.lines(app)))
            self.assertEqual(graph.size.height, len(self.layout.rows) + 2)

    def test_launch_07_invocation_is_the_command_line_typed(self):
        argv = sys.argv
        try:
            for typed, shown in ((["rig", "--select"], "rig --select"), (["rig", "use", "web", "--select"], "rig use web --select"),
                                 (["rig", "claude", "--select"], "claude --select")):
                sys.argv = typed
                self.assertEqual(self.rig.invocation(), shown)
        finally:
            sys.argv = argv

    async def test_launch_07_tab_runs_across_the_rigs(self):
        app, running = self.running()
        async with running as pilot:
            await pilot.pause()
            graph = app.query_one("#graph")
            await pilot.press("tab")
            self.assertEqual(graph.column, 2)
            await pilot.press("tab")
            self.assertEqual(graph.column, 1)
            await pilot.press("shift+tab")
            self.assertEqual(graph.column, 2)
            self.assertIs(app.focused, graph)

    async def test_launch_07_keys_toggle_rigs_and_never_reach_base(self):
        app, running = self.running()
        async with running as pilot:
            await pilot.pause()
            await pilot.press("space", "right", "space")
            self.assertEqual(self.summary(app), "all 4 plugins")
            await pilot.press("left", "left", "left", "space")
            self.assertEqual(self.summary(app), "base + web: 4 plugins")
            self.assertEqual(app.query_one("#graph").column, 1)
            await pilot.press("l")
        self.assertEqual(app.return_value[0], ["web"])

    async def test_launch_07_full_goes_alone(self):
        app, running = self.running(selected=("web",))
        async with running as pilot:
            await pilot.pause()
            await pilot.click("#graph", offset=(self.x_of(2), 0))
            self.assertEqual(self.summary(app), "all 4 plugins")
            await pilot.click("#graph", offset=(self.x_of(1), 0))
            self.assertEqual(self.summary(app), "base + web: 4 plugins")
            await pilot.press("l")
        self.assertEqual(app.return_value[0], ["web"])

    async def test_launch_07_a_click_on_base_toggles_nothing(self):
        app, running = self.running(selected=())
        async with running as pilot:
            await pilot.pause()
            await pilot.click("#graph", offset=(self.x_of(0), 0))
            self.assertEqual(self.summary(app), "base: 2 plugins")
            await pilot.press("l")
        self.assertEqual(app.return_value[0], [])

    async def test_launch_11_a_click_on_a_row_picks_or_drops_its_plugin(self):
        app, running = self.running()
        async with running as pilot:
            await pilot.pause()
            await pilot.click("#graph", offset=(self.x_of(-1), 6))
            await pilot.click("#toggle")
            self.assertEqual(self.summary(app), "base + web + outside@m: 5 plugins")
            self.assertEqual([app.state(c) for c in range(3)], ["on", "on", "off"])
            await pilot.click("#graph", offset=(self.x_of(0), 2))
            self.assertEqual(self.summary(app), "base + web + outside@m - a@m: 4 plugins")
            self.assertEqual(app.state(0), "partial")
            self.assertEqual(self.lines(app)[1].split()[:2], ["◐", "✓"])
            await pilot.press("l")
        self.assertEqual(app.return_value[2:], (["outside@m"], ["a@m"]))

    async def test_launch_11_a_partly_loaded_rig_comes_in_whole(self):
        app, running = self.running(selected=())
        async with running as pilot:
            await pilot.pause()
            await pilot.click("#graph", offset=(self.x_of(-1), 4))
            await pilot.click("#toggle")
            self.assertEqual(self.summary(app), "base + here@m: 3 plugins")
            self.assertEqual(app.state(1), "partial")
            await pilot.click("#graph", offset=(self.x_of(1), 0))
            self.assertEqual(self.summary(app), "base + web: 4 plugins")
            await pilot.press("down", "enter", "left", "space")
            self.assertEqual(self.summary(app), "base - a@m: 1 plugin")
            await pilot.click("#graph", offset=(self.x_of(0), 0))
            self.assertEqual(self.summary(app), "base: 2 plugins")
            await pilot.press("l")
        self.assertEqual(app.return_value[2:], ([], []))

    async def test_pin_13_the_dialog_loads_or_skips_the_checkout(self):
        app, running = self.running()
        async with running as pilot:
            await pilot.pause()
            await pilot.press("down", "down", "down", "enter")
            await pilot.pause()
            self.assertEqual(str(app.screen.query_one("#pin-load").label), "Skip checkout")
            await pilot.click("#pin-load")
            await pilot.press("down", "down", "enter")
            await pilot.pause()
            await pilot.click("#pin-load")
            await pilot.press("up", "up", "up", "enter")
            await pilot.pause()
            self.assertEqual(len(app.screen.query("#pin-load")), 0)
            await pilot.press("escape", "l")
        self.assertEqual(self.choices(app), {"inrig": True, "here": False, "outside": True})

    async def test_launch_07_e_leaves_for_the_editor_with_the_rigs_chosen(self):
        app, running = self.running()
        async with running as pilot:
            await pilot.pause()
            await pilot.press("right", "space", "e")
        self.assertEqual(app.return_value, ("edit", ["full"], [], []))

    async def test_launch_13_the_rocket_at_the_end_of_the_footer_launches(self):
        app, running = self.running()
        async with running as pilot:
            await pilot.pause()
            rocket, footer = app.query_one("#launch"), app.query_one("Footer")
            self.assertIn("Launch", str(rocket.render()))
            self.assertIn("🚀", str(rocket.render()))
            self.assertEqual(rocket.region.right, footer.region.right + rocket.region.width)
            self.assertEqual(rocket.region.y, footer.region.y)
            first = rocket.tick
            await pilot.pause(0.4)
            self.assertGreater(rocket.tick, first)
            # pilot.click measures the screen less its border, so it can't reach the bar on the border's inner edge
            rocket.on_click()
            await pilot.pause()
        self.assertEqual(app.return_value[0], ["web"])

    async def test_launch_11_partly_loaded_named_in_the_legend_only_while_a_rig_is(self):
        app, running = self.running()
        async with running as pilot:
            await pilot.pause()
            self.assertNotIn("◐ = part", self.lines(app)[1])
            await pilot.press("down", "enter")
            self.assertIn("★ = default  ✓ = loads  ◐ = part", self.lines(app)[1])
            await pilot.press("enter")
            self.assertNotIn("◐ = part", self.lines(app)[1])

    async def test_pin_13_a_click_on_a_pin_opens_it_and_escape_or_the_x_closes_it(self):
        app, running = self.running()
        async with running as pilot:
            await pilot.pause()
            pin_x = self.rig.cells("inrig@m ")
            await pilot.click("#graph", offset=(pin_x, 3))
            await pilot.pause()
            self.assertEqual(type(app.screen).__name__, "PinDialog")
            self.assertEqual(app.focused.id, "unpin")
            details = str(app.screen.query_one("#pin-details").render())
            self.assertIn("/src/inrig", details)
            self.assertIn("in these rigs, so the checkout loads", details)
            await pilot.press("escape")
            self.assertNotEqual(type(app.screen).__name__, "PinDialog")
            await pilot.click("#graph", offset=(pin_x, 3))
            await pilot.pause()
            await pilot.click("#pin-close")
            await pilot.pause()
            self.assertNotEqual(type(app.screen).__name__, "PinDialog")
            self.assertEqual(self.summary(app), "base + web: 4 plugins")
            await pilot.press("l")
        self.assertEqual(self.choices(app), {"inrig": True, "here": True, "outside": False})
        self.assertEqual(len(self.rig.read_pins()), 3)

    async def test_pin_13_a_click_anywhere_on_a_pinned_row_opens_it_to_toggle_the_plugin(self):
        app, running = self.running()
        async with running as pilot:
            await pilot.pause()
            await pilot.click("#graph", offset=(self.x_of(0), 3))
            await pilot.pause()
            self.assertEqual(type(app.screen).__name__, "PinDialog")
            self.assertEqual(self.summary(app), "base + web: 4 plugins")
            await pilot.click("#toggle")
            await pilot.pause()
            self.assertNotEqual(type(app.screen).__name__, "PinDialog")
            self.assertEqual(self.summary(app), "base + web - inrig@m: 3 plugins")
            await pilot.click("#graph", offset=(self.x_of(-1), 2))
            await pilot.pause()
            self.assertEqual(self.summary(app), "base + web - inrig@m - a@m: 2 plugins")
            await pilot.press("l")
        self.assertEqual(app.return_value[3], ["inrig@m", "a@m"])

    async def test_pin_13_enter_unpins(self):
        app, running = self.running()
        async with running as pilot:
            await pilot.pause()
            await pilot.click("#graph", offset=(self.rig.cells("inrig@m "), 3))
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
            self.assertNotEqual(type(app.screen).__name__, "PinDialog")
            self.assertEqual(self.lines(app)[3].rstrip(), "inrig@m        ●     ·     ●")
            self.assertEqual([p["plugin"] for p in self.rig.read_pins()], ["here", "outside"])
            await pilot.press("l")
        self.assertEqual(self.choices(app), {"here": True, "outside": False})

    async def test_launch_07_space_and_enter_toggle_what_the_cursor_is_on_and_l_launches(self):
        app, running = self.running()
        async with running as pilot:
            await pilot.pause()
            graph = app.query_one("#graph")
            await pilot.press("enter")
            self.assertEqual(self.summary(app), "base: 2 plugins")
            await pilot.press("space")
            self.assertEqual(self.summary(app), "base + web: 4 plugins")
            await pilot.press("down", "space")
            self.assertEqual(self.summary(app), "base + web - a@m: 3 plugins")
            await pilot.press("enter")
            self.assertEqual(self.summary(app), "base + web: 4 plugins")
            await pilot.press("space", "right")
            self.assertEqual((graph.row, graph.column), (-1, 1))
            await pilot.press("down", "down", "enter")
            await pilot.pause()
            self.assertEqual(type(app.screen).__name__, "PinDialog")
            await pilot.press("l")
            self.assertIsNone(app.return_value)
            await pilot.press("escape", "l")
        self.assertEqual(app.return_value[0], ["web"])
        self.assertEqual(app.return_value[3], ["a@m"])

    async def test_launch_07_shift_enter_launches(self):
        app, running = self.running()
        async with running as pilot:
            await pilot.pause()
            await pilot.press("shift+enter")
        self.assertEqual(app.return_value[0], ["web"])

    async def test_launch_07_the_legend_names_only_the_marks_on_screen(self):
        app, running = self.running()
        async with running as pilot:
            await pilot.pause()
            self.assertTrue(self.lines(app)[1].endswith("★ = default  ✓ = loads"))
            await pilot.press("space")
            self.assertTrue(self.lines(app)[1].endswith("★ = default"))
            await pilot.press("down", "enter")
            self.assertTrue(self.lines(app)[1].endswith("★ = default  ◐ = part"))

    async def test_launch_07_q_cancels(self):
        app, running = self.running()
        async with running as pilot:
            await pilot.pause()
            await pilot.press("q")
        self.assertIsNone(app.return_value)


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
                         "default: [web-dev]\nclones:\n  github.com: ~/src\nrigs:\n  base:\n    plugins:\n    - a@m\n"
                         "  web-dev:\n    plugins: []\n"):
                path.write_text(text)
                names = subprocess.run(["awk", self.awk_program("_rig_names"), str(path)],
                                       capture_output=True, text=True).stdout.split()
                self.assertIn(names, (["base", "web"], ["base", "web-dev"]))

    STUBS = textwrap.dedent("""\
        compadd() {
          local -a a=("$@")
          if [[ $a[-2] == -a ]]; then print -rl -- ${(P)a[-1]}; else print -rl -- ${a[$a[(i)--]+1,-1]}; fi
        }
        _default() { print -r -- _default }
        words=("$@"); CURRENT=$#; PREFIX=$words[-1]; IPREFIX=; service=rig
        _rig
        print -r -- "IPREFIX=$IPREFIX"
        """)

    def complete(self, *words: str) -> list[str]:
        """What `rig <words>` completes to with the cursor at the end of the last word, read through stand-ins
        for the zsh builtins only a completion widget can call."""
        script = self.rig.ZSH_COMPLETION.replace('\n_rig "$@"\n', "\n") + self.STUBS
        result = subprocess.run(["zsh", "-f", "-c", script, "zsh", "rig", *words], capture_output=True, text=True,
                                env={**os.environ, "HOME": self.home})
        self.assertEqual(result.stderr, "")
        return result.stdout.splitlines()

    def test_tab_03_rigs_offered_after_spaces_and_commas(self):
        with tempfile.TemporaryDirectory() as home:
            self.home = home
            (Path(home) / ".rig").mkdir()
            (Path(home) / ".rig" / "rigs.yml").write_text(textwrap.dedent(BASIC_RIGS) + "  tools:\n    plugins: []\n")
            self.assertEqual(self.complete("use", ""), ["web", "tools", "full", "none", "IPREFIX="])
            self.assertEqual(self.complete("use", "none,"), ["IPREFIX=none,"])
            self.assertEqual(self.complete("use", "web", ""), ["tools", "full", "IPREFIX="])
            self.assertEqual(self.complete("use", "web,"), ["tools", "full", "IPREFIX=web,"])
            self.assertEqual(self.complete("use", "base,web,to"), ["tools", "full", "IPREFIX=base,web,"])
            self.assertEqual(self.complete("use", "web,tools", ""), ["full", "IPREFIX="])
            self.assertEqual(self.complete("use", "web", "tools", "full,"), ["IPREFIX=full,"])
            self.assertEqual(self.complete("use", "nope,"), ["_default", "IPREFIX="])
            self.assertEqual(self.complete("use", "web", "-p", ""), ["_default", "IPREFIX="])

    def test_tab_06_launch_flags(self):
        with tempfile.TemporaryDirectory() as home:
            self.home = home
            self.assertEqual(self.complete("use", "web", "--s"), ["--sandbox", "--select", "IPREFIX="])

    def test_zsh_parses_the_completion(self):
        with tempfile.NamedTemporaryFile("w", suffix=".zsh") as f:
            f.write(self.rig.ZSH_COMPLETION)
            f.flush()
            result = subprocess.run(["zsh", "-n", f.name], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
