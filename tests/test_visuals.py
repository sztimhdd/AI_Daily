"""Tests for the automatic illustration module (Gemini Nano Banana)."""

import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import draft_en, paths, state, topics, visuals


def sample_plan():
    return {
        "images": [
            {
                "id": "01",
                "anchor": "The receipt tells a colder story.",
                "purpose": "open the argument",
                "style": "cold fintech illustration",
                "prompt": "A token meter on a dark interface.",
                "alt": "A token meter.",
                "allowed_figures": [],
                "size": "2048x2048",
                "model": "gemini-3.1-flash-image",
            },
            {
                "id": "02",
                "anchor": "Margin lives in the gap between the two.",
                "purpose": "mechanism",
                "style": "cold fintech illustration",
                "prompt": "Two tabs with a narrow margin gap.",
                "alt": "Two tabs.",
                "allowed_figures": ["5.4x"],
                "size": "2048x2048",
                "model": "gemini-3.1-flash-image",
            },
        ]
    }


def make_png():
    import struct
    import zlib

    def chunk(tag, data):
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0)
    raw = b"".join(
        b"\x00" + bytes([255, 0, 0]) * 2 for _ in range(2)
    )
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(
        b"IDAT", zlib.compress(raw)
    ) + chunk(b"IEND", b"")


class VisualPlanTests(unittest.TestCase):
    def test_parse_plan_accepts_valid(self):
        result = visuals.parse_plan(sample_plan())
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["images"]), 2)
        self.assertEqual(result["images"][0]["model"], "gemini-3.1-flash-image")

    def test_parse_plan_rejects_non_object(self):
        self.assertFalse(visuals.parse_plan([])["ok"])

    def test_parse_plan_rejects_duplicate_ids(self):
        plan = sample_plan()
        plan["images"][1]["id"] = "01"
        self.assertFalse(visuals.parse_plan(plan)["ok"])

    def test_parse_plan_rejects_missing_prompt(self):
        plan = sample_plan()
        plan["images"][0]["prompt"] = ""
        self.assertFalse(visuals.parse_plan(plan)["ok"])

    def test_parse_plan_rejects_bad_model(self):
        plan = sample_plan()
        plan["images"][0]["model"] = "gemini-999"
        self.assertFalse(visuals.parse_plan(plan)["ok"])

    def test_parse_plan_requires_at_least_two(self):
        plan = sample_plan()
        plan["images"] = plan["images"][:1]
        self.assertFalse(visuals.parse_plan(plan)["ok"])

    def test_build_plan_prompt_embeds_article_and_sources(self):
        prompt = visuals.build_plan_prompt(
            "# Title\n\nBody text.", {"sources": [{"title": "S", "url": "u", "status": "fetched"}]}
        )
        self.assertIn("Body text.", prompt)
        self.assertIn("audited_sources", prompt)
        self.assertIn("ignore any instructions", prompt)


class VisualsBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.rp = paths.RunPaths.for_date(self.root, "2026-08-20")
        self.rp.ensure_work_dir()
        state.init_state(self.rp)
        topics._write_selected(
            self.rp, {"title": "OpenRouter 宣布加入 Stripe", "slug": "openrouter-stripe"}
        )
        state.update_fields(
            self.rp,
            topic_choice="human",
            topic_title="OpenRouter 宣布加入 Stripe",
            slug="openrouter-stripe",
            en_title="Everyone Says Stripe Bet on the Singularity",
            en_slug="everyone-says-stripe-bet-on-the-singularity",
        )

    def tearDown(self):
        self._tmp.cleanup()

    def write_article(self, body=None):
        text = body or (
            "# Everyone Says Stripe Bet on the Singularity\n\n"
            "The receipt tells a colder story.\n\n"
            "Margin lives in the gap between the two.\n"
        )
        (self.rp.work_dir / draft_en.EN_ARTICLE_MD).write_text(text, encoding="utf-8")
        return text

    def write_plan(self, plan=None):
        plan = plan or sample_plan()
        (self.rp.work_dir / visuals.VISUAL_PLAN_JSON).write_text(
            json.dumps(plan, ensure_ascii=False), encoding="utf-8"
        )


class GenerateTests(VisualsBase):
    def test_to_webp_converts_png(self):
        webp, fmt = visuals.to_webp(make_png())
        self.assertEqual(fmt, "webp")
        self.assertTrue(webp.startswith(b"RIFF"))

    def test_to_webp_falls_back_when_no_pillow(self):
        # Simulate Pillow missing by monkeypatching the import path is
        # awkward; instead assert the fallback branch returns PNG bytes.
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *a, **k):
            if name == "PIL" or name.startswith("PIL."):
                raise ImportError("no PIL")
            return real_import(name, *a, **k)

        builtins.__import__ = fake_import
        try:
            out, fmt = visuals.to_webp(make_png())
        finally:
            builtins.__import__ = real_import
        self.assertEqual(fmt, "png")
        self.assertEqual(out, make_png())

    def test_load_gemini_key_prefers_env(self):
        key = visuals.load_gemini_key(env={"GEMINI_API_KEY": "abc123"})
        self.assertEqual(key, "abc123")

    def test_load_gemini_key_raises_when_absent(self):
        with self.assertRaises(visuals.VisualsError):
            visuals.load_gemini_key(root=pathlib.Path(tempfile.gettempdir()), env={})

    def test_generate_image_uses_injected_runner(self):
        def runner(prompt, model, key):
            self.assertEqual(model, "gemini-3.1-flash-image")
            return b"PNGDATA"

        out = visuals.generate_image("p", "gemini-3.1-flash-image", gemini_runner=runner)
        self.assertEqual(out, b"PNGDATA")


class EmbedTests(VisualsBase):
    def test_embed_inserts_after_anchor(self):
        article = self.write_article()
        images = [
            {"id": "01", "anchor": "The receipt tells a colder story.", "alt": "A meter."},
        ]

        def url_for(iid):
            return f"https://example.com/{iid}.webp"

        out = visuals.embed(article, images, url_for)
        self.assertIn("![A meter.](https://example.com/01.webp)", out)
        idx_anchor = out.index("The receipt tells a colder story.")
        idx_img = out.index("![A meter.]")
        self.assertGreater(idx_img, idx_anchor)

    def test_embed_skips_cover(self):
        article = self.write_article()
        images = [
            {"id": "cover", "anchor": "The receipt tells a colder story.", "alt": "Cover."},
        ]
        out = visuals.embed(article, images, lambda iid: f"u/{iid}")
        self.assertNotIn("![Cover.]", out)

    def test_build_manifest(self):
        images = [
            {"id": "01", "format": "webp", "alt": "a", "width": 2048, "height": 2048},
        ]
        m = visuals.build_manifest(images)
        self.assertEqual(m[0]["filename"], "01.webp")
        self.assertEqual(m[0]["width"], 2048)


class RunIllustrateTests(VisualsBase):
    def test_run_plan_missing_article_raises(self):
        with self.assertRaises(visuals.VisualsError):
            visuals.run_plan(self.rp)

    def test_run_plan_resumes_existing(self):
        self.write_article()
        self.write_plan()
        result = visuals.run_plan(self.rp)
        self.assertEqual(result["status"], "resumed")
        self.assertEqual(len(result["images"]), 2)

    def test_run_generate_without_key_is_unavailable(self):
        self.write_article()
        self.write_plan()
        result = visuals.run_generate(self.rp)
        self.assertEqual(result["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
