"""Deterministic English editorial quality gate (bilingual editing layer).

Runs the Python-checkable subset of the spec §4 checks against an English
draft, before assembly.  Codex handles editorial judgment (voice, rhythm,
fact/inference/opinion distinction, walled-downgrade reasoning); this
module only checks what is deterministic and rejects/annotates — it never
rewrites.

Verdicts:
- ``pass``: every check is clean.
- ``pass_with_notes``: clean but with recorded minor notes.
- ``revise``: style/rhythm/de-AI/structural failure — redraft and re-gate.
- ``evidence_recovery``: evidence-boundary hard gate failed — back to research.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from . import deslop

EN_MIN_WORDS = 800
EN_MAX_WORDS = 1200
MAX_SENTENCES_PER_PARAGRAPH = 3

VERDICTS = ("pass", "pass_with_notes", "revise", "evidence_recovery")

_LINK_RE = re.compile(r"\]\((https?://[^)\s]+)\)")

_PLACEHOLDER_RES = (
    re.compile(r"\{\[\s*IMG_\d+\s*\]\}", re.I),
    re.compile(r"\[\s*IMG_\d+\s*\]", re.I),
    re.compile(r"!\[[^\]]*\]\([^)]*placeholder[^)]*\)", re.I),
    re.compile(r"\{\{.*?\}\}", re.S),
)

_AI_TRACE_TAG_RES = [
    re.compile(r"^\s*(?:in\s+)?summary\s*:", re.I | re.M),
    re.compile(r"^\s*conclusion\s*:", re.I | re.M),
    re.compile(r"^\s*key\s+takeaways?\s*:", re.I | re.M),
    re.compile(r"\[editor'?s?\s*note\]", re.I),
    re.compile(r"\[ed\.\s*note\]", re.I),
]
_HTML_TAG_RE = re.compile(r"</?[a-zA-Z][a-zA-Z0-9]*(?:\s[^<>]*)?>")

# A bold delimiter sandwiched between two word characters is glued to text
# where a space belongs (``The**cost**is``).  Paragraph-start lead-ins
# (``**Point.** text``) and inline ``**cost**`` are fine.
_BOLD_ABUT_RE = re.compile(r"\w\*\*\w")

_WORD_RE = re.compile(r"[\w'\u2019-]+")

_ABBREV_RE = re.compile(
    r"\b(e\.g|i\.e|etc|vs|dr|mr|ms|prof|inc|ltd|co|u\.s|st|no|approx)\.",
    re.I,
)
_SENTENCE_END_RE = re.compile(r"[.!?](?=\s|$)")

_WALLED_HOST_SUFFIXES = (
    "zhihu.com", "mp.weixin.qq.com", "weixin.qq.com", "wechat.com",
)

_WALLED_DOWNGRADE_MARKERS = [
    re.compile(r"unverified", re.I),
    re.compile(r"not (?:yet |independently )?verified", re.I),
    re.compile(r"could not (?:be )?(?:fetched|verify|verified)", re.I),
    re.compile(r"(?:single )?walled[ -]source", re.I),
    re.compile(r"unconfirmed", re.I),
    re.compile(r"uncorroborated", re.I),
    re.compile(r"unable to (?:fetch|verify|confirm)", re.I),
]

_MARKDOWN_LINK_TARGET_RE = re.compile(r"\]\(https?://[^)\s]+\)")
_BARE_URL_RE = re.compile(r"https?://\S+")


@dataclass(frozen=True)
class Finding:
    check: str
    message: str
    line: int = 0


@dataclass
class QualityResult:
    verdict: str
    findings: list = field(default_factory=list)
    word_count: int = 0
    paragraph_count: int = 0

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "word_count": self.word_count,
            "paragraph_count": self.paragraph_count,
            "findings": [
                {"check": f.check, "message": f.message, "line": f.line}
                for f in self.findings
            ],
        }


def word_count(text: str) -> int:
    """Count English words (apostrophes and hyphens join, digits count)."""
    return len(_WORD_RE.findall(text or ""))


def _body_words(text: str) -> int:
    """Word count excluding URL/link targets, so URLs never inflate length."""
    stripped = _MARKDOWN_LINK_TARGET_RE.sub("]", text or "")
    stripped = _BARE_URL_RE.sub(" ", stripped)
    return word_count(stripped)


def _count_sentences(paragraph: str) -> int:
    """Sentence ends in one paragraph, ignoring common abbreviations."""
    protected = _ABBREV_RE.sub(lambda m: m.group(0).replace(".", "\u0000"),
                               paragraph or "")
    return len(_SENTENCE_END_RE.findall(protected))


def _paragraphs(text: str) -> list:
    return [
        p.strip()
        for p in (text or "").split("\n\n")
        if p.strip()
    ]


def _walled_failed_sources(evidence: dict) -> list:
    """Walled-platform sources that were not successfully fetched."""
    out = []
    for src in (evidence or {}).get("sources") or []:
        if not isinstance(src, dict):
            continue
        host = (urlsplit(src.get("url") or "").hostname or "").lower()
        if not any(host.endswith(s) for s in _WALLED_HOST_SUFFIXES):
            continue
        if str(src.get("status") or "").lower() != "fetched":
            out.append(src)
    return out


def check_en(text: str, evidence: dict, min_words: int = EN_MIN_WORDS,
             max_words: int = EN_MAX_WORDS) -> QualityResult:
    """Run the deterministic English checks and return a verdict.

    ``evidence`` is the evidence-package object (``{"sources": [...]}``)
    produced by the 06 targeted loop; only its walled-source fetch status is
    consulted here.
    """
    findings: list = []
    hard: list = []      # evidence-boundary problems -> evidence_recovery
    paragraphs = _paragraphs(text)
    words = _body_words(text)

    # -- evidence boundary (hard gate) --------------------------------------
    if not _LINK_RE.search(text or ""):
        hard.append(Finding("links", "article carries no inline source links"))

    certainty = [f for f in deslop.check_text_en(text or "")
                 if f.category == "unsupported-certainty"]
    if certainty:
        hard.append(Finding(
            "unsupported-certainty",
            "unsupported certainty without a source: "
            + "; ".join(f.phrase for f in certainty[:3]),
            certainty[0].line,
        ))

    for src in _walled_failed_sources(evidence):
        url = src.get("url") or ""
        host = urlsplit(url).hostname or "walled"
        # Only require a downgrade when the article actually cites the walled
        # source; an unused failed-fetch URL in the package is not a claim.
        if url not in (text or "") and host not in (text or ""):
            continue
        if not any(m.search(text or "") for m in _WALLED_DOWNGRADE_MARKERS):
            hard.append(Finding(
                "walled-downgrade",
                f"walled source {host} was not fetched and is cited "
                "without a downgrade marker",
            ))
            break

    # -- de-AI / style / rhythm (revise) ------------------------------------
    slop = [f for f in deslop.check_text_en(text or "")
            if f.category != "unsupported-certainty"]
    for f in slop:
        findings.append(Finding(
            f"de-ai:{f.category}", f"“{f.phrase}”", f.line
        ))

    if words < min_words or words > max_words:
        findings.append(Finding(
            "word-count",
            f"{words} words outside [{min_words}, {max_words}]",
        ))

    for i, para in enumerate(paragraphs, 1):
        if _count_sentences(para) > MAX_SENTENCES_PER_PARAGRAPH:
            findings.append(Finding(
                "sentence-rule",
                f"paragraph {i} exceeds {MAX_SENTENCES_PER_PARAGRAPH} sentences",
            ))

    for rx in _AI_TRACE_TAG_RES:
        m = rx.search(text or "")
        if m:
            findings.append(Finding("ai-trace-tag", m.group(0).strip()))
            break
    m = _HTML_TAG_RE.search(text or "")
    if m:
        findings.append(Finding("markdown-purity", f"raw HTML tag {m.group(0)!r}"))

    for rx in _PLACEHOLDER_RES:
        m = rx.search(text or "")
        if m:
            findings.append(Finding("placeholder", f"unreplaced {m.group(0)!r}"))
            break

    # -- minor notes (pass_with_notes) --------------------------------------
    notes = []
    if _BOLD_ABUT_RE.search(text or ""):
        notes.append(Finding("bold-spacing", "bold marker abuts a word"))

    if hard:
        verdict = "evidence_recovery"
        findings = hard + findings
    elif findings:
        verdict = "revise"
    elif notes:
        verdict = "pass_with_notes"
        findings = notes
    else:
        verdict = "pass"

    return QualityResult(
        verdict=verdict,
        findings=findings,
        word_count=words,
        paragraph_count=len(paragraphs),
    )


def report(result: QualityResult) -> str:
    """One-line-per-finding report of a quality gate run."""
    if result.verdict == "pass":
        return (
            f"english quality gate: PASS "
            f"({result.word_count} words, {result.paragraph_count} paragraphs)"
        )
    lines = [
        f"english quality gate: {result.verdict.upper()} "
        f"({result.word_count} words, {result.paragraph_count} paragraphs)"
    ]
    for f in result.findings:
        lines.append(f"- [{f.check}] {f.message}")
    return "\n".join(lines)
