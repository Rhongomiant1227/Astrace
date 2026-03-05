import base64

import httpx

from astrace.fetch import WebFetcher, _normalize_result_url


class _StubResponse:
    def __init__(self, url: str, status_code: int, text: str) -> None:
        self.url = url
        self.status_code = status_code
        self.text = text
        self._request = httpx.Request("GET", url)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"{self.status_code} error",
                request=self._request,
                response=httpx.Response(
                    status_code=self.status_code,
                    request=self._request,
                    text=self.text,
                ),
            )


class _StubClient:
    def __init__(self, ddg_text: str, bing_text: str, bing_news_text: str = "") -> None:
        self.ddg_text = ddg_text
        self.bing_text = bing_text
        self.bing_news_text = bing_news_text
        self.calls: list[str] = []

    def get(self, url: str, params: dict | None = None) -> _StubResponse:
        self.calls.append(url)
        if "duckduckgo.com" in url:
            return _StubResponse(url=url, status_code=202, text=self.ddg_text)
        if "bing.com/news/search" in url:
            return _StubResponse(url=url, status_code=200, text=self.bing_news_text)
        if "bing.com" in url:
            return _StubResponse(url=url, status_code=200, text=self.bing_text)
        return _StubResponse(url=url, status_code=404, text="")

    def close(self) -> None:
        return None


def test_search_falls_back_to_bing_when_ddg_has_no_results():
    fetcher = WebFetcher(search_backends=("ddg", "bing"))
    fetcher.client = _StubClient(
        ddg_text="<html><body><div>challenge page</div></body></html>",
        bing_text=(
            "<html><body>"
            "<li class='b_algo'>"
            "<h2><a href='https://example.com/a'>Example A</a></h2>"
            "<div class='b_caption'><p>Result A snippet</p></div>"
            "</li>"
            "</body></html>"
        ),
    )

    results = fetcher.search("astrbot mcp", max_results=3)

    assert len(results) == 1
    assert results[0].url == "https://example.com/a"
    assert results[0].title == "Example A"


def test_search_stops_after_first_backend_if_limit_hit():
    fetcher = WebFetcher(search_backends=("ddg", "bing"))
    fetcher.client = _StubClient(
        ddg_text=(
            "<html><body>"
            "<div class='result'>"
            "<a class='result__a' href='https://example.com/ddg'>DDG Result</a>"
            "<a class='result__snippet'>DDG snippet</a>"
            "</div>"
            "</body></html>"
        ),
        bing_text=(
            "<html><body>"
            "<li class='b_algo'>"
            "<h2><a href='https://example.com/bing'>Bing Result</a></h2>"
            "<div class='b_caption'><p>Bing snippet</p></div>"
            "</li>"
            "</body></html>"
        ),
    )

    results = fetcher.search("astrbot mcp", max_results=1)

    assert len(results) == 1
    assert results[0].url == "https://example.com/ddg"
    assert fetcher.client.calls == [
        "https://html.duckduckgo.com/html/",
        "https://www.bing.com/search",
    ]


def test_search_can_fall_back_to_bing_news():
    fetcher = WebFetcher(search_backends=("ddg", "bing", "bing_news"))
    fetcher.client = _StubClient(
        ddg_text="<html><body></body></html>",
        bing_text="<html><body></body></html>",
        bing_news_text=(
            "<html><body>"
            "<a class='title' href='https://example.com/news'>News Result</a>"
            "<div class='snippet'>News snippet</div>"
            "</body></html>"
        ),
    )

    results = fetcher.search("astrbot mcp", max_results=3)

    assert len(results) == 1
    assert results[0].url == "https://example.com/news"
    assert results[0].title == "News Result"


def test_search_limits_single_domain_and_keeps_diversity():
    fetcher = WebFetcher(search_backends=("ddg", "bing", "bing_news"))
    fetcher.client = _StubClient(
        ddg_text="<html><body></body></html>",
        bing_text=(
            "<html><body>"
            "<li class='b_algo'><h2><a href='https://same.test/a'>A</a></h2></li>"
            "<li class='b_algo'><h2><a href='https://same.test/b'>B</a></h2></li>"
            "<li class='b_algo'><h2><a href='https://same.test/c'>C</a></h2></li>"
            "</body></html>"
        ),
        bing_news_text=(
            "<html><body>"
            "<a class='title' href='https://other.test/news'>News Result</a>"
            "</body></html>"
        ),
    )

    results = fetcher.search("astrbot mcp", max_results=3)

    assert len(results) == 3
    assert results[0].url == "https://same.test/a"
    assert results[1].url == "https://same.test/b"
    assert results[2].url == "https://other.test/news"


def test_bing_redirect_url_is_unwrapped():
    target = "https://example.com/path?q=1&lang=zh"
    encoded = base64.urlsafe_b64encode(target.encode("utf-8")).decode("ascii").rstrip("=")
    wrapped = f"https://www.bing.com/ck/a?u=a1{encoded}&ntb=1"

    assert _normalize_result_url(wrapped) == target
