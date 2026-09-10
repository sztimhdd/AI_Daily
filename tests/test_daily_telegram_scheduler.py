"""Regression coverage for the workday scheduler and its completion receipt."""

import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ("daily-telegram.sh", "daily-telegram-hermes.sh")
DATE = "2026-09-01"

# Stubs the clock and the CLI so a tick runs offline: every `python3` call is
# captured, and the run-en stub writes the delivery the real stage would write.
BASH_ENV = """\
date() {
  case "$1" in
    +%u) printf '1\\n' ;;
    +%H) printf '10\\n' ;;
    +%Y-%m-%d) printf '__DATE__\\n' ;;
    '+%F %T') printf '__DATE__ 10:00:00\\n' ;;
    *) command date "$@" ;;
  esac
}
python3() {
  printf '%s\\n' "$*" >> "$TEST_CAPTURE"
  for arg in "$@"; do
    if [ "$arg" = "run-en" ]; then
      printf '{\\n  "status": "delivered"\\n}\\n' > ".local/runs/__DATE__/delivery-en.json"
    fi
  done
}
"""

CHOICES = (
    "- run_id: AI-Daily/%(date)s\n"
    "- date: %(date)s\n"
    "- stage: targeted_research\n"
    "- status: in_progress\n"
    "- slug: demo-slug\n"
    '- topic_choice: "1"\n'
    "- topic_title: Demo\n"
    '- narrative_choice: "1"\n'
)


class DailyTelegramSchedulerTests(unittest.TestCase):
    def run_scheduler(self, script_name, *, state=None, delivery=None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = pathlib.Path(tmp.name)
        script = root / "scripts" / script_name
        script.parent.mkdir(parents=True)
        shutil.copy2(ROOT / "scripts" / script_name, script)
        run_dir = root / ".local" / "runs" / DATE
        run_dir.mkdir(parents=True)
        if state is not None:
            (run_dir / "state.md").write_text(state, encoding="utf-8")
        if delivery is not None:
            (run_dir / "delivery-en.json").write_text(
                json.dumps(delivery, indent=2) + "\n", encoding="utf-8"
            )
        capture = root / "python-invocations.txt"
        bash_env = root / "bash-env"
        bash_env.write_text(BASH_ENV.replace("__DATE__", DATE), encoding="utf-8")
        result = subprocess.run(
            ["bash", str(script)],
            capture_output=True,
            text=True,
            env={**os.environ, "BASH_ENV": str(bash_env), "TEST_CAPTURE": str(capture)},
        )
        invocations = capture.read_text(encoding="utf-8") if capture.exists() else ""
        return result, invocations

    @staticmethod
    def stage_index(invocations: str, stage: str) -> int:
        lines = [line for line in invocations.splitlines() if line.strip()]
        for index, line in enumerate(lines):
            if f" {stage} " in f" {line} ":
                return index
        raise AssertionError(f"stage {stage!r} never ran in:\n{invocations}")

    def test_failed_run_sends_blocked_receipt_before_exiting(self):
        """A failed audit must call the Telegram CLI on the next tick."""
        for script in SCRIPTS:
            with self.subTest(script=script):
                result, invocations = self.run_scheduler(
                    script, state="- status: failed\n"
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"telegram --root . --date {DATE}", invocations)
                # Only the decision channel polls; a failed day owes no receipt.
                self.assertNotIn("receipt", invocations)

    def test_delivered_day_retries_the_completion_receipt(self):
        """The delivered early return still announces, so a failed send retries."""
        for script in SCRIPTS:
            with self.subTest(script=script):
                result, invocations = self.run_scheduler(
                    script, delivery={"status": "delivered"}
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"receipt --root . --date {DATE}", invocations)
                # Nothing else re-runs once the article is delivered.
                self.assertNotIn("run-en", invocations)
                self.assertNotIn("collect", invocations)

    def test_completed_run_notifies_after_delivery(self):
        """The normal path ends with a receipt, after the delivery stage."""
        for script in SCRIPTS:
            with self.subTest(script=script):
                result, invocations = self.run_scheduler(
                    script, state=CHOICES % {"date": DATE}
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"receipt --root . --date {DATE}", invocations)
                self.assertLess(
                    self.stage_index(invocations, "run-en"),
                    self.stage_index(invocations, "receipt"),
                )

    def test_partial_resume_notifies_after_run_en(self):
        """Resuming a partial delivery also announces the finished article."""
        for script in SCRIPTS:
            with self.subTest(script=script):
                result, invocations = self.run_scheduler(
                    script, delivery={"status": "partial", "reason": "images degraded"}
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertLess(
                    self.stage_index(invocations, "run-en"),
                    self.stage_index(invocations, "receipt"),
                )
                # A partial resume never repeats the expensive early stages.
                self.assertNotIn("collect", invocations)
                self.assertNotIn("research", invocations)


if __name__ == "__main__":
    unittest.main()
