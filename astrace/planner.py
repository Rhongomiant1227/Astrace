from __future__ import annotations

import re
from collections import Counter

from .types import SourceDocument

Mode = str

DEEP_HINTS = (
    "deep",
    "research",
    "investigate",
    "compare",
    "comprehensive",
    "evidence",
    "multi-source",
    "latest progress",
    "benchmark",
    "tradeoff",
)


def decide_mode(topic: str, requested_mode: Mode = "auto") -> tuple[Mode, str]:
    req = (requested_mode or "auto").strip().lower()
    if req in {"shallow", "deep"}:
        return req, f"mode forced by caller: {req}"

    lowered = topic.lower()
    score = 0
    hit_terms: list[str] = []
    for hint in DEEP_HINTS:
        if hint in lowered:
            score += 1
            hit_terms.append(hint)

    if score >= 2:
        return "deep", f"auto selected deep due to hints: {', '.join(hit_terms[:5])}"
    return "shallow", "auto selected shallow (no strong deep-research hints)"


def tokenize(text: str) -> list[str]:
    en = re.findall(r"[a-zA-Z0-9]{3,}", text.lower())
    zh = re.findall(r"[\u4e00-\u9fff]{2,}", text)
    return en + zh


class ResearchPlanner:
    def seed_queries(self, topic: str, mode: Mode) -> list[str]:
        topic = topic.strip()
        base = [topic]
        if mode == "deep":
            base.extend(
                [
                    f"{topic} latest updates",
                    f"{topic} comparison",
                    f"{topic} key risks",
                ]
            )
        else:
            base.append(f"{topic} overview")
        return _unique_keep_order(base)

    def next_queries(
        self,
        topic: str,
        sources: list[SourceDocument],
        used_queries: list[str],
        mode: Mode,
    ) -> list[str]:
        if mode != "deep" or not sources:
            return []
        tokens = Counter()
        for src in sources:
            tokens.update(tokenize(f"{src.title} {src.snippet}")[:30])

        candidates: list[str] = []
        for token, _ in tokens.most_common(20):
            if token in topic.lower():
                continue
            query = f"{topic} {token}"
            candidates.append(query)

        used = set(q.lower() for q in used_queries)
        fresh = [q for q in candidates if q.lower() not in used]
        return _unique_keep_order(fresh)[:4]


def _unique_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item.strip())
    return out
