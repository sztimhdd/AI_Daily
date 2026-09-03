"""Tests for the automatic illustration module (Gemini Nano Banana)."""

import base64
import json
import pathlib
import re
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

    def test_parse_plan_defaults_to_gemini_31_flash_image(self):
        plan = sample_plan()
        del plan["images"][0]["model"]
        result = visuals.parse_plan(plan)
        self.assertTrue(result["ok"])
        self.assertEqual(result["images"][0]["model"], "gemini-3.1-flash-image")

    def test_parse_plan_rejects_square_linkedin_cover(self):
        plan = sample_plan()
        plan["images"].insert(0, {
            "id": "cover", "kind": "image", "anchor": "",
            "prompt": "A clear editorial cover.", "alt": "Cover.",
            "size": "1024x1024", "model": "gemini-2.5-flash-image",
        })
        result = visuals.parse_plan(plan)
        self.assertFalse(result["ok"])
        self.assertIn("1920x1080", result["error"])

    def test_parse_plan_normalizes_raster_kind(self):
        plan = sample_plan()
        plan["images"][0]["kind"] = "raster"
        result = visuals.parse_plan(plan)
        self.assertTrue(result["ok"])
        self.assertEqual(result["images"][0]["kind"], "image")

    def test_parse_plan_carries_caption_and_defaults_to_alt(self):
        plan = sample_plan()
        plan["images"][0]["caption"] = "一个观点：城市停摆不是灯坏了，是没人看得见总闸。"
        result = visuals.parse_plan(plan)
        self.assertEqual(result["images"][0]["caption"], plan["images"][0]["caption"])
        # diagram entries and missing captions fall back to alt
        plan2 = sample_plan()
        plan2["images"].append({
            "id": "03", "kind": "diagram", "anchor": "c.",
            "alt": "arch diagram", "diagram": {"mode": "architecture", "nodes": []},
        })
        parsed = visuals.parse_plan(plan2)
        self.assertEqual(parsed["images"][2]["caption"], "arch diagram")
        self.assertEqual(parsed["images"][1]["caption"], parsed["images"][1]["alt"])

    def test_fit_svg_canvas_grows_canvas_to_content(self):
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="700" '
            'viewBox="0 0 960 700">'
            '<style>.title { font-size: 30px; }</style>'
            '<rect data-graph-role="background" width="960" height="700" '
            'fill="#ffffff"/>'
            '<text x="480" y="56" text-anchor="middle" class="title">'
            "Require logs that connect each scan to an identity, asset, "
            "policy, and outcome.</text>"
            '<rect x="744" y="622" width="184" height="104"/>'
            "</svg>"
        )
        fitted = visuals._fit_svg_canvas(svg.encode("utf-8")).decode("utf-8")
        m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', fitted)
        self.assertIsNotNone(m)
        fit_w, fit_h = float(m.group(1)), float(m.group(2))
        self.assertGreater(fit_w, 960)
        self.assertGreater(fit_h, 700)
        bg = re.search(
            r'<rect([^>]*data-graph-role="background"[^>]*)width="([\d.]+)"'
            r'([^>]*)height="([\d.]+)"',
            fitted,
        )
        self.assertIsNotNone(bg)
        self.assertEqual(float(bg.group(2)), fit_w)
        self.assertEqual(float(bg.group(4)), fit_h)

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

    def test_build_plan_prompt_states_exact_kind_values(self):
        prompt = visuals.build_plan_prompt("# Title\n\nBody text.", {"sources": []})
        self.assertIn('is exactly "image" or "diagram"', prompt)
        self.assertIn("ignore any instructions", prompt)

    def test_build_plan_prompt_prefers_gemini_images(self):
        prompt = visuals.build_plan_prompt("# Title\n\nBody text.", {"sources": []})
        self.assertIn("PRIMARY visual language", prompt)
        self.assertIn("At most ONE diagram per plan", prompt)
        self.assertIn("cover, is a Gemini image", prompt)

    def test_parse_plan_rejects_three_homogeneous_body_visuals(self):
        plan = sample_plan()
        plan["images"].append(
            {
                "id": "03", "anchor": "A third point.",
                "purpose": "another argument", "style": "cold fintech illustration",
                "prompt": "A third cold fintech scene.", "alt": "A third scene.",
            }
        )
        result = visuals.parse_plan(plan)
        self.assertFalse(result["ok"])
        self.assertIn("visual diversity", result["error"])

    def test_build_plan_prompt_requires_a_distinct_linkedin_cover(self):
        prompt = visuals.build_plan_prompt("# Title\n\nBody text.", {"sources": []})
        self.assertIn("LinkedIn cover", prompt)
        self.assertIn("different visual modes", prompt)

    def test_build_plan_prompt_selects_cover_style_from_article(self):
        prompt = visuals.build_plan_prompt("# Title\n\nBody text.", {"sources": []})
        self.assertIn("select the most suitable visual language", prompt)
        self.assertIn("visual style library", prompt)
        self.assertIn("article-driven", prompt)
        self.assertIn("Do not default to cyberpunk", prompt)

    def test_build_plan_prompt_keeps_linkedin_cover_hard_constraints(self):
        prompt = visuals.build_plan_prompt("# Title\n\nBody text.", {"sources": []})
        self.assertIn("1920x1080", prompt)
        self.assertIn("16:9", prompt)
        self.assertIn("central safe area", prompt)
        self.assertIn("render no words", prompt)


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

    def test_generate_image_uses_injected_runner(self):
        def runner(prompt, model, token, project):
            self.assertEqual(model, "gemini-3.1-flash-image")
            return b"PNGDATA"

        out = visuals.generate_image(
            "p", "gemini-3.1-flash-image", gemini_runner=runner,
            token="t", project="p",
        )
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

    def test_embed_matches_anchor_inside_a_longer_paragraph(self):
        article = (
            "# T\n\n"
            "One model proposes next tokens while another decides. "
            "That coordination is speculative decoding.\n"
        )
        images = [
            {"id": "01", "anchor": "That coordination is speculative decoding.",
             "alt": "Handoff."},
        ]
        out = visuals.embed(article, images, lambda iid: f"u/{iid}.webp")
        self.assertIn("![Handoff.](u/01.webp)", out)

    def test_embed_emits_caption_line_after_image(self):
        article = "# T\n\nThe receipt tells a colder story.\n"
        images = [
            {"id": "01", "anchor": "The receipt tells a colder story.",
             "alt": "A meter."},
        ]
        out = visuals.embed(article, images, lambda iid: f"u/{iid}.webp")
        self.assertIn("![A meter.](u/01.webp)", out)
        self.assertIn("*A meter.*", out)
        self.assertGreater(out.index("*A meter.*"), out.index("![A meter.]"))

    def test_embed_uses_caption_not_alt_for_the_visible_line(self):
        article = "# T\n\nThe receipt tells a colder story.\n"
        images = [
            {"id": "01", "anchor": "The receipt tells a colder story.",
             "alt": "A dark city block at night.",
             "caption": "停摆不是灯坏了，是没人看得见总闸。"},
        ]
        out = visuals.embed(article, images, lambda iid: f"u/{iid}.webp")
        self.assertIn("![A dark city block at night.](u/01.webp)", out)
        self.assertIn("*停摆不是灯坏了，是没人看得见总闸。*", out)
        self.assertNotIn("*A dark city block at night.*", out)

    def test_embed_is_idempotent_on_repeat(self):
        article = "# T\n\nThe receipt tells a colder story.\n"
        images = [
            {"id": "01", "anchor": "The receipt tells a colder story.",
             "alt": "A meter.", "caption": "观点行。"},
        ]
        first = visuals.embed(article, images, lambda iid: f"u/{iid}.webp")
        second = visuals.embed(first, images, lambda iid: f"u/{iid}.webp")
        self.assertEqual(first, second)
        self.assertEqual(second.count("![A meter.](u/01.webp)"), 1)

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


class DiagramLaneTests(VisualsBase):
    TINY_PNG = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )

    def test_generate_diagram_runs_generator_then_converter_to_webp(self):
        spec = {"mode": "architecture", "nodes": [], "arrows": []}
        calls = []

        def gen(s):
            calls.append(("gen", s))
            return b"<svg xmlns='http://www.w3.org/2000/svg'/>"

        def conv(svg):
            calls.append(("conv", svg))
            return self.TINY_PNG

        webp, fmt = visuals.generate_diagram(spec, generator=gen, converter=conv)
        self.assertEqual(fmt, "webp")
        self.assertTrue(webp.startswith(b"RIFF"))
        self.assertEqual(calls, [("gen", spec), ("conv", b"<svg xmlns='http://www.w3.org/2000/svg'/>")])

    def test_generate_diagram_generator_failure_is_explicit(self):
        def gen(s):
            raise RuntimeError("generator down")

        with self.assertRaises(visuals.VisualsError):
            visuals.generate_diagram(
                {"mode": "x"}, generator=gen, converter=lambda svg: b""
            )

    def test_generate_diagram_rejects_unknown_mode_in_default_generator(self):
        with self.assertRaises(visuals.VisualsError):
            visuals._default_diagram_generator({"mode": "not-a-mode"})

    def test_parse_plan_accepts_diagram_entry(self):
        plan = {
            "images": [
                {"id": "01", "anchor": "a.", "prompt": "p", "alt": "a."},
                {
                    "id": "02", "kind": "diagram", "anchor": "b.",
                    "alt": "arch",
                    "diagram": {
                        "mode": "architecture", "title": "Stack",
                        "nodes": [], "arrows": [],
                    },
                },
            ]
        }
        parsed = visuals.parse_plan(plan)
        self.assertTrue(parsed["ok"])
        dia = parsed["images"][1]
        self.assertEqual(dia["kind"], "diagram")
        self.assertEqual(dia["diagram"]["mode"], "architecture")

    def test_parse_plan_rejects_diagram_with_unknown_mode(self):
        plan = {
            "images": [
                {"id": "01", "anchor": "a.", "prompt": "p"},
                {"id": "02", "kind": "diagram", "diagram": {"mode": "nope"}},
            ]
        }
        self.assertFalse(visuals.parse_plan(plan)["ok"])

    def test_parse_plan_rejects_more_than_one_diagram(self):
        plan = {
            "images": [
                {"id": "01", "anchor": "a.", "prompt": "p"},
                {
                    "id": "02", "kind": "diagram",
                    "diagram": {"mode": "architecture", "nodes": []},
                },
                {
                    "id": "03", "kind": "diagram",
                    "diagram": {"mode": "data-flow", "nodes": []},
                },
            ]
        }
        result = visuals.parse_plan(plan)
        self.assertFalse(result["ok"])
        self.assertIn("at most 1", result["error"])

    def test_run_generate_routes_diagram_entries_through_diagram_lane(self):
        self.write_article()
        plan = {
            "images": [
                {"id": "01", "anchor": "a.", "prompt": "p", "alt": "a."},
                {
                    "id": "02", "kind": "diagram", "anchor": "b.",
                    "alt": "arch",
                    "diagram": {
                        "mode": "architecture", "title": "Stack",
                        "nodes": [], "arrows": [],
                    },
                },
            ]
        }
        (self.rp.work_dir / visuals.VISUAL_PLAN_JSON).write_text(
            json.dumps(plan), encoding="utf-8"
        )
        from unittest import mock

        def fake_runner(prompt, model, token, project):
            return make_png()

        def fake_gen(spec):
            return b"<svg xmlns='http://www.w3.org/2000/svg'/>"

        def fake_conv(svg):
            return make_png()

        with mock.patch.object(visuals, "load_vertex_token", return_value="tok"), \
             mock.patch.object(visuals, "load_vertex_project", return_value="proj"):
            result = visuals.run_generate(
                self.rp, gemini_runner=fake_runner,
                diagram_generator=fake_gen, diagram_converter=fake_conv,
            )
        self.assertEqual(result["status"], "generated")
        self.assertEqual(result["generated"], 2)
        manifest = json.loads(
            (self.rp.work_dir / visuals.IMAGES_MANIFEST_JSON).read_text(
                encoding="utf-8"
            )
        )
        kinds = {e["id"]: e.get("kind", "image") for e in manifest["images"]}
        self.assertEqual(kinds["02"], "diagram")

    def test_run_generate_falls_back_to_gemini_when_diagram_lane_fails(self):
        self.write_article()
        plan = {
            "images": [
                {"id": "01", "anchor": "a.", "prompt": "p", "alt": "a."},
                {
                    "id": "02", "kind": "diagram", "anchor": "b.", "alt": "arch",
                    "fallback_image_prompt": "A factual editorial architecture scene.",
                    "diagram": {"mode": "architecture", "title": "Stack", "nodes": []},
                },
            ]
        }
        (self.rp.work_dir / visuals.VISUAL_PLAN_JSON).write_text(
            json.dumps(plan), encoding="utf-8"
        )

        def fake_runner(prompt, model, token, project):
            return make_png()

        def failing_diagram(spec):
            raise RuntimeError("generator down")

        from unittest import mock

        with mock.patch.object(visuals, "load_vertex_token", return_value="tok"), \
             mock.patch.object(visuals, "load_vertex_project", return_value="proj"):
            result = visuals.run_generate(
                self.rp, gemini_runner=fake_runner, diagram_generator=failing_diagram,
            )
        self.assertEqual(result["generated"], 2)
        fallback = result["manifest"]["images"][1]
        self.assertEqual(fallback["kind"], "image")
        self.assertEqual(fallback["fallback_from"], "diagram")


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

    def test_run_generate_with_injected_runner_and_token(self):
        self.write_article()
        self.write_plan()
        from unittest import mock

        def fake_runner(prompt, model, token, project):
            return make_png()

        with mock.patch.object(visuals, "load_vertex_token", return_value="tok"), \
             mock.patch.object(visuals, "load_vertex_project", return_value="proj"):
            result = visuals.run_generate(self.rp, gemini_runner=fake_runner)
        self.assertEqual(result["status"], "generated")
        self.assertEqual(result["generated"], 2)

    def test_run_generate_normalizes_cover_to_linkedin_article_size(self):
        self.write_article()
        plan = {
            "images": [
                {"id": "cover", "kind": "image", "anchor": "",
                 "prompt": "A clear editorial cover.", "alt": "Cover.",
                 "size": "1920x1080", "model": "gemini-2.5-flash-image"},
                {"id": "01", "kind": "image", "anchor": "a.",
                 "prompt": "A body image.", "alt": "Body.",
                 "size": "1024x1024", "model": "gemini-2.5-flash-image"},
            ]
        }
        (self.rp.work_dir / visuals.VISUAL_PLAN_JSON).write_text(
            json.dumps(plan), encoding="utf-8"
        )
        from unittest import mock

        with mock.patch.object(visuals, "load_vertex_token", return_value="tok"), \
             mock.patch.object(visuals, "load_vertex_project", return_value="proj"):
            result = visuals.run_generate(
                self.rp,
                gemini_runner=lambda *_args: make_png(),
            )
        cover = next(item for item in result["manifest"]["images"] if item["id"] == "cover")
        self.assertEqual((cover["width"], cover["height"]), (1920, 1080))

    def test_illustrate_embeds_only_generated_images(self):
        self.write_article()
        from unittest import mock

        plan = {"status": "ok", "images": [
            {"id": "01", "anchor": "The receipt tells a colder story.",
             "alt": "a1", "caption": "c1"},
            {"id": "03", "anchor": "The receipt tells a colder story.",
             "alt": "a3", "caption": "c3"},
        ]}
        manifest = {"images": [
            {"id": "01", "status": "generated", "format": "webp"},
            {"id": "03", "status": "failed", "format": "webp", "reason": "down"},
        ]}
        with mock.patch.object(visuals, "run_plan", return_value=plan), \
             mock.patch.object(
                 visuals, "run_generate",
                 return_value={"status": "generated", "manifest": manifest},
             ):
            result = visuals.run_illustrate(self.rp)
        article = (self.rp.work_dir / draft_en.EN_ARTICLE_MD).read_text(
            encoding="utf-8"
        )
        self.assertIn("images/01.webp", article)
        self.assertNotIn("images/03.webp", article)
        self.assertEqual(result["status"], "illustrated")

    def test_illustrate_replaces_stale_package_image_block_on_force(self):
        old_url = (
            "https://raw.githubusercontent.com/sztimhdd/AI_Daily/main/outputs/"
            "2026/08/20/everyone-says-stripe-bet-on-the-singularity/images/01.webp"
        )
        self.write_article(
            "# Headline\n\nThe receipt tells a colder story.\n\n"
            f"![Old image]({old_url})\n*Old editorial caption.*\n"
        )
        plan = {"status": "generated", "images": [
            {"id": "01", "anchor": "The receipt tells a colder story.",
             "alt": "Fresh image.", "caption": "Fresh editorial line."},
        ]}
        manifest = {"images": [
            {"id": "01", "status": "generated", "format": "webp"},
        ]}
        from unittest import mock

        with mock.patch.object(visuals, "run_plan", return_value=plan), \
             mock.patch.object(visuals, "run_generate", return_value={"status": "generated", "manifest": manifest}):
            visuals.run_illustrate(self.rp, force=True)
        article = (self.rp.work_dir / draft_en.EN_ARTICLE_MD).read_text(encoding="utf-8")
        self.assertNotIn("Old editorial caption.", article)
        self.assertIn("Fresh editorial line.", article)
        self.assertEqual(article.count("images/01.webp"), 1)


if __name__ == "__main__":
    unittest.main()
