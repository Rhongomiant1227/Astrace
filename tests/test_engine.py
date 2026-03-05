from astrace.engine import ResearchEngine


class MockFetcher:
    def search(self, query: str, max_results: int = 8):
        out = []
        for i in range(max_results):
            out.append(
                type(
                    "SearchResultLike",
                    (),
                    {
                        "query": query,
                        "title": f"{query} title {i}",
                        "url": f"https://example.com/{query.replace(' ', '_')}/{i}",
                        "snippet": f"snippet {i} for {query}",
                        "score": 0.0,
                    },
                )()
            )
        return out

    def fetch_text(self, url: str) -> str:
        return (
            "AstrBot and NapCat compatibility requires testing on Windows and Linux. "
            "This page contains stable content for unit tests."
        )


def test_engine_shallow_runs():
    engine = ResearchEngine(fetcher=MockFetcher())
    result = engine.run(topic="AstrBot NapCat compatibility", mode="shallow")
    assert result["mode"] == "shallow"
    assert result["total_sources"] > 0
    assert len(result["findings"]) > 0


def test_engine_auto_runs():
    engine = ResearchEngine(fetcher=MockFetcher())
    result = engine.run(topic="Do a comprehensive multi-source research", mode="auto")
    assert result["mode"] in {"shallow", "deep"}
    assert result["total_sources"] > 0

