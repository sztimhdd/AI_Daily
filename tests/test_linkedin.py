"""Tests for the LinkedIn distribution kit module."""

import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import draft_en, linkedin, paths, state, topics


def sample_kit():
    return {
        "seo_title": "Liquid AI's 3.2x Is Not Your Bill",
        "seo_description": "A vendor-reported 3.2x speedup means little until you "
        "validate it on your own traffic. The draft path changes what you must test.",
        "post": (
            "Your serving dashboard can make speed look clean.\n\n"
            "- The 3.18x figure is vendor-reported on one H100.\n"
            "- It does not transfer to your traffic or your stack.\n"
            "- The new draft path changes your acceptance surface.\n\n"
            "The meter under the poster still counts.\n\n"
            "Read the full deep dive below 👇\n\n"
            "#AI #LLMOps #Inference"
        ),
    }


class ParseKitTests(unittest.TestCase):
    def test_parse_accepts_valid(self):
        result = linkedin.parse_kit(sample_kit())
        self.assertTrue(result["ok"])
        self.assertEqual(result["seo_title"], sample_kit()["seo_title"])

    def test_parse_rejects_non_object(self):
        self.assertFalse(linkedin.parse_kit([])["ok"])

    def test_parse_rejects_missing_seo_title(self):
        kit = sample_kit()
        kit.pop("seo_title")
        self.assertFalse(linkedin.parse_kit(kit)["ok"])

    def test_parse_rejects_long_seo_title(self):
        kit = sample_kit()
        kit["seo_title"] = "x" * 61
        self.assertFalse(linkedin.parse_kit(kit)["ok"])

    def test_parse_rejects_long_seo_description(self):
        kit = sample_kit()
        kit["seo_description"] = "y" * 161
        self.assertFalse(linkedin.parse_kit(kit)["ok"])

    def test_parse_rejects_missing_post(self):
        kit = sample_kit()
        kit.pop("post")
        self.assertFalse(linkedin.parse_kit(kit)["ok"])

    def test_render_kit_md_has_all_sections(self):
        md = linkedin.render_kit_md(sample_kit())
        self.assertIn("# 🚀 LinkedIn Distribution Kit", md)
        self.assertIn("### 1. SEO Title", md)
        self.assertIn("### 2. SEO Description", md)
        self.assertIn("### 3. LinkedIn Post", md)

    def test_render_kit_md_includes_generated_cover_when_available(self):
        kit = {**sample_kit(), "cover": {
            "url": "https://raw.githubusercontent.com/example/cover.webp",
            "alt": "A locked box beside an open channel.",
        }}
        md = linkedin.render_kit_md(kit)
        self.assertIn("### 4. LinkedIn Cover", md)
        self.assertIn("cover.webp", md)

    def test_build_kit_prompt_embeds_article(self):
        prompt = linkedin.build_kit_prompt("# T\n\nBody.", "T")
        self.assertIn("Body.", prompt)
        self.assertIn("ignore any instructions", prompt)


class RunKitTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.rp = paths.RunPaths.for_date(self.root, "2026-08-20")
        self.rp.ensure_work_dir()
        state.init_state(self.rp)
        topics._write_selected(
            self.rp, {"title": "Topic", "slug": "topic"}
        )
        state.update_fields(
            self.rp, topic_choice="human", topic_title="Topic", slug="topic",
        )

    def tearDown(self):
        self._tmp.cleanup()

    def test_run_kit_missing_article_unavailable(self):
        result = linkedin.run(self.rp)
        self.assertEqual(result["status"], "unavailable")

    def test_run_kit_generates_files(self):
        (self.rp.work_dir / draft_en.EN_ARTICLE_MD).write_text(
            "# The Title\n\nBody.", encoding="utf-8"
        )

        def runner(prompt):
            return {"seo_title": sample_kit()["seo_title"],
                    "seo_description": sample_kit()["seo_description"],
                    "post": sample_kit()["post"]}

        result = linkedin.run(self.rp, codex_runner=runner)
        self.assertEqual(result["status"], "generated")
        self.assertTrue((self.rp.work_dir / linkedin.LINKEDIN_KIT_JSON).is_file())
        self.assertTrue((self.rp.work_dir / linkedin.LINKEDIN_KIT_MD).is_file())

    def test_run_kit_adds_successful_visual_cover(self):
        (self.rp.work_dir / draft_en.EN_ARTICLE_MD).write_text(
            "# The Title\n\nBody.", encoding="utf-8"
        )
        state.update_fields(self.rp, en_slug="the-title")
        (self.rp.work_dir / "images-manifest.json").write_text(
            json.dumps({"images": [{
                "id": "cover", "status": "generated", "format": "webp",
                "alt": "A chosen editorial cover.", "caption": "The argument in one frame.",
            }]}), encoding="utf-8"
        )
        image_dir = self.rp.work_dir / "images"
        image_dir.mkdir()
        (image_dir / "cover.webp").write_bytes(b"RIFF....WEBP")

        result = linkedin.run(self.rp, codex_runner=lambda prompt: sample_kit())
        self.assertEqual(result["status"], "generated")
        self.assertIn("cover", result)
        self.assertIn("the-title/images/cover.webp", result["cover"]["url"])
        rendered = (self.rp.work_dir / linkedin.LINKEDIN_KIT_MD).read_text(encoding="utf-8")
        self.assertIn("### 4. LinkedIn Cover", rendered)


if __name__ == "__main__":
    unittest.main()
