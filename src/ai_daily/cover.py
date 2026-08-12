"""Optional cover handling: validation, ChatGPT-export locator, move.

The cover stage is OPTIONAL and NONBLOCKING.  A missing source, an
unknown format or truncated bytes always yield a structured failed
``CoverResult`` — never an exception, never a pipeline stop.  No
credential or image-generation service is ever automated: the cover is
only adopted from an existing local export the editor produced.

Supported formats are validated from raw bytes with the standard
library only:

- PNG: signature + IHDR width/height.
- JPEG: SOI + first SOF frame dimensions.
- WebP: RIFF/WEBP container, VP8 / VP8L / VP8X dimension chunks.
"""

from __future__ import annotations

import dataclasses
import pathlib
import re
import shutil
import struct

COVER_STEM = "cover"
CHATGPT_PREFIX = "ChatGPT Image"


@dataclasses.dataclass
class CoverResult:
    ok: bool
    reason: str = ""
    path: str = ""
    width: int = 0
    height: int = 0
    format: str = ""


def sniff_format(data: bytes) -> str:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8"):
        return "jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return ""


def _png_dimensions(data: bytes):
    # IHDR must be the first chunk after the 8-byte signature.
    if len(data) < 8 + 8 + 16:
        return None
    length = struct.unpack(">I", data[8:12])[0]
    if data[12:16] != b"IHDR" or length < 13:
        return None
    width, height = struct.unpack(">II", data[16:24])
    if width <= 0 or height <= 0:
        return None
    return width, height


def _jpeg_dimensions(data: bytes):
    i = 2
    n = len(data)
    while i + 9 <= n:
        if data[i] != 0xFF:
            return None
        marker = data[i + 1]
        # Standalone markers without a segment payload.
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        if marker == 0xFF:  # fill byte
            i += 1
            continue
        seg_len = struct.unpack(">H", data[i + 2 : i + 4])[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            if i + 9 > n:
                return None
            height, width = struct.unpack(">HH", data[i + 5 : i + 9])
            if width <= 0 or height <= 0:
                return None
            return width, height
        i += 2 + seg_len
    return None


def _webp_dimensions(data: bytes):
    i = 12
    n = len(data)
    while i + 8 <= n:
        fourcc = data[i : i + 4]
        size = struct.unpack("<I", data[i + 4 : i + 8])[0]
        body = data[i + 8 : i + 8 + size]
        if fourcc == b"VP8X" and len(body) >= 10:
            width = int.from_bytes(body[4:7], "little") + 1
            height = int.from_bytes(body[7:10], "little") + 1
            return (width, height) if width > 0 and height > 0 else None
        if fourcc == b"VP8 " and len(body) >= 10 and body[3:6] == b"\x9d\x01\x2a":
            width = struct.unpack("<H", body[6:8])[0] & 0x3FFF
            height = struct.unpack("<H", body[8:10])[0] & 0x3FFF
            return (width, height) if width > 0 and height > 0 else None
        if fourcc == b"VP8L" and len(body) >= 5 and body[0] == 0x2F:
            bits = struct.unpack("<I", body[1:5])[0]
            width = (bits & 0x3FFF) + 1
            height = ((bits >> 14) & 0x3FFF) + 1
            return (width, height) if width > 0 and height > 0 else None
        i += 8 + size + (size & 1)
    return None


def validate_cover(path) -> CoverResult:
    """Validate image bytes: non-empty, readable, known format, dims."""
    path = pathlib.Path(path)
    try:
        if not path.is_file():
            return CoverResult(ok=False, reason=f"cover not found: {path}")
        data = path.read_bytes()
    except OSError as exc:
        return CoverResult(ok=False, reason=f"cover unreadable: {exc}")
    if not data:
        return CoverResult(ok=False, reason=f"cover file is empty: {path}")
    fmt = sniff_format(data)
    if not fmt:
        return CoverResult(ok=False, reason="unrecognized image format (want PNG/JPEG/WebP)")
    dims = {"png": _png_dimensions, "jpeg": _jpeg_dimensions, "webp": _webp_dimensions}[fmt](data)
    if dims is None:
        return CoverResult(ok=False, reason=f"{fmt} bytes truncated or missing dimensions")
    return CoverResult(
        ok=True, reason="", path=str(path), width=dims[0], height=dims[1], format=fmt
    )


def locate_chatgpt_image(source_dir):
    """Newest local ChatGPT export in ``source_dir`` (by mtime).

    Only files whose name starts with ``ChatGPT Image`` qualify; other
    images are never touched.  Returns None when nothing qualifies.
    """
    source_dir = pathlib.Path(source_dir)
    if not source_dir.is_dir():
        return None
    candidates = [
        p
        for p in source_dir.iterdir()
        if p.is_file() and p.name.startswith(CHATGPT_PREFIX)
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _existing_cover(run_paths):
    for ext in ("png", "jpg", "jpeg", "webp"):
        path = run_paths.work_dir / f"{COVER_STEM}.{ext}"
        if path.is_file():
            return path
    return None


def run(run_paths, source_dir=None, force: bool = False) -> CoverResult:
    """Optional cover adoption.  Always returns; never raises.

    Resume: a previously adopted, still-valid cover is reused without
    touching ``source_dir``.  When nothing usable exists the result is
    a soft failure the pipeline may ignore.
    """
    try:
        existing = _existing_cover(run_paths)
        if existing is not None and not force:
            result = validate_cover(existing)
            if result.ok:
                result.reason = "resumed existing cover"
                return result
        if source_dir is None:
            return CoverResult(ok=False, reason="no cover source dir given (cover is optional)")
        located = locate_chatgpt_image(source_dir)
        if located is None:
            return CoverResult(
                ok=False, reason=f"no ChatGPT export found in {source_dir} (cover is optional)"
            )
        ext = located.suffix.lstrip(".").lower() or "png"
        if ext == "jpeg":
            ext = "jpg"
        dest = run_paths.work_dir / f"{COVER_STEM}.{ext}"
        shutil.move(str(located), str(dest))
        result = validate_cover(dest)
        if not result.ok:
            result.reason = f"located cover failed validation: {result.reason}"
        return result
    except Exception as exc:  # nonblocking by contract
        return CoverResult(ok=False, reason=f"cover stage error: {type(exc).__name__}: {exc}")
