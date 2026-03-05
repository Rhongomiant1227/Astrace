from __future__ import annotations

import base64
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
        search_backends: tuple[str, ...] | None = None,
    ) -> None:
        self.timeout = timeout
        self.max_text_chars = max_text_chars
        self.search_backends = search_backends or ("ddg", "bing")
        self.client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": DEFAULT_UA},
        )

    def close(self) -> None:
        self.client.close()

    def search(self, query: str, max_results: int = 8) -> list[SearchResult]:
        out: list[SearchResult] = []
        seen: set[str] = set()
        for backend in self.search_backends:
            backend_results = self._search_backend(
                backend=backend,
                query=query,
                max_results=max_results,
            )
            for item in backend_results:
                if item.url in seen:
                    continue
                seen.add(item.url)
                out.append(item)
                if len(out) >= max_results:
                    return out
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

    def _search_backend(
        self,
        backend: str,
        query: str,
        max_results: int,
    ) -> list[SearchResult]:
        if backend == "ddg":
            return self._search_ddg(query=query, max_results=max_results)
        if backend == "bing":
            return self._search_bing(query=query, max_results=max_results)
        return []

    def _search_ddg(self, query: str, max_results: int) -> list[SearchResult]:
        params = {"q": query}
        resp = self.client.get("https://html.duckduckgo.com/html/", params=params)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        return _parse_ddg_results(soup=soup, query=query, max_results=max_results)

    def _search_bing(self, query: str, max_results: int) -> list[SearchResult]:
        params = {"q": query}
        resp = self.client.get("https://www.bing.com/search", params=params)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        return _parse_bing_results(soup=soup, query=query, max_results=max_results)


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
    if "bing.com/ck/a" in url and "u=" in url:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        unwrapped = _decode_bing_target(qs.get("u", [""])[0])
        if unwrapped:
            url = unwrapped
    return url.strip()


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _decode_bing_target(encoded: str) -> str:
    token = (encoded or "").strip()
    if not token:
        return ""
    if token.startswith("a1"):
        token = token[2:]
    token = unquote(token)
    if token.startswith(("http://", "https://")):
        return token

    # Bing commonly packs the URL as URL-safe base64 without padding.
    padding = "=" * ((4 - len(token) % 4) % 4)
    try:
        decoded = base64.urlsafe_b64decode(token + padding).decode(
            "utf-8",
            errors="ignore",
        )
    except Exception:
        return ""
    return decoded if decoded.startswith(("http://", "https://")) else ""


def _parse_ddg_results(
    soup: BeautifulSoup,
    query: str,
    max_results: int,
) -> list[SearchResult]:
    out: list[SearchResult] = []
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


def _parse_bing_results(
    soup: BeautifulSoup,
    query: str,
    max_results: int,
) -> list[SearchResult]:
    out: list[SearchResult] = []
    for result in soup.select("li.b_algo"):
        a_tag = result.select_one("h2 a")
        if not a_tag:
            continue

        title = _normalize_ws(a_tag.get_text(" ", strip=True))
        url = _normalize_result_url((a_tag.get("href") or "").strip())
        snippet_tag = result.select_one(".b_caption p") or result.select_one("p")
        snippet = _normalize_ws(
            snippet_tag.get_text(" ", strip=True) if snippet_tag else ""
        )

        if not title or not url:
            continue
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
