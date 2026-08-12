"""Tests for optional cover validation and the ChatGPT image locator.

Cover handling is optional and nonblocking: any failure (missing file,
unknown format, truncated bytes) must produce a structured failed
CoverResult, never an exception, never a pipeline stop.
"""

import pathlib
import struct
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import cover, paths, state


def make_png(width=16, height=9):
    def chunk(tag, payload):
        return (
            struct.pack(">I", len(payload))
            + tag
            + payload
            + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IEND", b"")
    )


def make_jpeg(width=640, height=360):
    sof = struct.pack(">BHHBB", 8, height, width, 3, 0)
    return b"\xff\xd8" + b"\xff\xc0" + struct.pack(">H", len(sof) + 2) + sof + b"\xff\xd9"


def make_webp_vp8x(width=512, height=288):
    payload = b"\x00\x00\x00\x00" + (width - 1).to_bytes(3, "little") + (height - 1).to_bytes(3, "little")
    chunk = b"VP8X" + struct.pack("<I", len(payload)) + payload
    riff = b"RIFF" + struct.pack("<I", 4 + len(chunk)) + b"WEBP" + chunk
    return riff


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name, data):
        path = self.dir / name
        path.write_bytes(data)
        return path

    def test_valid_png_dimensions_parsed(self):
        result = cover.validate_cover(self.write("c.png", make_png(32, 18)))
        self.assertTrue(result.ok, result.reason)
        self.assertEqual((result.width, result.height), (32, 18))
        self.assertEqual(result.format, "png")

    def test_valid_jpeg_dimensions_parsed(self):
        result = cover.validate_cover(self.write("c.jpg", make_jpeg(640, 360)))
        self.assertTrue(result.ok, result.reason)
        self.assertEqual((result.width, result.height), (640, 360))
        self.assertEqual(result.format, "jpeg")

    def test_valid_webp_dimensions_parsed(self):
        result = cover.validate_cover(self.write("c.webp", make_webp_vp8x(512, 288)))
        self.assertTrue(result.ok, result.reason)
        self.assertEqual((result.width, result.height), (512, 288))
        self.assertEqual(result.format, "webp")

    def test_empty_file_fails_softly(self):
        result = cover.validate_cover(self.write("empty.png", b""))
        self.assertFalse(result.ok)
        self.assertIn("empty", result.reason)

    def test_unknown_bytes_fail_softly(self):
        result = cover.validate_cover(self.write("fake.png", b"not an image at all"))
        self.assertFalse(result.ok)
        self.assertFalse(result.width or result.height)

    def test_truncated_png_fails_softly(self):
        result = cover.validate_cover(self.write("trunc.png", make_png()[:12]))
        self.assertFalse(result.ok)

    def test_missing_file_fails_softly(self):
        result = cover.validate_cover(self.dir / "nope.png")
        self.assertFalse(result.ok)
        self.assertIn("not", result.reason.lower())


class ChatGptLocatorTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def touch(self, name, mtime):
        path = self.dir / name
        path.write_bytes(make_png())
        import os
        os.utime(path, (mtime, mtime))
        return path

    def test_newest_chatgpt_image_selected_by_mtime(self):
        self.touch("ChatGPT Image Aug 1, 2026, 10_00_00 AM.png", 100)
        newest = self.touch("ChatGPT Image Aug 12, 2026, 09_15_32 PM.png", 300)
        self.touch("ChatGPT Image Aug 5, 2026, 08_00_00 AM.png", 200)
        self.touch("screenshot.png", 400)  # not a ChatGPT export
        self.assertEqual(cover.locate_chatgpt_image(self.dir), newest)

    def test_no_chatgpt_image_returns_none(self):
        self.touch("screenshot.png", 100)
        self.assertIsNone(cover.locate_chatgpt_image(self.dir))

    def test_missing_dir_returns_none(self):
        self.assertIsNone(cover.locate_chatgpt_image(self.dir / "absent"))


class AdoptCoverTests(unittest.TestCase):
    """run() moves the newest ChatGPT export into the run's work dir."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.rp = paths.RunPaths.for_date(self.root, "2026-08-12")
        self.rp.ensure_work_dir()
        state.init_state(self.rp)
        self.src = self.root / "downloads"
        self.src.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def test_move_located_cover_into_work_dir(self):
        src = self.src / "ChatGPT Image Aug 12, 2026, 09_15_32 PM.png"
        src.write_bytes(make_png(100, 56))
        result = cover.run(self.rp, source_dir=self.src)
        self.assertTrue(result.ok, result.reason)
        self.assertTrue(pathlib.Path(result.path).is_file())
        self.assertFalse(src.exists(), "locator must move, not copy")
        self.assertEqual((result.width, result.height), (100, 56))

    def test_no_source_is_soft_failure(self):
        result = cover.run(self.rp, source_dir=self.src)
        self.assertFalse(result.ok)
        self.assertTrue(result.reason)

    def test_resume_keeps_existing_valid_cover(self):
        src = self.src / "ChatGPT Image Aug 12, 2026, 09_15_32 PM.png"
        src.write_bytes(make_png())
        first = cover.run(self.rp, source_dir=self.src)
        second = cover.run(self.rp, source_dir=self.src)
        self.assertTrue(second.ok)
        self.assertEqual(second.path, first.path)

    def test_located_but_invalid_image_is_soft_failure(self):
        src = self.src / "ChatGPT Image Aug 12, 2026, 09_15_32 PM.png"
        src.write_bytes(b"garbage bytes, not an image")
        result = cover.run(self.rp, source_dir=self.src)
        self.assertFalse(result.ok)
        self.assertTrue(result.reason)


if __name__ == "__main__":
    unittest.main()
