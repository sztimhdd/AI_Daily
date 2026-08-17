"""AI_Daily: Codex-native daily editorial pipeline (V1).

One independent editorial run per calendar day:
collect -> topic_choice -> research -> narrative -> outline -> draft ->
optional_cover -> assembly -> completed
"""

__version__ = "0.1.0"

STAGES = [
    "collect",
    "topic_choice",
    "research",
    "narrative",
    "outline",
    "draft",
    "optional_cover",
    "assembly",
    "completed",
]
