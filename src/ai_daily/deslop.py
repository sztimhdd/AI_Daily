"""Executable remove-ai-slop contract: 8 categories, deterministic checks.

Compiled from the immutable core IP (see knowledge/remove-ai-slop.md for
provenance): the reference workflow's 去AI味 node MODULE 1 blacklist and
the 中文图文编辑 banned-word list.  This module only detects and reports;
rewriting is the draft generator's job.
"""

from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass

CATEGORIES = [
    {
        "id": "empty-connectives",
        "name": "空泛 AI 连接词",
        "description": "僵硬连接词：此外、然而、总而言之、综上所述、值得注意的是、总之。",
    },
    {
        "id": "template-opening",
        "name": "模板化开头",
        "description": "烂大街开场：随着...的飞速发展、在当今的数字化时代、众所周知等。",
    },
    {
        "id": "mechanical-enumeration",
        "name": "机械总分总",
        "description": "首先/其次/最后 成对出现构成的机械枚举结构。",
    },
    {
        "id": "over-parallelism",
        "name": "过度对称排比",
        "description": "不仅是...更是（一次即判）；不是...而是、既...又等软模式累计两次判定。",
    },
    {
        "id": "corporate-bookish",
        "name": "过度书面化表达",
        "description": "大厂黑话、伪高级修辞与机翻公关废话黑名单。",
    },
    {
        "id": "marketing-hype",
        "name": "空泛营销词",
        "description": "解锁、变革性、颠覆性、里程碑式、重磅等无信息量营销词。",
    },
    {
        "id": "unsupported-certainty",
        "name": "无依据确定性结论",
        "description": "必将、必然、毫无疑问、注定等无来源支撑的确定性断言。",
    },
    {
        "id": "stiff-ending-uplift",
        "name": "僵硬结尾升华",
        "description": "结尾段的让我们拭目以待、未来可期、开启新纪元式升华。",
    },
]

CATEGORY_IDS = [c["id"] for c in CATEGORIES]
_NAMES = {c["id"]: c["name"] for c in CATEGORIES}

# -- blacklists (compiled from core IP; see knowledge/remove-ai-slop.md) ----

_EMPTY_CONNECTIVES = ["此外", "然而", "总而言之", "综上所述", "值得注意的是", "总之"]

_TEMPLATE_OPENING_RES = [
    re.compile(r"随着.{0,20}(飞速发展|快速发展|迅猛发展|到来|普及)"),
    re.compile(r"在当今.{0,12}(时代|社会|世界)"),
    re.compile(r"众所周知"),
    re.compile(r"不可否认的是"),
    re.compile(r"成为了?热门话题"),
]

_ENUM_MARKERS = ["首先", "其次", "最后"]

_ABSOLUTE_PARALLEL_RES = [re.compile(r"不仅(?:仅)?是?.{0,40}?更是")]
_SOFT_PARALLEL_RES = [
    re.compile(r"不是.{0,40}?而是"),
    re.compile(r"既.{0,40}?又"),
    re.compile(r"一方面.{0,60}?另一方面"),
]

_CORPORATE_BOOKISH = [
    # 大厂假大空与造词
    "赋能", "闭环", "颗粒度", "抓手", "对齐", "拉通", "链路", "沉淀",
    "倒逼", "耦合", "解耦", "复盘", "迭代", "落地", "组合拳", "生态位",
    "顶层设计", "底层逻辑", "赛道", "势能", "心智", "痛点", "中台",
    # 伪高级修辞与宏大叙事
    "熵增", "熵减", "降维打击", "涌现", "奇点", "第一性原理", "飞轮效应",
    "数据引力", "长尾效应", "黑天鹅", "灰犀牛", "认知突围", "图谱",
    "矩阵", "共生", "共创", "全景", "蓝图", "基石", "催化剂",
    # 机翻腔与公关废话
    "致力于", "旨在", "标志着", "不可或缺", "至关重要", "具有深远的意义",
]

_MARKETING_HYPE = [
    "解锁", "变革性", "颠覆性", "里程碑式", "重磅", "王炸", "炸裂",
    "沸腾", "轰动",
]

_UNSUPPORTED_CERTAINTY = [
    "必将", "必然", "毫无疑问", "毋庸置疑", "注定", "一定会", "肯定会",
    "铁定",
]

_ENDING_UPLIFT = [
    "让我们拭目以待", "时间会给出答案", "未来可期", "开启新纪元",
    "新篇章", "让我们共同",
]


@dataclass(frozen=True)
class Finding:
    category: str
    name: str
    phrase: str
    line: int
    excerpt: str


def _mask_urls(text: str) -> str:
    """Blank out link targets so URL content never triggers findings."""
    text = re.sub(r"\]\([^)]*\)", "]( )", text)
    text = re.sub(r"https?://\S+", lambda m: " " * len(m.group(0)), text)
    return text


def _scan_phrases(text: str, phrases: list, category: str, names=None) -> list:
    """Find phrase occurrences, deduping overlaps in favor of longer hits."""
    names = _NAMES if names is None else names
    matches = []  # (start, end, phrase)
    for phrase in phrases:
        start = 0
        while True:
            idx = text.find(phrase, start)
            if idx < 0:
                break
            matches.append((idx, idx + len(phrase), phrase))
            start = idx + 1
    matches.sort(key=lambda m: (m[0], -(m[1] - m[0])))
    kept = []
    last_end = -1
    for s, e, phrase in matches:
        if s >= last_end:
            kept.append((s, e, phrase))
            last_end = e
    return _with_lines(text, kept, category, names)


def _scan_regexes(text: str, patterns: list, category: str, names=None) -> list:
    names = _NAMES if names is None else names
    kept = []
    for pat in patterns:
        for m in pat.finditer(text):
            kept.append((m.start(), m.end(), m.group(0)))
    kept.sort(key=lambda m: m[0])
    return _with_lines(text, kept, category, names)


def _with_lines(text: str, spans: list, category: str, names=None) -> list:
    names = _NAMES if names is None else names
    findings = []
    for s, e, phrase in spans:
        line_no = text.count("\n", 0, s) + 1
        line_start = text.rfind("\n", 0, s) + 1
        line_end = text.find("\n", e)
        if line_end < 0:
            line_end = len(text)
        excerpt = text[line_start:line_end].strip()
        if len(excerpt) > 80:
            excerpt = excerpt[:77] + "..."
        findings.append(
            Finding(category, names[category], phrase.strip(), line_no, excerpt)
        )
    return findings


def _last_paragraph(text: str) -> tuple:
    """Return (last_paragraph_text, char_offset_of_its_start)."""
    stripped = text.rstrip()
    idx = stripped.rfind("\n\n")
    if idx < 0:
        return stripped, 0
    return stripped[idx + 2 :], idx + 2


def _check_categories(
    masked: str,
    *,
    names: dict,
    connectives: list,
    template_res: list,
    enum_markers: list,
    absolute_parallel_res: list,
    soft_parallel_res: list,
    corporate: list,
    hype: list,
    certainty: list,
    ending: list,
) -> list:
    """Run the 8 category checks against one pre-masked, pre-cased text."""
    findings: list = []

    # 1. empty connectives
    findings += _scan_phrases(masked, connectives, "empty-connectives", names)

    # 2. template opening (first 200 chars only)
    opening = masked[:200]
    findings += _scan_regexes(opening, template_res, "template-opening", names)

    # 3. mechanical enumeration: >= 2 distinct markers present
    present = [m for m in enum_markers if m in masked]
    if len(present) >= 2:
        findings += _scan_phrases(masked, present, "mechanical-enumeration", names)

    # 4. over-parallelism: absolute patterns once; soft patterns need >= 2
    findings += _scan_regexes(masked, absolute_parallel_res, "over-parallelism", names)
    soft_spans = []
    for pat in soft_parallel_res:
        soft_spans.extend((m.start(), m.end(), m.group(0)) for m in pat.finditer(masked))
    if len(soft_spans) >= 2:
        soft_spans.sort(key=lambda m: m[0])
        findings += _with_lines(masked, soft_spans, "over-parallelism", names)

    # 5. corporate bookish
    findings += _scan_phrases(masked, corporate, "corporate-bookish", names)

    # 6. marketing hype
    findings += _scan_phrases(masked, hype, "marketing-hype", names)

    # 7. unsupported certainty
    findings += _scan_phrases(masked, certainty, "unsupported-certainty", names)

    # 8. stiff ending uplift (final paragraph only)
    last_para, offset = _last_paragraph(masked)
    for f in _scan_phrases(last_para, ending, "stiff-ending-uplift", names):
        findings.append(
            Finding(f.category, f.name, f.phrase,
                    masked.count("\n", 0, offset) + f.line, f.excerpt)
        )

    findings.sort(key=lambda f: (f.line, f.category))
    return findings


def check_text(text: str) -> list:
    """Run all 8 Chinese category checks; returns a list of ``Finding``."""
    return _check_categories(
        _mask_urls(text or ""),
        names=_NAMES,
        connectives=_EMPTY_CONNECTIVES,
        template_res=_TEMPLATE_OPENING_RES,
        enum_markers=_ENUM_MARKERS,
        absolute_parallel_res=_ABSOLUTE_PARALLEL_RES,
        soft_parallel_res=_SOFT_PARALLEL_RES,
        corporate=_CORPORATE_BOOKISH,
        hype=_MARKETING_HYPE,
        certainty=_UNSUPPORTED_CERTAINTY,
        ending=_ENDING_UPLIFT,
    )


# -- English de-AI contract (Lead Tech Editor; spec §4.2/§4.3) --------------

_EN_NAMES = {
    "empty-connectives": "Empty AI connectives",
    "template-opening": "Template opening",
    "mechanical-enumeration": "Mechanical enumeration",
    "over-parallelism": "Over-parallelism",
    "corporate-bookish": "Corporate bookish",
    "marketing-hype": "Marketing hype",
    "unsupported-certainty": "Unsupported certainty",
    "stiff-ending-uplift": "Stiff ending uplift",
}

_EN_EMPTY_CONNECTIVES = [
    "furthermore", "moreover", "in conclusion", "in summary", "to sum up",
    "it is worth noting", "it's worth noting", "it is important to note",
    "it's important to note", "additionally", "on the other hand", "nevertheless",
]

_EN_TEMPLATE_OPENING_RES = [
    re.compile(r"in today'?s (?:rapidly evolving|digital|fast-paced|modern)\b"),
    re.compile(r"in the era of\b"),
    re.compile(r"as we all know\b"),
    re.compile(r"it goes without saying\b"),
    re.compile(r"with the (?:rapid|fast) (?:development|growth|rise) of\b"),
    re.compile(r"in recent years,?\b"),
]

_EN_ENUM_MARKERS = ["firstly", "secondly", "thirdly", "finally", "lastly"]

_EN_ABSOLUTE_PARALLEL_RES = [re.compile(r"not only.{0,40}?but also")]
_EN_SOFT_PARALLEL_RES = [
    re.compile(r"on (?:the )?one hand.{0,80}?on the other hand"),
]

_EN_CORPORATE_BOOKISH = [
    "leverage", "robust", "delve", "utilize", "utilise", "synergy",
    "paradigm shift", "cutting-edge", "best-in-class", "best of breed",
    "seamless", "holistic", "empower", "streamline", "innovative",
    "state-of-the-art", "revolutionize", "actionable", "frictionless",
    "world-class", "bleeding-edge", "thought leadership", "circle back",
    "move the needle",
]

_EN_MARKETING_HYPE = [
    "revolutionary", "disruptive", "groundbreaking", "unprecedented",
    "supercharge", "turbocharge", "unlock the power",
    "unlock the full potential", "next-level", "game-changer",
    "game-changing",
]

_EN_UNSUPPORTED_CERTAINTY = [
    "undoubtedly", "invariably", "inevitably", "without a doubt", "no doubt",
    "certainly will", "definitely", "bound to", "guaranteed to", "will surely",
]

_EN_ENDING_UPLIFT = [
    "only time will tell", "time will tell", "the future is bright",
    "stay tuned", "a new era", "new era", "the possibilities are endless",
    "in the years to come", "let's wait and see", "the sky is the limit",
]


def check_text_en(text: str) -> list:
    """Run all 8 English de-AI checks; returns a list of ``Finding``."""
    masked = _mask_urls(text or "")
    masked = masked.lower().replace("\u2019", "'")
    return _check_categories(
        masked,
        names=_EN_NAMES,
        connectives=_EN_EMPTY_CONNECTIVES,
        template_res=_EN_TEMPLATE_OPENING_RES,
        enum_markers=_EN_ENUM_MARKERS,
        absolute_parallel_res=_EN_ABSOLUTE_PARALLEL_RES,
        soft_parallel_res=_EN_SOFT_PARALLEL_RES,
        corporate=_EN_CORPORATE_BOOKISH,
        hype=_EN_MARKETING_HYPE,
        certainty=_EN_UNSUPPORTED_CERTAINTY,
        ending=_EN_ENDING_UPLIFT,
    )


def check_file(path) -> list:
    return check_text(pathlib.Path(path).read_text(encoding="utf-8"))


def is_clean(text: str) -> bool:
    return not check_text(text)


def report(findings: list) -> str:
    if not findings:
        return "remove-ai-slop: PASS (8/8 categories clean)"
    lines = [f"remove-ai-slop: FAIL ({len(findings)} finding(s))"]
    for f in findings:
        lines.append(f"- L{f.line} [{f.category}] {f.name}: “{f.phrase}” — {f.excerpt}")
    return "\n".join(lines)
