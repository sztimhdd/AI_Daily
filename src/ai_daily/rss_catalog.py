"""Provenance-aware RSS source catalog compiled from the core-IP JSONs.

The five immutable legacy JSONs are the only source of truth.  This
module extracts every feed-like source entry with its provenance
(file + node), preserves duplicate entries across legacy pool nodes,
and documents which URLs are extractable feeds.  It never invents
feeds: a URL enters the catalog only by being found verbatim in a
legacy file.

V1 invariants (asserted by tests):

- 93 legacy entries = 91 source occurrences (88 RSS/Atom-style URLs,
  including the Zhihu hot-list feed API endpoint, plus 3 plain
  ``.xml`` blog feeds; URLs repeated across legacy pool nodes keep one
  occurrence per node) + 2 auxiliary services (Tavily Search API,
  Event Registry API) counted once each.
- 73 unique extractable URLs = unique URLs unambiguously identifiable
  as feeds by marker (72 RSS/Atom XML feeds + 1 JSON feed API).  Three
  additional legacy plain ``.xml`` blog feeds are preserved and
  fetchable, giving 76 unique fetchable sources.

Extractability is a marker heuristic, not runtime verification: a URL
is marked extractable when it carries a feed marker (``feed``/``rss``/
``atom``), ends in ``.xml``, or is the known Zhihu feed API endpoint.
No network request is made at catalog build time; dead or moved feeds
are discovered (and recorded as nonblocking failures) only during the
collect stage.

Regeneration is deterministic and independent of wall-clock time: the
catalog carries no timestamp, and building it twice from the same
core-IP files yields byte-identical output.
"""

from __future__ import annotations

import json
import pathlib
import re

CORE_IP_FILES = [
    "workflows/reference/公众号选题写稿配图一体化工作流.json",
    "[Atomic] Researcher_Skill.json",
    "[Atomic] Topic_Survey_Skill.json",
    "[Atomic] Universal Draft Writing.json",
    "Long-Content-Writing.json",
]

URL_RE = re.compile(r"https?://[^\s\"'\\<>,)）\]]+")
FEED_MARKER_RE = re.compile(r"(feed|rss|atom)", re.I)

AUXILIARY_SERVICES = [
    {"name": "Tavily Search API", "match": "tavily.com", "role": "web_search"},
    {"name": "Event Registry API", "match": "eventregistry.org", "role": "news_api"},
]


def _classify(url: str):
    low = url.lower()
    if any(svc["match"] in low for svc in AUXILIARY_SERVICES):
        return "auxiliary"
    if "zhihu.com/api" in low:
        return "json_feed"
    if FEED_MARKER_RE.search(low):
        return "rss_xml"
    if low.endswith(".xml"):
        return "rss_xml"
    return None


def build_catalog(repo_root) -> dict:
    repo_root = pathlib.Path(repo_root)
    sources: dict = {}   # url -> record
    auxiliary: dict = {} # name -> record

    for rel in CORE_IP_FILES:
        path = repo_root / rel
        data = json.loads(path.read_text(encoding="utf-8"))
        for node in data.get("nodes", []):
            blob = json.dumps(node.get("parameters", {}), ensure_ascii=False)
            for url in URL_RE.findall(blob):
                url = url.rstrip(".")
                kind = _classify(url)
                if kind is None:
                    continue
                if kind == "auxiliary":
                    svc = next(s for s in AUXILIARY_SERVICES if s["match"] in url.lower())
                    rec = auxiliary.setdefault(
                        svc["name"],
                        {
                            "name": svc["name"],
                            "role": svc["role"],
                            "extractable_feed": False,
                            "provenance": [],
                        },
                    )
                    entry = {"file": rel, "node": node.get("name", "")}
                    if entry not in rec["provenance"]:
                        rec["provenance"].append(entry)
                    continue
                identifiable = bool(FEED_MARKER_RE.search(url.lower()))
                rec = sources.setdefault(
                    url,
                    {
                        "url": url,
                        "format": "json_feed" if kind == "json_feed" else "rss_xml",
                        "extractable": True,
                        "identifiable": identifiable,
                        "provenance": [],
                    },
                )
                rec["provenance"].append({"file": rel, "node": node.get("name", "")})

    source_list = sorted(sources.values(), key=lambda r: r["url"])
    aux_list = sorted(auxiliary.values(), key=lambda r: r["name"])
    occurrences = sum(len(r["provenance"]) for r in source_list)
    legacy_entries = occurrences + len(aux_list)

    return {
        "catalog_version": 1,
        "generated_from": CORE_IP_FILES,
        "summary": {
            "legacy_entries": legacy_entries,
            "feed_occurrences": occurrences,
            "auxiliary_services": len(aux_list),
            "entry_math": (
                f"{legacy_entries} = {occurrences} source occurrences "
                f"+ {len(aux_list)} auxiliary services"
            ),
            "unique_extractable_urls": sum(1 for r in source_list if r["identifiable"]),
            "unique_fetchable_urls": len(source_list),
            "dual_pool_urls": sum(1 for r in source_list if len(r["provenance"]) >= 2),
            "extractability_note": (
                "extractable is a marker heuristic (feed/rss/atom marker, .xml "
                "suffix, known JSON feed API); it is not runtime verification"
            ),
        },
        "sources": source_list,
        "auxiliary_services": aux_list,
    }


def write_catalog(catalog: dict, path) -> pathlib.Path:
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
