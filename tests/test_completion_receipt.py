"""Offline tests for the durable completion receipt: idempotency + retry."""

import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import completion_receipt, telegram_adapter
from ai_daily.paths import RunPaths

DATE = "2026-09-10"
SLUG = "cache-lane-is-cheaper"
ARTICLE_REL = f"articles/{DATE}-{SLUG}-en.md"
PACKAGE_REL = f"outputs/2026/09/10/{SLUG}"


class FakeHttp:
    """Injectable Telegram transport: records calls and can fail the first N."""

    def __init__(self, failures: int = 0):
        self.calls = []
        self.failures = failures

    def __call__(self, url, payload):
        self.calls.append((url, json.loads(payload.decode("utf-8"))))
        if self.failures:
            self.failures -= 1
            raise OSError("transport down")
        return json.dumps({"ok": True, "result": {"message_id": 7}}).encode("utf-8")

    def texts(self) -> list:
        return [body["text"] for _, body in self.calls]


class ReceiptBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = pathlib.Path(self._tmp.name)
        self.rp = RunPaths.for_date(self.root, DATE)
        self.rp.ensure_work_dir()

    def write_delivery(self, *, status="delivered", kit=True, metadata=True,
                       article=True, publication_status="remote",
                       publication_article=ARTICLE_REL) -> dict:
        package = self.root / PACKAGE_REL
        package.mkdir(parents=True, exist_ok=True)
        if metadata:
            (package / completion_receipt.METADATA_JSON).write_text(
                json.dumps({"title": "A Cache Lane Is Cheaper"}), encoding="utf-8"
            )
        if kit:
            (package / completion_receipt.LINKEDIN_KIT_MD).write_text(
                "# kit\n", encoding="utf-8"
            )
        if article:
            article_path = self.root / ARTICLE_REL
            article_path.parent.mkdir(parents=True, exist_ok=True)
            article_path.write_text("# A Cache Lane Is Cheaper\n", encoding="utf-8")
        publication = {"status": publication_status}
        if publication_article:
            publication["article"] = publication_article
        summary = {
            "status": status,
            "package_dir": PACKAGE_REL,
            "final_article": ARTICLE_REL,
            "publication": publication,
        }
        self.write_summary(summary)
        return summary

    def write_summary(self, summary: dict) -> None:
        (self.rp.work_dir / "delivery-en.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def marker(self) -> dict:
        path = self.rp.work_dir / completion_receipt.RECEIPT_JSON
        if not path.is_file():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def send(self, http, **kwargs) -> dict:
        return completion_receipt.send_completion_receipt(
            self.rp, token="token", chat_id="chat", http=http, **kwargs
        )


class ReceiptContentTests(ReceiptBase):
    def test_receipt_carries_article_and_linkedin_kit_links(self):
        self.write_delivery()
        http = FakeHttp()
        result = self.send(http)

        self.assertEqual(result["status"], "sent")
        self.assertNotIn("parse_mode", http.calls[0][1])
        text = http.texts()[0]
        self.assertIn(f"{completion_receipt.BLOB_BASE}/{ARTICLE_REL}", text)
        self.assertIn(
            f"{completion_receipt.BLOB_BASE}/{PACKAGE_REL}/linkedin-kit.md", text
        )
        self.assertIn("A Cache Lane Is Cheaper", text)

    def test_missing_kit_is_reported_instead_of_linked(self):
        self.write_delivery(kit=False)
        http = FakeHttp()
        self.send(http)

        text = http.texts()[0]
        self.assertIn("LinkedIn 套件：未生成", text)
        self.assertNotIn("linkedin-kit.md", text)
        self.assertIn(f"{completion_receipt.BLOB_BASE}/{ARTICLE_REL}", text)

    def test_nonremote_publication_is_not_advertised_as_a_public_url(self):
        for mode in ("local-only", "failed"):
            with self.subTest(mode=mode):
                self.write_delivery(
                    publication_status=mode,
                    publication_article=ARTICLE_REL if mode == "failed" else None,
                )
                http = FakeHttp()
                self.send(http)

                text = http.texts()[0]
                self.assertNotIn(completion_receipt.BLOB_BASE, text)
                self.assertIn(f"（远端未发布：{mode}）", text)
                self.assertIn(f"文章（本地）：{ARTICLE_REL}", text)
                self.assertIn(f"LinkedIn 套件（本地）：{PACKAGE_REL}/linkedin-kit.md", text)


class ReceiptIdempotencyTests(ReceiptBase):
    def test_recorded_send_is_not_repeated(self):
        self.write_delivery()
        first = FakeHttp()
        self.assertEqual(self.send(first)["status"], "sent")
        self.assertEqual(self.marker()["status"], "sent")
        self.assertEqual(self.marker()["article"], ARTICLE_REL)

        second = FakeHttp()
        self.assertEqual(self.send(second)["status"], "already-sent")
        self.assertEqual(second.calls, [])

    def test_lost_marker_reannounces_rather_than_dropping_the_receipt(self):
        """At-least-once: the crash window between send and marker write re-sends."""
        self.write_delivery()
        self.send(FakeHttp())
        (self.rp.work_dir / completion_receipt.RECEIPT_JSON).unlink()

        again = FakeHttp()
        self.assertEqual(self.send(again)["status"], "sent")
        self.assertEqual(len(again.calls), 1)

    def test_already_sent_receipt_needs_no_credentials_or_network(self):
        self.write_delivery()
        self.send(FakeHttp())

        with mock.patch.object(
            telegram_adapter, "load_config",
            side_effect=AssertionError("credentials must not be read"),
        ):
            result = completion_receipt.send_completion_receipt(
                self.rp, token=None, chat_id=None, http=FakeHttp()
            )
        self.assertEqual(result["status"], "already-sent")

    def test_failed_send_leaves_no_marker_and_is_retried(self):
        self.write_delivery()
        flaky = FakeHttp(failures=2)

        for _ in range(2):
            with self.assertRaises(telegram_adapter.TelegramError):
                self.send(flaky)
            self.assertEqual(self.marker(), {})

        self.assertEqual(self.send(flaky)["status"], "sent")
        self.assertEqual(len(flaky.calls), 3)
        self.assertEqual(self.marker()["status"], "sent")

    def test_changed_delivery_earns_a_fresh_receipt(self):
        summary = self.write_delivery(status="partial", kit=False)
        self.assertEqual(self.send(FakeHttp())["status"], "sent")

        # The resumed run produced the kit and completed: the message changed.
        (self.root / PACKAGE_REL / completion_receipt.LINKEDIN_KIT_MD).write_text(
            "# kit\n", encoding="utf-8"
        )
        summary["status"] = "delivered"
        self.write_summary(summary)

        second = FakeHttp()
        self.assertEqual(self.send(second)["status"], "sent")
        self.assertEqual(len(second.calls), 1)
        self.assertIn("linkedin-kit.md", second.texts()[0])


class ReceiptGatingTests(ReceiptBase):
    def test_no_delivery_summary_is_a_noop(self):
        http = FakeHttp()
        result = self.send(http)
        self.assertEqual(result["status"], "noop")
        self.assertEqual(http.calls, [])
        self.assertEqual(self.marker(), {})

    def test_failed_delivery_is_not_announced(self):
        self.write_delivery(status="failed")
        http = FakeHttp()
        self.assertEqual(self.send(http)["status"], "noop")
        self.assertEqual(http.calls, [])
        self.assertEqual(self.marker(), {})


if __name__ == "__main__":
    unittest.main()
