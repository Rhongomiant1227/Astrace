from __future__ import annotations

import argparse
import os
from typing import Any

from .engine import ResearchEngine
from .fetch import WebFetcher
from .tasks import ResearchTaskManager

try:
    from fastmcp import FastMCP
except Exception:
    from mcp.server.fastmcp import FastMCP  # type: ignore


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def build_components() -> tuple[ResearchEngine, ResearchTaskManager]:
    timeout = float(os.getenv("REQUEST_TIMEOUT", "15"))
    max_chars = _int_env("MAX_TEXT_CHARS", 12000)
    fetcher = WebFetcher(timeout=timeout, max_text_chars=max_chars)
    engine = ResearchEngine(fetcher=fetcher)
    max_workers = _int_env("ASTRACE_TASK_WORKERS", 2)
    task_manager = ResearchTaskManager(engine=engine, max_workers=max_workers)
    return engine, task_manager


ENGINE, TASKS = build_components()
MCP = FastMCP("Astrace")


@MCP.tool()
def research(
    topic: str,
    mode: str = "auto",
    max_iterations: int | None = None,
    max_pages: int | None = None,
    max_results_per_query: int = 8,
    include_raw_text: bool = False,
) -> dict[str, Any]:
    """
    Run structured topic research.

    The model can choose mode:
    - shallow: quick scan
    - deep: iterative broad research
    - auto: planner decides based on topic intent
    """
    return ENGINE.run(
        topic=topic,
        mode=mode,
        max_iterations=max_iterations,
        max_pages=max_pages,
        max_results_per_query=max_results_per_query,
        include_raw_text=include_raw_text,
    )


@MCP.tool()
def start_research(
    topic: str,
    mode: str = "auto",
    max_iterations: int | None = None,
    max_pages: int | None = None,
    max_results_per_query: int = 8,
    include_raw_text: bool = False,
) -> dict[str, Any]:
    """Start async research task for larger deep-research jobs."""
    task_id = TASKS.start(
        topic=topic,
        mode=mode,
        max_iterations=max_iterations,
        max_pages=max_pages,
        max_results_per_query=max_results_per_query,
        include_raw_text=include_raw_text,
    )
    return {"task_id": task_id, "status": "queued"}


@MCP.tool()
def get_research_status(task_id: str) -> dict[str, Any]:
    """Get async task status."""
    return TASKS.get_status(task_id)


@MCP.tool()
def get_research_result(task_id: str) -> dict[str, Any]:
    """Get async task result when status is done."""
    return TASKS.get_result(task_id)


@MCP.tool()
def research_health() -> dict[str, Any]:
    """Simple health probe."""
    return {
        "ok": True,
        "service": "Astrace",
        "mcp_host": os.getenv("MCP_HOST", "0.0.0.0"),
        "mcp_port": _int_env("MCP_PORT", 8788),
        "stateless_http": _bool_env("ASTRACE_STATELESS_HTTP", True),
    }


def run_server() -> None:
    host = os.getenv("MCP_HOST", os.getenv("ASTRACE_HOST", "0.0.0.0"))
    port = _int_env("MCP_PORT", _int_env("ASTRACE_PORT", 8788))
    stateless_http = _bool_env("ASTRACE_STATELESS_HTTP", True)
    MCP.run(
        transport="streamable-http",
        host=host,
        port=port,
        stateless_http=stateless_http,
    )


def self_test() -> int:
    class _MockFetcher:
        def search(self, query: str, max_results: int = 8):
            return [
                type("SearchResultLike", (), {
                    "query": query,
                    "title": f"{query} title {i}",
                    "url": f"https://example.com/{i}",
                    "snippet": f"{query} snippet {i}",
                    "score": 0.0,
                })()
                for i in range(1, max_results + 1)
            ]

        def fetch_text(self, url: str) -> str:
            return (
                "This is a deterministic mock page used for Astrace self-test. "
                "It contains enough tokens for scoring and findings extraction."
            )

    engine = ResearchEngine(fetcher=_MockFetcher())  # type: ignore[arg-type]
    result = engine.run(topic="AstrBot NapCat compatibility research", mode="auto")
    if result["total_sources"] <= 0:
        print("SELF_TEST_FAIL: total_sources <= 0")
        return 1
    if result["mode"] not in {"shallow", "deep"}:
        print("SELF_TEST_FAIL: invalid mode")
        return 1
    print("SELF_TEST_OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Astrace MCP Server")
    parser.add_argument("--self-test", action="store_true", help="Run deterministic self-test and exit")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    run_server()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
