"""Regression coverage for the launchd Telegram recovery path."""

import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "daily-telegram.sh"


class DailyTelegramSchedulerTests(unittest.TestCase):
    def test_failed_run_sends_blocked_receipt_before_exiting(self):
        """A failed audit must call the Telegram CLI on the next scheduler tick."""
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            script = root / "scripts" / "daily-telegram.sh"
            script.parent.mkdir()
            shutil.copy2(SCRIPT, script)
            state = root / ".local" / "runs" / "2026-09-01" / "state.md"
            state.parent.mkdir(parents=True)
            state.write_text("- status: failed\n", encoding="utf-8")
            capture = root / "python-invocations.txt"
            bash_env = root / "bash-env"
            bash_env.write_text(
                """date() {
  case \"$1\" in
    +%u) printf '1\\n' ;;
    +%H) printf '10\\n' ;;
    +%Y-%m-%d) printf '2026-09-01\\n' ;;
    '+%F %T') printf '2026-09-01 10:00:00\\n' ;;
    *) command date \"$@\" ;;
  esac
}
python3() { printf '%s\\n' \"$*\" >> \"$TEST_CAPTURE\"; }
""",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["bash", str(script)],
                capture_output=True,
                text=True,
                env={**os.environ, "BASH_ENV": str(bash_env), "TEST_CAPTURE": str(capture)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(capture.exists(), result.stderr)
            self.assertIn("telegram --root . --date 2026-09-01", capture.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
