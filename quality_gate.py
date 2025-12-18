"""
Heuristic quality gate for extracted PDF pages.

Each page is scored using lightweight rules so we can flag low-quality
results (blank text, too many weird symbols, etc.) without calling an LLM.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import string


@dataclass(frozen=True)
class QualityGateConfig:
    """
    Thresholds for deciding whether a page extraction looks suspicious.
    Tune these defaults as you learn more about your corpus.
    """

    min_chars: int = 120
    max_weird_char_ratio: float = 0.05
    min_avg_line_length: int = 14
    max_newline_ratio: float = 0.30


DEFAULT_CONFIG = QualityGateConfig()
WEIRD_GLYPHS = {"�"}


def _compute_stats(text: str) -> Dict[str, float]:
    text = text or ""
    char_count = len(text)
    newline_count = text.count("\n")
    stripped_lines = [line.strip() for line in text.splitlines() if line.strip()]
    avg_line_length = (
        sum(len(line) for line in stripped_lines) / len(stripped_lines)
        if stripped_lines
        else 0.0
    )

    weird_chars = 0
    allowed = set(string.printable)
    for ch in text:
        if ch in WEIRD_GLYPHS or ch == "\x00":
            weird_chars += 1
            continue
        # Flag extremely low ASCII control chars (excluding newline + tab)
        if ord(ch) < 32 and ch not in ("\n", "\r", "\t"):
            weird_chars += 1
            continue
        if ch not in allowed and not ch.isprintable():
            weird_chars += 1

    weird_char_ratio = weird_chars / char_count if char_count else 0.0
    newline_ratio = newline_count / char_count if char_count else 0.0

    return {
        "char_count": char_count,
        "newline_count": newline_count,
        "avg_line_length": avg_line_length,
        "weird_char_ratio": weird_char_ratio,
        "newline_ratio": newline_ratio,
    }


def evaluate_page_quality(
    content: str,
    method: str,
    config: Optional[QualityGateConfig] = None,
) -> Dict[str, object]:
    """
    Score a single page and return a structured quality report.
    """
    cfg = config or DEFAULT_CONFIG
    stats = _compute_stats(content)

    reasons: List[str] = []
    if stats["char_count"] < cfg.min_chars:
        reasons.append("too_short")
    if stats["weird_char_ratio"] > cfg.max_weird_char_ratio:
        reasons.append("many_symbols")
    if stats["avg_line_length"] < cfg.min_avg_line_length:
        reasons.append("short_lines")
    if stats["newline_ratio"] > cfg.max_newline_ratio:
        reasons.append("many_newlines")

    quality = "low" if reasons else "ok"
    return {
        "method": method,
        "quality": quality,
        "reason": reasons,
        "metrics": stats,
        "thresholds": asdict(cfg),
    }


def is_low_quality(content: str, method: str) -> bool:
    """
    Convenience helper that returns True when the page failed the gate.
    """
    report = evaluate_page_quality(content, method)
    return report["quality"] == "low"
