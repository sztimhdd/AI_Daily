"""RSS/Atom collection: fetch, parse, time-filter, dedup, stats, pool.

Code does all raw feed work so the model never reads 93 feeds one by
one; it reads the compressed intelligence pool instead.  Any single
feed failure is recorded and never blocks the AIHOT main path.

Date semantics (documented contract):

- Dates are read from ``pubDate`` (RSS), ``dc:date`` (Dublin Core,
  namespace ``http://purl.org/dc/elements/1.1/``) or Atom
  ``updated``/``published``.
- Items dated before the window cutoff are dropped and counted in
  ``stats["items_out_of_window"]``.
- Items with no date, or a date no parser understands, are KEPT with
  ``published == ""`` and counted in ``stats["undated_items"]``:
  dropping them would silently lose sources that simply omit dates.
- ``stats["by_feed"]`` maps each successfully parsed feed URL to the
  number of items it contributed to the kept pool (feed contribution).
- ``stats["failures"]`` is the machine-readable per-feed failure list
  (``{"url": ..., "error": ...}`` entries); ``stats["feeds_failed"]``
  always equals ``len(stats["failures"])``.  The same failures stay in
  the human-readable pool markdown.
"""

from __future__ import annotations

import dataclasses
import datetime
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ATOM_NS = "{http://www.w3.org/2005/Atom}"
DC_DATE_TAG = "{http://purl.org/dc/elements/1.1/}date"
USER_AGENT = "AI_Daily/0.1 (+rss-collector; stdlib)"

_TITLE_PUNCT_RE = re.compile(r"[\W_]+", re.UNICODE)


def normalize_title(title: str) -> str:
    return _TITLE_PUNCT_RE.sub(" ", title.lower()).strip()


def normalize_url(url: str) -> str:
    parts = urllib.parse.urlsplit(url.strip())
    path = parts.path.rstrip("/")
    return urllib.parse.urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), path, parts.query, "")
    )


def _parse_date(value: str):
    if not value:
        return None
    value = value.strip()
    try:
        return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        pass
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
        try:
            return datetime.datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _text(el, tag: str) -> str:
    child = el.find(tag)
    return (child.text or "").strip() if child is not None and child.text else ""


def parse_feed(body: bytes) -> list:
    """Parse RSS 2.0 or Atom payload into raw item dicts."""
    root = ET.fromstring(body)
    items = []
    if root.tag == "rss":
        for item in root.iter("item"):
            link = _text(item, "link")
            date_raw = (
                _text(item, "pubDate")
                or _text(item, DC_DATE_TAG)
                or _text(item, "dc:date")  # tolerate undeclared literal prefix
            )
            items.append(
                {
                    "title": _text(item, "title"),
                    "url": link,
                    "date_raw": date_raw,
                    "summary": _text(item, "description"),
                }
            )
    elif root.tag == f"{ATOM_NS}feed" or root.tag == "feed":
        ns = ATOM_NS if root.tag.startswith("{") else ""
        for entry in root.iter(f"{ns}entry"):
            link_el = entry.find(f"{ns}link")
            url = link_el.get("href", "") if link_el is not None else ""
            title = _text(entry, f"{ns}title")
            date_raw = _text(entry, f"{ns}updated") or _text(entry, f"{ns}published")
            summary = _text(entry, f"{ns}summary") or _text(entry, f"{ns}content")
            items.append(
                {"title": title, "url": url, "date_raw": date_raw, "summary": summary}
            )
    else:
        raise ValueError(f"unrecognized feed root element: {root.tag}")
    return items


@dataclasses.dataclass
class CollectResult:
    items: list
    failures: list
    stats: dict


def _default_fetch(url: str, timeout: float) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def collect(urls, fetch=None, now=None, window_hours: int = 96, timeout: float = 15.0) -> CollectResult:
    """Collect all feeds; per-feed failures never raise.

    ``urls`` may be any iterable, including a one-shot generator: it is
    materialized first so feed statistics stay correct.
    """
    fetch = fetch or _default_fetch
    urls = list(urls)
    if isinstance(now, str):
        now_dt = datetime.datetime.fromisoformat(now)
    else:
        now_dt = now or datetime.datetime.now(datetime.timezone.utc)
    if now_dt.tzinfo is None:
        now_dt = now_dt.replace(tzinfo=datetime.timezone.utc)
    cutoff = now_dt - datetime.timedelta(hours=window_hours)

    items, failures = [], []
    seen_urls, seen_titles = set(), set()
    items_seen, dup_removed = 0, 0
    out_of_window, undated = 0, 0
    by_feed: dict = {}

    for url in urls:
        try:
            body = fetch(url, timeout)
        except Exception as exc:  # network, HTTP, timeout: never block
            failures.append({"url": url, "error": f"fetch failed: {exc}"})
            continue
        try:
            raw_items = parse_feed(body)
        except Exception as exc:
            failures.append({"url": url, "error": f"parse failed: {exc}"})
            continue
        kept_here = 0
        for raw in raw_items:
            items_seen += 1
            if not raw["title"] or not raw["url"]:
                dup_removed += 1
                continue
            when = _parse_date(raw["date_raw"])
            if when is not None:
                if when.tzinfo is None:
                    when = when.replace(tzinfo=datetime.timezone.utc)
                if when < cutoff:
                    out_of_window += 1
                    continue
            else:
                undated += 1
            nurl = normalize_url(raw["url"])
            ntitle = normalize_title(raw["title"])
            if nurl in seen_urls or ntitle in seen_titles:
                dup_removed += 1
                continue
            seen_urls.add(nurl)
            seen_titles.add(ntitle)
            items.append(
                {
                    "title": raw["title"].strip(),
                    "url": raw["url"].strip(),
                    "published": when.isoformat() if when else "",
                    "summary": raw["summary"][:280],
                    "feed": url,
                    "origin": "rss",
                }
            )
            by_feed[url] = by_feed.get(url, 0) + 1
            kept_here += 1
        if kept_here == 0 and not raw_items:
            failures.append({"url": url, "error": "feed parsed but contained no items"})

    stats = {
        "feeds_requested": len(urls),
        "feeds_ok": len(urls) - len(failures),
        "feeds_failed": len(failures),
        "failures": failures,
        "items_seen": items_seen,
        "items_kept": len(items),
        "duplicates_removed": dup_removed,
        "items_out_of_window": out_of_window,
        "undated_items": undated,
        "by_feed": by_feed,
        "window_hours": window_hours,
    }
    return CollectResult(items=items, failures=failures, stats=stats)


def compress_pool(result: CollectResult, max_per_source: int = 3) -> dict:
    """Compressed intelligence pool: capped items per source + totals."""
    by_source: dict = {}
    for item in result.items:
        by_source.setdefault(item["feed"], []).append(item)
    sources = []
    for feed, feed_items in sorted(by_source.items()):
        sources.append(
            {
                "feed": feed,
                "count": len(feed_items),
                "items": [
                    {"title": it["title"], "url": it["url"], "published": it["published"]}
                    for it in feed_items[:max_per_source]
                ],
            }
        )
    return {
        "sources": sources,
        "failures": result.failures,
        "totals": result.stats,
    }


def pool_markdown(pool: dict) -> str:
    lines = ["# RSS 压缩情报池", ""]
    t = pool["totals"]
    lines.append(
        f"成功 {t['feeds_ok']} / 失败 {t['feeds_failed']} 个源；"
        f"保留 {t['items_kept']} 条（去重 {t['duplicates_removed']} 条）；"
        f"时间窗 {t['window_hours']} 小时。"
    )
    lines.append("")
    for src in pool["sources"]:
        lines.append(f"## {src['feed']}（{src['count']} 条）")
        for it in src["items"]:
            date = f" · {it['published'][:16]}" if it["published"] else ""
            lines.append(f"- [{it['title']}]({it['url']}){date}")
        lines.append("")
    if pool["failures"]:
        lines.append("## 失败记录（不阻塞主流程）")
        for f in pool["failures"]:
            lines.append(f"- {f['url']}: {f['error']}")
        lines.append("")
    return "\n".join(lines)
