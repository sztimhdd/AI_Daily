"""Tests for scripts/open_ai_daily_terminal.sh.

Only the --dry-run path is exercised: the script prints the generated
shell command and never calls osascript, so no real Terminal window is
ever launched from the test suite.
"""

import pathlib
import subprocess
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "open_ai_daily_terminal.sh"


def make_root(tmp: str) -> pathlib.Path:
    """Create a minimal repo root with src/ai_daily/cli.py present."""
    root = pathlib.Path(tmp)
    (root / "src" / "ai_daily").mkdir(parents=True, exist_ok=True)
    (root / "src" / "ai_daily" / "cli.py").write_text("", encoding="utf-8")
    return root


def run_script(root, date, command=None):
    argv = [str(SCRIPT), "--root", str(root), "--date", date]
    if command is not None:
        argv += ["--command", command]
    argv += ["--dry-run"]
    return subprocess.run(argv, capture_output=True, text=True)


class TerminalLauncherDryRunTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def test_success_command_has_expected_parts(self):
        root = make_root(self._tmp.name)
        res = run_script(root, "2026-08-17")
        self.assertEqual(res.returncode, 0, res.stderr)
        out = res.stdout.strip()
        self.assertIn("cd ", out)
        self.assertIn(str(root), out)
        self.assertIn("PYTHONPATH=src", out)
        self.assertIn("python3 -m ai_daily.cli", out)
        self.assertIn(" session ", out)
        self.assertIn("--date '2026-08-17'", out)
        self.assertNotIn("osascript", res.stderr)

    def test_status_command_allowed(self):
        root = make_root(self._tmp.name)
        res = run_script(root, "2026-08-17", command="status")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn(" status ", res.stdout)

    def test_session_command_allowed(self):
        root = make_root(self._tmp.name)
        res = run_script(root, "2026-08-17", command="session")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn(" session ", res.stdout)

    def test_spaces_in_root_are_single_quote_escaped(self):
        spaced = pathlib.Path(self._tmp.name) / "My Root dir"
        spaced.mkdir()
        root = make_root(str(spaced))
        res = run_script(root, "2026-08-17")
        self.assertEqual(res.returncode, 0, res.stderr)
        out = res.stdout.strip()
        self.assertIn(f"cd '{spaced}'", out)
        self.assertIn(f"--root '{spaced}'", out)

    def test_single_quote_in_root_is_escaped(self):
        quoted = pathlib.Path(self._tmp.name) / "O'Brien's root"
        quoted.mkdir()
        root = make_root(str(quoted))
        res = run_script(root, "2026-08-17")
        self.assertEqual(res.returncode, 0, res.stderr)
        escaped = str(quoted).replace("'", "'\\''")
        self.assertIn(f"cd '{escaped}'", res.stdout)
        self.assertIn(f"--root '{escaped}'", res.stdout)

    def test_dollar_sign_in_root_stays_literal(self):
        dollar = pathlib.Path(self._tmp.name) / "a b$c"
        dollar.mkdir()
        root = make_root(str(dollar))
        res = run_script(root, "2026-08-17")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn(f"'{dollar}'", res.stdout)

    def test_invalid_date_rejected(self):
        root = make_root(self._tmp.name)
        for bad in ("2026-8-1", "2026-08", "not-a-date", ""):
            res = run_script(root, bad)
            self.assertNotEqual(res.returncode, 0, bad)
            self.assertIn("date", res.stderr.lower())

    def test_invalid_command_rejected(self):
        root = make_root(self._tmp.name)
        for bad in ("collect", "status2", "choose-topic --force", "rm -rf /"):
            res = run_script(root, "2026-08-17", command=bad)
            self.assertNotEqual(res.returncode, 0, bad)
            self.assertIn("command", res.stderr.lower())

    def test_missing_root_rejected(self):
        missing = pathlib.Path(self._tmp.name) / "does-not-exist"
        res = run_script(missing, "2026-08-17")
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("root", res.stderr.lower())

    def test_root_without_cli_py_rejected(self):
        root = pathlib.Path(self._tmp.name)
        (root / "src" / "ai_daily").mkdir(parents=True)
        res = run_script(root, "2026-08-17")
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("cli.py", res.stderr)

    def test_missing_date_arg_rejected(self):
        root = make_root(self._tmp.name)
        res = subprocess.run(
            [str(SCRIPT), "--root", str(root), "--dry-run"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("date", res.stderr.lower())


if __name__ == "__main__":
    unittest.main()
