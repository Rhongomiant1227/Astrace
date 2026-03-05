from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from .fetch import WebFetcher
from .planner import ResearchPlanner, decide_mode, tokenize
from .types import Finding, IterationTrace, ResearchReport, SearchResult, SourceDocument


@dataclass
class _ModeProfile:
    iterations: int
    query_width: int
    page_budget: int


MODE_PROFILES: dict[str, _ModeProfile] = {
    "shallow": _ModeProfile(iterations=1, query_width=2, page_budget=8),
    "deep": _ModeProfile(iterations=4, query_width=4, page_budget=48),
}


class ResearchEngine:
    def __init__(
        self,
        fetcher: WebFetcher | None = None,
        planner: ResearchPlanner | None = None,
    ) -> None:
        self.fetcher = fetcher or WebFetcher()
        self.planner = planner or ResearchPlanner()

    def run(
        self,
        topic: str,
        mode: str = "auto",
        max_iterations: int | None = None,
        max_pages: int | None = None,
        max_results_per_query: int = 8,
        include_raw_text: bool = False,
    ) -> dict[str, Any]:
        if not topic.strip():
            raise ValueError("topic must not be empty")

        decided_mode, reason = decide_mode(topic, mode)
        profile = MODE_PROFILES[decided_mode]

        iterations = (
            max(1, min(max_iterations, 12))
            if isinstance(max_iterations, int)
            else profile.iterations
        )
        page_budget = (
            max(1, min(max_pages, 120))
            if isinstance(max_pages, int)
            else profile.page_budget
        )

        trace: list[IterationTrace] = []
        all_sources: list[SourceDocument] = []
        seen_urls: set[str] = set()

        query_history: list[str] = []
        current_queries = self.planner.seed_queries(topic, decided_mode)[: profile.query_width]

        source_id_counter = 1
        for index in range(iterations):
            if not current_queries:
                break
            if len(all_sources) >= page_budget:
                break

            crawled_urls_this_iter: list[str] = []
            search_pool: list[SearchResult] = []

            for query in current_queries[: profile.query_width]:
                query_history.append(query)
                results = self.fetcher.search(query, max_results=max_results_per_query)
                for item in results:
                    item.score = _score_search_result(query, item)
                search_pool.extend(results)

            search_pool.sort(key=lambda item: item.score, reverse=True)
            for item in search_pool:
                if len(all_sources) >= page_budget:
                    break
                if item.url in seen_urls:
                    continue
                seen_urls.add(item.url)

                text = ""
                try:
                    text = self.fetcher.fetch_text(item.url)
                except Exception:
                    continue
                if not text:
                    continue

                score = _score_document(topic=topic, query=item.query, source=item, text=text)
                document = SourceDocument(
                    source_id=f"S{source_id_counter}",
                    query=item.query,
                    title=item.title,
                    url=item.url,
                    snippet=item.snippet,
                    text=text,
                    score=score,
                )
                source_id_counter += 1
                all_sources.append(document)
                crawled_urls_this_iter.append(item.url)

            next_queries = self.planner.next_queries(
                topic=topic,
                sources=all_sources,
                used_queries=query_history,
                mode=decided_mode,
            )

            trace.append(
                IterationTrace(
                    iteration=index + 1,
                    input_queries=current_queries,
                    output_queries=next_queries,
                    crawled_urls=crawled_urls_this_iter,
                )
            )
            current_queries = next_queries[: profile.query_width]

            if decided_mode == "shallow":
                break

        report = _build_report(
            topic=topic,
            mode=decided_mode,
            reason=reason,
            sources=all_sources,
            trace=trace,
        )
        return report.to_dict(include_raw_text=include_raw_text)


def _score_search_result(query: str, item: SearchResult) -> float:
    query_tokens = set(tokenize(query))
    text_tokens = set(tokenize(f"{item.title} {item.snippet}"))
    if not query_tokens:
        return 0.0
    overlap = len(query_tokens.intersection(text_tokens))
    return overlap / max(1, len(query_tokens))


def _score_document(topic: str, query: str, source: SearchResult, text: str) -> float:
    topic_tokens = set(tokenize(topic))
    query_tokens = set(tokenize(query))
    text_tokens = set(tokenize(f"{source.title} {source.snippet} {text[:2000]}"))
    topic_overlap = len(topic_tokens.intersection(text_tokens))
    query_overlap = len(query_tokens.intersection(text_tokens))
    return topic_overlap * 1.2 + query_overlap * 0.8


def _build_report(
    topic: str,
    mode: str,
    reason: str,
    sources: list[SourceDocument],
    trace: list[IterationTrace],
) -> ResearchReport:
    sorted_sources = sorted(sources, key=lambda item: item.score, reverse=True)
    findings: list[Finding] = []

    top_sources = sorted_sources[: min(6, len(sorted_sources))]
    for item in top_sources:
        claim = _first_sentence(item.text) or item.snippet or item.title
        confidence = _confidence_label(item.score)
        findings.append(
            Finding(
                claim=claim,
                evidence=[
                    {
                        "source_id": item.source_id,
                        "title": item.title,
                        "url": item.url,
                    }
                ],
                confidence=confidence,
            )
        )

    summary = _build_summary(topic=topic, mode=mode, sources=sorted_sources, findings=findings)
    return ResearchReport(
        topic=topic,
        mode=mode,
        decision_reason=reason,
        summary=summary,
        findings=findings,
        sources=sorted_sources,
        iterations_used=len(trace),
        total_sources=len(sorted_sources),
        trace=trace,
    )


def _build_summary(
    topic: str,
    mode: str,
    sources: list[SourceDocument],
    findings: list[Finding],
) -> str:
    domains = {urlparse(item.url).netloc for item in sources if item.url}
    domain_count = len(domains)
    top_claims = [finding.claim for finding in findings[:3]]
    claims_text = " | ".join(top_claims)
    return (
        f"Topic: {topic}. Mode: {mode}. "
        f"Sources: {len(sources)} from {domain_count} domains. "
        f"Top findings: {claims_text}"
    )


def _first_sentence(text: str) -> str:
    sentence = re.split(r"(?<=[.!?。！？])\s+", text.strip())[0]
    sentence = sentence.strip()
    return sentence[:220]


def _confidence_label(score: float) -> str:
    if score >= 12:
        return "high"
    if score >= 6:
        return "medium"
    return "low"

