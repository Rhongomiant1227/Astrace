from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class SearchResult:
    query: str
    title: str
    url: str
    snippet: str
    score: float = 0.0


@dataclass
class SourceDocument:
    source_id: str
    query: str
    title: str
    url: str
    snippet: str
    text: str
    score: float


@dataclass
class Finding:
    claim: str
    evidence: list[dict[str, str]]
    confidence: str


@dataclass
class IterationTrace:
    iteration: int
    input_queries: list[str]
    output_queries: list[str]
    crawled_urls: list[str]


@dataclass
class ResearchReport:
    topic: str
    mode: str
    decision_reason: str
    summary: str
    findings: list[Finding]
    sources: list[SourceDocument]
    iterations_used: int
    total_sources: int
    trace: list[IterationTrace]

    def to_dict(self, include_raw_text: bool = False) -> dict[str, Any]:
        payload = asdict(self)
        if not include_raw_text:
            for source in payload["sources"]:
                source["text"] = ""
        return payload

