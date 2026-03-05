from __future__ import annotations

import html
import re
from urllib.parse import parse_qs, unquote, urlparse

import httpx
from bs4 import BeautifulSoup

from .types import SearchResult

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class WebFetcher:
    def __init__(
        self,
        timeout: float = 15.0,
        max_text_chars: int = 12000,
    ) -> None:
        self.timeout = timeout
        self.max_text_chars = max_text_chars
        self.client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": DEFAULT_UA},
        )

    def close(self) -> None:
        self.client.close()

    def search(self, query: str, max_results: int = 8) -> list[SearchResult]:
        params = {"q": query}
        resp = self.client.get("https://html.duckduckgo.com/html/", params=params)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        out: list[SearchResult] = []
        seen: set[str] = set()
        for result in soup.select(".result"):
            a_tag = result.select_one("a.result__a")
            if not a_tag:
                continue

            title = _normalize_ws(a_tag.get_text(" ", strip=True))
            raw_url = (a_tag.get("href") or "").strip()
            url = _normalize_result_url(raw_url)
            snippet_tag = result.select_one(".result__snippet")
            snippet = _normalize_ws(
                snippet_tag.get_text(" ", strip=True) if snippet_tag else ""
            )

            if not title or not url:
                continue
            if url in seen:
                continue
            seen.add(url)
            out.append(
                SearchResult(
                    query=query,
                    title=title,
                    url=url,
                    snippet=snippet,
                )
            )
            if len(out) >= max_results:
                break
        return out

    def fetch_text(self, url: str) -> str:
        resp = self.client.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
            tag.decompose()

        text = soup.get_text(" ", strip=True)
        text = html.unescape(text)
        text = _normalize_ws(text)
        return text[: self.max_text_chars]


def _normalize_result_url(raw_url: str) -> str:
    if not raw_url:
        return ""
    url = raw_url
    if "duckduckgo.com/l/?" in url and "uddg=" in url:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        unwrapped = qs.get("uddg", [""])[0]
        if unwrapped:
            url = unquote(unwrapped)
    return url.strip()


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()

