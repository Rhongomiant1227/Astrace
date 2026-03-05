from __future__ import annotations

import base64
import html
import re
from collections import Counter
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
        self.search_backends = search_backends or ("ddg", "bing", "bing_news")
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
        return _select_diverse_results(out, max_results=max_results)

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
        if backend == "bing_news":
            return self._search_bing_news(query=query, max_results=max_results)
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

    def _search_bing_news(self, query: str, max_results: int) -> list[SearchResult]:
        params = {"q": query}
        resp = self.client.get("https://www.bing.com/news/search", params=params)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        return _parse_bing_news_results(soup=soup, query=query, max_results=max_results)


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
        if not _is_candidate_url(url):
            continue
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


def _parse_bing_news_results(
    soup: BeautifulSoup,
    query: str,
    max_results: int,
) -> list[SearchResult]:
    out: list[SearchResult] = []
    for a_tag in soup.select("a.title[href]"):
        title = _normalize_ws(a_tag.get_text(" ", strip=True))
        url = _normalize_result_url((a_tag.get("href") or "").strip())
        if not _is_candidate_url(url):
            continue

        card = a_tag.find_parent()
        snippet = ""
        if card:
            snippet_tag = card.select_one(".snippet") or card.select_one(".source")
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


def _is_candidate_url(url: str) -> bool:
    if not url.startswith(("http://", "https://")):
        return False
    lowered = url.lower()
    blocked_prefixes = (
        "https://www.bing.com/ck/a",
        "https://www.bing.com/search",
        "https://www.bing.com/news/search",
        "http://go.microsoft.com/",
        "https://go.microsoft.com/",
    )
    return not lowered.startswith(blocked_prefixes)


def _select_diverse_results(
    candidates: list[SearchResult],
    max_results: int,
    max_per_domain: int = 2,
) -> list[SearchResult]:
    if max_results <= 0:
        return []
    if not candidates:
        return []

    selected: list[SearchResult] = []
    domain_counter: Counter[str] = Counter()

    for item in candidates:
        domain = (urlparse(item.url).netloc or "").lower()
        if domain and domain_counter[domain] >= max_per_domain:
            continue
        selected.append(item)
        if domain:
            domain_counter[domain] += 1
        if len(selected) >= max_results:
            return selected

    if len(selected) >= max_results:
        return selected[:max_results]

    selected_urls = {item.url for item in selected}
    for item in candidates:
        if item.url in selected_urls:
            continue
        selected.append(item)
        if len(selected) >= max_results:
            break
    return selected[:max_results]
